# Implementation Plan: 导入显示优化及推荐和课程表bug修复

**Branch**: `007-fix-import-display-and-bugfixes` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-fix-import-display-and-bugfixes/spec.md`

## Summary

修复三个问题：(1) 导入结果页面简化为只显示成功条数，任何失败即整体失败；(2) 推荐功能因 LLM 无法看到可用课程数据而始终返回空结果；(3) 周课程表因 SSE 流中 Pydantic 模型序列化失败而不显示。

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.x
**Primary Dependencies**: FastAPI, React 19, Vite 8, Pydantic v2, pandas
**Storage**: In-memory session (SessionStore), PostgreSQL (courses)
**Testing**: pytest (backend), no frontend tests currently
**Target Platform**: Web application (Chrome/Firefox/Safari)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: LLM P95 < 5s, import < 2s for 1000 rows, schedule render < 1s
**Constraints**: LLM API key required, SSE for streaming, cookie-based session
**Scale/Scope**: ~10 files to modify across frontend and backend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | ✅ | All changes use existing typed structures |
| Module Layering | ✅ | Changes stay within existing layers (api → services → schemas) |
| UX Consistency | ✅ | Loading states exist, error messages will be improved |
| Performance | ✅ | No new performance concerns introduced |
| LLM Degradation | ✅ | Fallback path will be improved |

No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/007-fix-import-display-and-bugfixes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no new contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── import_.py          # Fix: store raw_data in session
│   │   └── conversation.py     # Fix: Pydantic serialization in SSE
│   ├── services/
│   │   ├── recommend.py        # Fix: ensure LLM sees course data
│   │   ├── session_store.py    # Add raw_data storage
│   │   └── llm/
│   │       ├── mimo.py         # Fix: don't overwrite system prompt
│   │       └── fallback.py     # Fix: return recommendations key
│   └── schemas/

frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload/
│   │   │   └── FileUpload.tsx  # Fix: simplify done step display
```

## Complexity Tracking

> No constitution violations. No complexity justification needed.
