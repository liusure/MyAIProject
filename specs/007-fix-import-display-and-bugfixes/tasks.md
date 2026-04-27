# Tasks: 导入显示优化及推荐和课程表bug修复

**Input**: Design documents from `/specs/007-fix-import-display-and-bugfixes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - 导入结果简化展示 (Priority: P1) 🎯 MVP

**Goal**: 导入成功后只显示"成功导入 X 条"，任何失败即整体失败，展示错误列表。

**Independent Test**: 上传包含有效数据的 Excel，确认只显示成功条数；上传含错误数据的文件，确认显示失败信息。

### Implementation for User Story 1

- [x] T001 [US1] 简化 done 步骤展示逻辑：成功时只显示 total 数量，失败时显示 errors 列表，移除 courses 列表渲染 in `frontend/src/components/FileUpload/FileUpload.tsx` (line ~136-180)

**Checkpoint**: User Story 1 complete — 导入结果页面只显示条数或错误，不再展示课程列表。

---

## Phase 2: User Story 2 - 修复推荐功能返回空结果 (Priority: P1)

**Goal**: 推荐功能基于已上传课程数据返回有效推荐方案，而非始终返回空结果。

**Independent Test**: 上传课程文件后输入选课偏好，确认返回包含课程列表的推荐方案。

### Implementation for User Story 2

- [x] T002 [P] [US2] 修改 `generate_structured()` 方法：将 JSON schema 信息追加到已有 system message 末尾，而非创建新的 system message 覆盖 in `backend/src/services/llm/mimo.py` (line ~33-60)

- [x] T003 [P] [US2] 在 fallback 的 `generate_structured()` 返回值中添加 `recommendations: []` 键，确保调用方逻辑一致 in `backend/src/services/llm/fallback.py` (line ~24-40)

**Checkpoint**: User Story 2 complete — 推荐功能返回有效方案，fallback 路径也返回正确结构。

---

## Phase 3: User Story 3 - 修复周课程表不显示 (Priority: P1)

**Goal**: 推荐方案返回后，每个方案下方正确显示周课程表视图。

**Independent Test**: 获取推荐方案后，确认方案下方出现课程表网格，有 schedule 的课程显示在正确格子中。

### Implementation for User Story 3

- [x] T004 [US3] 修复 SSE 流中 Pydantic 模型序列化：在 `json.dumps()` 调用前，将 recommendations 和 conflicts 列表中的 Pydantic 模型实例用 `model_dump(mode='json')` 转换为 dict in `backend/src/api/conversation.py` (line ~159)

**Checkpoint**: User Story 3 complete — SSE 流不再因序列化错误中断，前端 onDone 正常触发，课程表正常渲染。

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation across all fixes.

- [x] T005 端到端验证：按 quickstart.md 的 4 个场景逐一测试，确认所有修复生效

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — frontend-only change, can start immediately
- **Phase 2 (US2)**: No dependencies — backend-only changes, can start immediately
- **Phase 3 (US3)**: No dependencies — backend-only change, can start immediately
- **Phase 4 (Polish)**: Depends on Phase 1-3 all complete

### User Story Dependencies

- **US1, US2, US3**: All independent — can be implemented in parallel since they touch different files
- US2 and US3 are related (both affect the recommendation flow) but their fixes are in separate files (mimo.py/fallback.py vs conversation.py)

### Parallel Opportunities

```bash
# All three user stories can be implemented in parallel:
Task: "T001 [US1] Simplify done step display in frontend/src/components/FileUpload/FileUpload.tsx"
Task: "T002 [US2] Fix system prompt overwrite in backend/src/services/llm/mimo.py"
Task: "T003 [US2] Add recommendations key in backend/src/services/llm/fallback.py"
Task: "T004 [US3] Fix Pydantic serialization in backend/src/api/conversation.py"

# T002 and T003 are in different files so they can run in parallel
```

---

## Implementation Strategy

### Incremental Delivery

1. **US1 first** (frontend-only, lowest risk) → validate import display
2. **US2 next** (backend LLM fix) → validate recommendations return data
3. **US3 next** (backend SSE fix) → validate schedule renders
4. **Polish** → run all quickstart scenarios end-to-end

### Parallel Strategy (single developer)

Since all 3 stories touch different files with no shared dependencies:
- Apply all 4 implementation tasks (T001-T004) in one batch
- Then validate end-to-end with T005

---

## Notes

- session_store.py and import_.py changes (raw_data storage) were already applied in a prior session — no tasks needed for those files
- All tasks modify existing files; no new files created
- Each task maps to exactly one user story for traceability
