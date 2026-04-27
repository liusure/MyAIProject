from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import router as auth_router
from src.api.conversation import router as conversation_router
from src.api.courses import router as courses_router
from src.api.plan import router as plan_router
from src.api.admin import router as admin_router
from src.api.import_ import router as import_router

app = FastAPI(
    title="LLM 自动选课系统 API",
    version="0.1.0",
    description="AI 驱动的智能选课推荐平台 API 接口规范",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(plan_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(import_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
