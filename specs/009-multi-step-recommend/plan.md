# Implementation Plan: Multi-Step Course Recommendation

**Branch**: `009-multi-step-recommend` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-multi-step-recommend/spec.md`

## Summary

将现有的单步课程推荐流程重构为两步流水线：第一步将用户需求和学科列表发送给 LLM 做学科多选过滤，第二步将过滤后的非敏感课程信息发送给 LLM 做精细筛选，最后在本地通过课程序号重新查找完整课程详情并执行冲突检测。目标是解决 prompt 过长触发 MiMo API 内容安全策略的问题，同时减少 LLM 暴露的数据量。

## Technical Context

**Language/Version**: Python ≥3.12
**Primary Dependencies**: FastAPI ≥0.115, SQLAlchemy (async) ≥2.0.36, Pydantic v2 ≥2.10, httpx ≥0.28
**Storage**: PostgreSQL 16 (conversations, audit), Redis 7 (LLM cache), in-memory SessionStore (session courses)
**Testing**: pytest ≥8.3 + pytest-asyncio, Ruff (line=120), strict mypy
**Target Platform**: Linux/macOS server (uvicorn ASGI)
**Project Type**: Web service (FastAPI backend + React frontend)
**Performance Goals**: 端到端响应 ≤30s (SC-004), LLM P95 <5s (constitution), 冲突检测 <500ms (constitution)
**Constraints**: MiMo API 内容安全过滤不可触发 (SC-006), 两步 LLM 调用总 token 用量可控
**Scale/Scope**: 单用户 2000+ 条课程记录, 100 并发用户 (constitution)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| 类型安全优先 | ✅ | 所有新函数使用完整 Type Hints，Pydantic 模型定义数据结构 |
| 文档完整性 | ✅ | 公共 API 使用 Google 风格 Docstring |
| 模块化设计 | ✅ | 新逻辑在 RecommendService 内部重构，不引入新层级 |
| 单元测试覆盖率 ≥85% | ✅ | 两步流水线的每个步骤独立可测 |
| LLM API Mock 测试 | ✅ | 使用 Mock 测试两步 LLM 调用 |
| 性能 P95 <5s | ✅ | 两步调用各自独立，总时间受 SC-004 ≤30s 约束 |
| LLM 必须有降级方案 | ✅ | 保留现有 FallbackLLMProvider 降级链 |
| 课程冲突检测 | ✅ | 保留现有 detect_time_conflicts + detect_commute_conflicts |
| 敏感信息不暴露给 LLM | ✅ | 第二步仅发送非敏感字段（FR-004） |

无违规项。

## Project Structure

### Documentation (this feature)

```text
specs/009-multi-step-recommend/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/src/
├── services/
│   ├── recommend.py              # ⭐ 主要修改：两步流水线逻辑
│   ├── llm/
│   │   ├── base.py               # LLMProvider ABC（不变）
│   │   ├── mimo.py               # MiMoProvider（不变）
│   │   ├── fallback.py           # FallbackLLMProvider（不变）
│   │   ├── cache.py              # LLMCache（不变）
│   │   └── factory.py            # LLMFactory（不变）
│   ├── conflict/
│   │   ├── time.py               # 时间冲突检测（不变）
│   │   └── commute.py            # 通勤冲突检测（不变）
│   └── session_store.py          # SessionStore（不变）
├── schemas/
│   ├── course.py                 # SessionCourse（不变）
│   └── plan.py                   # RecommendationPlan（不变）
└── api/
    └── conversation.py           # 聊天端点（小改：错误处理适配）
```

**Structure Decision**: 修改集中在 `backend/src/services/recommend.py`，API 层和 Schema 层无结构性变更。

## Complexity Tracking

无宪章违规项，无需填写。
