# Implementation Plan: 课程数据仅存会话，推荐历史持久化

**Branch**: `008-session-only-courses` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-session-only-courses/spec.md`

## Summary

课程数据仅存在于内存会话中（SessionStore），不持久化到数据库。推荐历史（含课程快照）通过现有 Conversation.messages JSONB 字段持久化。移除 RecommendService 中对数据库 courses 表的回退查询。

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.x
**Primary Dependencies**: FastAPI, React 19, Vite 8, Pydantic v2, pandas
**Storage**: In-memory session (SessionStore), PostgreSQL (conversations)
**Testing**: pytest (backend), no frontend tests currently
**Target Platform**: Web application (Chrome/Firefox/Safari)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: LLM P95 < 5s, import < 2s for 1000 rows
**Constraints**: LLM API key required, SSE for streaming, cookie-based session
**Scale/Scope**: ~2 files to modify, 1 method to simplify

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | ✅ | 使用现有类型结构 |
| Module Layering | ✅ | 变更限制在 service 层 |
| UX Consistency | ✅ | 无上传时有明确提示 |
| Performance | ✅ | 移除 DB 查询，性能提升 |
| LLM Degradation | ✅ | 无影响 |

No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/008-session-only-courses/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # N/A — no new API contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   ├── recommend.py        # 核心变更：移除 DB 回退
│   │   └── session_store.py    # 无变更
│   ├── api/
│   │   ├── conversation.py     # 无变更（推荐结果已通过 messages 持久化）
│   │   └── import_.py          # 无变更
│   ├── models/
│   │   └── course.py           # 保留不删除
│   └── services/
│       ├── course_import.py    # 保留不删除（其他功能可能使用）
│       └── course_search.py    # 保留不删除
```

## Complexity Tracking

> No constitution violations. No complexity justification needed.
