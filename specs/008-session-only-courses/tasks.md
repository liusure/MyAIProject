# Tasks: 课程数据仅存会话，推荐历史持久化

**Input**: Design documents from `/specs/008-session-only-courses/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 3 - 服务端不再回退到数据库课程 (Priority: P2) 🎯 MVP

**Goal**: 当会话中无课程数据时，推荐服务直接提示"请先上传课表文件"，不再从数据库 courses 表回退。

**Independent Test**: 不上传课程文件直接请求推荐 → 确认系统返回"请先上传课表文件"，不使用数据库中的旧课程数据。

### Implementation for User Story 3

- [x] T001 [US3] 修改 `recommend()` 方法：当 `session_courses` 为空时直接返回提示信息，移除 `_get_active_courses()` 数据库回退逻辑 in `backend/src/services/recommend.py` (lines 54-68)

**Checkpoint**: User Story 3 complete — 无 session courses 时推荐服务不再查询数据库，直接返回提示。

---

## Phase 2: User Story 1 & 2 - 会话数据生命周期与推荐历史持久化 (Priority: P1)

**Goal**: 课程数据仅存内存会话（刷新即消失），推荐历史含课程快照通过 Conversation.messages 持久化（已有的行为无需额外修改）。

**Independent Test**: 上传课程 → 获得推荐 → 刷新页面 → 课程列表为空，推荐历史仍可完整查看。

### Implementation for User Story 1 & 2

- [x] T002 [US1] [US2] 验证推荐历史快照完整性：确认 `_build_recommendation_plan()` 返回的 `CourseResponse` 列表包含完整课程信息（名称、学分、教师、schedule），无需代码变更 in `backend/src/services/recommend.py` (lines 143-198)

**Checkpoint**: 推荐历史通过现有 Conversation.messages 持久化，课程快照数据完整。SessionStore 内存行为不变（刷新即清空）。

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: 端到端验证。

- [x] T003 端到端验证：按 quickstart.md 的 4 个场景逐一测试

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US3)**: No dependencies — single file change, can start immediately
- **Phase 2 (US1/US2)**: Depends on Phase 1 — 验证推荐结果包含完整快照
- **Phase 3 (Polish)**: Depends on Phase 1-2 complete

### User Story Dependencies

- **US3**: 核心变更，其他 story 依赖此变更
- **US1, US2**: 推荐历史持久化和会话生命周期是现有行为，只需验证不需要额外代码变更

### Parallel Opportunities

```bash
# T001 is the only implementation task — no parallel execution needed
# T002 is a verification task (read-only)
```

---

## Implementation Strategy

### MVP First

1. Apply T001 — 移除 DB 回退（唯一代码变更）
2. 验证：不上传文件直接推荐 → 返回"请先上传课表文件"
3. 验证：上传文件后推荐 → 返回有效方案，历史可查看

### Notes

- 此 feature 仅需修改 1 个文件 (`backend/src/services/recommend.py`)
- 推荐历史持久化通过现有 `Conversation.messages` JSONB 实现，无需新表或新 API
- SessionStore 内存行为不变，`--reload` 模式下丢失是开发环境已知行为
- `courses` 表及相关代码（CourseImportService, CourseSearchService）保留不删除
