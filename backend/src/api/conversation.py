import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_or_create_device
from src.schemas.conversation import ChatRequest
from src.schemas.plan import ChatResponse
from src.services.audit import AuditService
from src.services.conversation import ConversationService
from src.services.llm.cache import LLMCache
from src.services.llm.factory import LLMFactory
from src.services.llm.mimo import ContentFilteredError
from src.services.llm.fallback import FallbackLLMProvider
from src.services.recommend import RecommendService
from src.services.session_store import SessionStore

logger = logging.getLogger(__name__)


def _serialize_result(result: dict) -> dict:
    """Convert Pydantic models in result to JSON-serializable dicts."""
    serialized = {}
    for key, value in result.items():
        if key == "recommendations" and isinstance(value, list):
            serialized[key] = [
                r.model_dump(mode="json") if hasattr(r, "model_dump") else r
                for r in value
            ]
        elif hasattr(value, "model_dump"):
            serialized[key] = value.model_dump(mode="json")
        else:
            serialized[key] = value
    return serialized

router = APIRouter(prefix="/conversation", tags=["对话"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)],
    db: AsyncSession = Depends(get_db),
):
    conv_service = ConversationService(db)

    # 获取或创建对话
    if req.conversation_id:
        conversation = await conv_service.get(req.conversation_id)
        if not conversation or conversation.device_id != device_id:
            conversation = await conv_service.create(device_id)
    else:
        conversation = await conv_service.create(device_id)

    # 记录用户消息
    await conv_service.add_message(conversation, "user", req.message)

    # 获取上下文
    context = await conv_service.get_context_messages(conversation)

    # 尝试缓存（跳过降级结果）
    cached = await LLMCache.get(context + [{"role": "user", "content": req.message}])
    if cached and not cached.get("degraded") and cached.get("recommendations"):
        await conv_service.add_message(conversation, "assistant", cached["reply"], cached)
        return ChatResponse(
            conversation_id=conversation.id,
            reply=cached["reply"],
            recommendations=cached.get("recommendations", []),
            conflicts=cached.get("conflicts", []),
            degraded=False,
        )

    # 调用 LLM 推荐
    session_courses = SessionStore.get_courses(device_id)
    degraded = False
    try:
        llm = LLMFactory.get_available()
        service = RecommendService(db, llm, session_courses=session_courses)
        result = await service.recommend(req.message, context)
    except ContentFilteredError:
        result = {
            "reply": "抱歉，您的请求触发了内容安全策略。请尝试简化描述，例如「推荐计算机课程」。",
            "recommendations": [],
        }
        degraded = True
    except Exception:
        # 降级模式
        degraded = True
        llm = FallbackLLMProvider()
        service = RecommendService(db, llm, session_courses=session_courses)
        result = await service.recommend(req.message, context)

    # 缓存结果（不缓存降级结果）
    serializable = _serialize_result(result)
    if not degraded and serializable.get("recommendations"):
        await LLMCache.set(context + [{"role": "user", "content": req.message}], serializable)

    # 记录回复
    await conv_service.add_message(conversation, "assistant", result["reply"], serializable)

    # 记录审计日志
    audit = AuditService(db)
    await audit.log("chat", "conversation", conversation.id, {"message": req.message}, device_id)

    return ChatResponse(
        conversation_id=conversation.id,
        reply=result["reply"],
        recommendations=result.get("recommendations", []),
        conflicts=result.get("conflicts", []),
        degraded=degraded,
    )


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)],
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式对话接口：逐步产出 token，最终发送完整推荐结果"""

    async def event_generator():
        conv_service = ConversationService(db)

        # 获取或创建对话
        if req.conversation_id:
            conversation = await conv_service.get(req.conversation_id)
            if not conversation or conversation.device_id != device_id:
                conversation = await conv_service.create(device_id)
        else:
            conversation = await conv_service.create(device_id)

        await conv_service.add_message(conversation, "user", req.message)
        context = await conv_service.get_context_messages(conversation)

        # 检查缓存（跳过降级结果）
        try:
            cached = await LLMCache.get(context + [{"role": "user", "content": req.message}])
        except Exception as e:
            logger.warning(f"LLMCache.get failed: {type(e).__name__}: {e}")
            cached = None
        if cached and not cached.get("degraded") and cached.get("recommendations"):
            yield f"data: {json.dumps({'type': 'token', 'content': cached['reply']}, ensure_ascii=False)}\n\n"
            rec_dicts = [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in cached.get("recommendations", [])]
            conflict_dicts = [c.model_dump(mode="json") if hasattr(c, "model_dump") else c for c in cached.get("conflicts", [])]
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': str(conversation.id), 'reply': cached['reply'], 'recommendations': rec_dicts, 'conflicts': conflict_dicts, 'degraded': False}, ensure_ascii=False)}\n\n"
            await conv_service.add_message(conversation, "assistant", cached["reply"], cached)
            return

        # 使用 recommend_stream 获取推荐结果并流式输出回复
        degraded = False
        reply_text = ""
        try:
            session_courses = SessionStore.get_courses(device_id)
            llm = LLMFactory.get_available()
            service = RecommendService(db, llm, session_courses=session_courses)

            # on_progress 回调：发送 progress SSE 事件
            async def send_progress(stage: str, message: str):
                yield f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': message}, ensure_ascii=False)}\n\n"

            # 注意：progress 事件需要在 event_generator 的上下文中 yield
            # 由于 on_progress 是回调，我们需要收集 progress 事件再发送
            progress_events: list[str] = []

            async def collect_progress(stage: str, message: str):
                progress_events.append(
                    f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': message}, ensure_ascii=False)}\n\n"
                )

            result, reply_stream = await service.recommend_stream(req.message, context, on_progress=collect_progress)

            # 发送收集到的 progress 事件
            for evt in progress_events:
                yield evt

            # 流式发送回复文字
            async for chunk in reply_stream:
                reply_text += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"

        except ContentFilteredError:
            result = {
                "reply": "抱歉，您的请求触发了内容安全策略。请尝试简化描述，例如「推荐计算机课程」。",
                "recommendations": [],
            }
            reply_text = result["reply"]
            yield f"data: {json.dumps({'type': 'token', 'content': reply_text}, ensure_ascii=False)}\n\n"
            degraded = True
        except Exception as e:
            logger.error(f"Recommend failed, using fallback: {type(e).__name__}: {e}")
            degraded = True
            session_courses = SessionStore.get_courses(device_id)
            llm = FallbackLLMProvider()
            service = RecommendService(db, llm, session_courses=session_courses)
            result = await service.recommend(req.message, context)
            reply_text = result.get("reply", "")
            yield f"data: {json.dumps({'type': 'token', 'content': reply_text}, ensure_ascii=False)}\n\n"

        # 缓存 & 持久化（不缓存降级结果）
        serializable = _serialize_result(result)
        if not degraded and serializable.get("recommendations"):
            await LLMCache.set(context + [{"role": "user", "content": req.message}], serializable)
        await conv_service.add_message(conversation, "assistant", reply_text, serializable)

        audit = AuditService(db)
        await audit.log("chat_stream", "conversation", conversation.id, {"message": req.message}, device_id)

        # 发送最终结果事件
        recommendations = result.get("recommendations", [])
        rec_dicts = [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in recommendations]
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': str(conversation.id), 'reply': reply_text, 'recommendations': rec_dicts, 'conflicts': [], 'degraded': degraded}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
