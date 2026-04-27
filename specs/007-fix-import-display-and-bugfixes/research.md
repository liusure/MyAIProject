# Research: 导入显示优化及推荐和课程表bug修复

## Bug 1: 推荐功能返回空结果

**Root Cause**: `MiMoProvider.generate_structured()` 在 `backend/src/services/llm/mimo.py` 中创建新的 system message（仅包含 JSON Schema），覆盖了 `recommend()` 传入的包含可用课程列表的 system message。LLM 看不到真实课程数据，生成无法匹配的 course_ids。

**Decision**: 修改 `mimo.py` 的 `generate_structured()` 方法，将 schema 信息追加到已有的 system message 中，而非创建新的 system message 覆盖。

**Rationale**: 保留 recommend() 注入的课程上下文是核心需求，schema 指令应作为补充而非替代。

**Alternatives considered**:
- 在 recommend() 中直接构造完整 prompt（耦合过紧）
- 使用 tool calling 替代 structured output（API 变更大）

## Bug 2: 课程表不显示

**Root Cause**: SSE 流式接口 `conversation.py:159` 使用 `json.dumps()` 序列化包含 Pydantic 模型的 `recommendations` 和 `conflicts` 列表。`json.dumps` 无法序列化 Pydantic v2 模型实例，抛出 `TypeError`，导致 SSE 流中断，前端 `onDone` 回调从未触发。

**Decision**: 在 `json.dumps()` 调用前，使用 Pydantic 的 `model_dump(mode='json')` 将所有模型实例转换为可序列化的 dict。

**Rationale**: 这是标准的 Pydantic v2 JSON 序列化方式，无需引入自定义 encoder。

**Alternatives considered**:
- 注册自定义 JSON encoder（全局影响，过度设计）
- 使用 FastAPI 的 `jsonable_encoder`（需要额外导入）

## Bug 3: Fallback LLM 不返回推荐

**Root Cause**: `backend/src/services/llm/fallback.py` 的 `generate_structured()` 返回的 dict 不包含 `recommendations` 键，导致 `recommend()` 中的 `result.get('recommendations', [])` 始终为空列表。

**Decision**: 在 fallback 返回值中添加空的 `recommendations: []` 键，使调用方逻辑一致。

**Rationale**: 最小改动，确保 API 契约一致。

## Import Display

**Context**: 当前 `FileUpload.tsx` 的 done 步骤展示完整课程列表，用户认为无意义。

**Decision**: 移除课程列表展示，成功时只显示"成功导入 X 条"，失败时显示错误列表。

**Rationale**: 符合用户需求，简化界面。
