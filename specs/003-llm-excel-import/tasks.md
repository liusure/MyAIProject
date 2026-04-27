# Tasks: 学生课表智能导入与推荐

**Input**: Design documents from `/specs/003-llm-excel-import/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/import-api.md, research.md

**Tests**: Not explicitly requested in spec. No test tasks generated.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core schemas and session infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 [P] Create import-related Pydantic schemas in `backend/src/schemas/import_result.py` — ColumnMapping, MappingResult, DegradationImpact, DegradationReport, ImportAnalyzeResponse, ImportConfirmResponse
- [X] T002 [P] Add SessionCourse Pydantic schema in `backend/src/schemas/course.py` — with all fields optional except name and credit, schedule as list[ScheduleItem]
- [X] T003 Create SessionStore class in `backend/src/services/session_store.py` — in-memory dict keyed by device_id, methods: set_courses, get_courses, clear, has_courses
- [X] T004 Create import API router in `backend/src/api/import_.py` — POST /analyze, POST /confirm, GET /session/courses, DELETE /session/courses, using cookie device_id
- [X] T005 [P] Add import-related TypeScript types in `frontend/src/types/index.ts` — ImportMapping, DegradationReport, SessionCourse interfaces

**Checkpoint**: Schemas, session store, import API router, and frontend types all ready. User story work can now begin.

---

## Phase 2: User Story 1 - 学生上传任意格式课表 (Priority: P1)

**Goal**: 学生上传任意格式的 Excel 课表文件，系统通过 LLM 自动识别列名映射，提取课程数据到会话内存中。

**Independent Test**: 上传一份中文列名（课程名称、学分、任课教师...）的 Excel，验证系统自动识别列并展示课程列表。刷新页面后数据消失（不持久化）。

### Implementation for User Story 1

- [X] T006 [P] [US1] Rewrite ImportParser.parse() in `backend/src/services/import_parser.py` — remove fixed column requirement, accept MappingResult to map variable columns to system fields
- [X] T007 [P] [US1] Create ImportAnalyzer service in `backend/src/services/import_analyzer.py` — send only headers + 3 sample rows to LLM, receive column mapping, fallback to fixed format on LLM failure
- [X] T008 [P] [US1] Create FieldNormalizer service in `backend/src/services/field_normalizer.py` — normalize dates/semester via regex, extract instructor names by stripping titles, convert Chinese credit numbers, define FIELD_DEFINITIONS aliases
- [X] T009 [US1] Create FileUpload component in `frontend/src/components/FileUpload/FileUpload.tsx` and `frontend/src/components/FileUpload/FileUpload.css` — drag-and-drop + click upload, call /analyze, show mapping preview, call /confirm
- [X] T010 [US1] Add import API functions in `frontend/src/services/api.ts` — uploadAnalyze(file), confirmImport(mapping, rawData), getSessionCourses(), clearSessionCourses()
- [X] T011 [US1] Add upload entry point in `frontend/src/pages/CourseSelect.tsx` — integrate FileUpload component at page top, show imported course list after confirmation

**Checkpoint**: US1 complete — students can upload any-format Excel, see auto-detected column mapping, and have courses loaded into session memory.

---

## Phase 3: User Story 2 - Token 节省：仅发送表头+样本行 (Priority: P1)

**Goal**: 系统不将整个文件发送给 LLM，仅发送表头和前几行样本数据。日期标准化、人名提取等确定性任务通过算法完成。

**Independent Test**: 上传 100 行 Excel，验证 LLM 调用 token 数不超过 500，且日期/学期字段未经过 LLM 处理。

### Implementation for User Story 2

- [X] T012 [US2] Add exact-match fast path in `backend/src/services/import_analyzer.py` — before calling LLM, check if all column names match FIELD_DEFINITIONS aliases exactly; if so, return mapping without LLM call
- [X] T013 [US2] Add token budget enforcement in `backend/src/services/import_analyzer.py` — truncate sample rows if combined headers + data exceeds 500 token estimate; log actual token usage
- [X] T014 [US2] Verify FieldNormalizer does NOT call LLM in `backend/src/services/field_normalizer.py` — date normalization (regex), instructor name extraction (strip titles), credit conversion (Chinese→Arabic) all purely algorithmic

**Checkpoint**: US2 complete — token usage under 500, deterministic fields processed by algorithms only, exact-match columns skip LLM entirely.

---

## Phase 4: User Story 3 - 缺失字段优雅降级 (Priority: P1)

**Goal**: 学生上传的课表可能缺少某些列。系统不应因缺少非关键信息而拒绝或频繁报错，应以降级模式继续提供推荐。

**Independent Test**: 上传仅有"课程名称"和"学分"两列的 Excel，验证系统成功导入并提供基础推荐。

### Implementation for User Story 3

- [X] T015 [US3] Implement graceful degradation in `backend/src/services/import_parser.py` — when optional columns missing, set field to None instead of raising error; only require name and credit
- [X] T016 [US3] Add LLM category inference fallback in `backend/src/services/import_analyzer.py` — when category column missing, batch-send course names to LLM for category inference; mark as "未知" on failure
- [X] T017 [US3] Add degradation report generation in `backend/src/services/import_analyzer.py` — after mapping, generate DegradationReport listing missing optional fields with impact descriptions
- [X] T018 [US3] Show degradation info in `frontend/src/components/FileUpload/FileUpload.tsx` — display DegradationReport as a warning panel after /analyze response, before user confirms import

**Checkpoint**: US3 complete — missing optional fields never block import, degradation report informs user of impact, LLM infers category when missing.

---

## Phase 5: User Story 4 - 推荐结果+课表可视化与冲突检测 (Priority: P2)

**Goal**: 学生输入选课需求后，系统返回推荐方案并在可视化课表中展示课程时间分布，冲突红色高亮。

**Independent Test**: 获取推荐结果后，验证课表正确展示每门课程在对应星期和时间段的位置，冲突高亮。

### Implementation for User Story 4

- [X] T019 [US4] Modify RecommendService to use session courses in `backend/src/services/recommend.py` — add constructor parameter for session courses; _get_courses() checks SessionStore first, falls back to DB query, returns "请先上传课表" if neither available
- [X] T020 [US4] Wire ConflictEngine into recommendation flow in `backend/src/services/recommend.py` — after _build_recommendation_plan(), call ConflictEngine.detect() on plan courses, populate conflicts field; skip time detection for courses with empty schedule
- [X] T021 [US4] Update conversation endpoint for session courses in `backend/src/api/conversation.py` — pass SessionStore courses to RecommendService when available
- [X] T022 [US4] Enhance ScheduleView for conflict display in `frontend/src/components/ScheduleView/ScheduleView.tsx` — accept conflicts prop, highlight conflicting time slots in red, show "时间未指定" label for courses without schedule
- [X] T023 [US4] Add missing-time course handling in `frontend/src/components/ScheduleView/ScheduleView.tsx` — render courses without schedule in a separate "未安排时间" section below the grid

**Checkpoint**: US4 complete — recommendations use session courses, conflict detection works, timetable shows courses with conflict highlighting.

---

## Phase 6: User Story 5 - 格式校验与错误反馈 (Priority: P2)

**Goal**: 系统对提取后的数据进行校验，仅对存在的核心字段报错，不因缺失可选字段阻止导入。

**Independent Test**: 上传学分字段为"三"的 Excel，验证校验给出明确错误提示但不因缺少时间列报错。

### Implementation for User Story 5

- [X] T024 [US5] Implement row-level validation in `backend/src/services/import_parser.py` — validate core fields (name non-empty, credit numeric > 0), collect errors with row numbers; skip optional field validation entirely when column not present
- [X] T025 [US5] Display validation errors in `frontend/src/components/FileUpload/FileUpload.tsx` — show row-level error list from /confirm response, allow user to proceed with valid rows only

**Checkpoint**: US5 complete — core field errors reported with row numbers, optional field absence never generates errors.

---

## Phase 7: User Story 6 - 列映射预览 (Priority: P3)

**Goal**: LLM 完成识别后展示映射结果和降级说明，学生可确认后再进入推荐。

**Independent Test**: LLM 返回列映射后，验证页面展示映射关系和缺失字段影响说明。

### Implementation for User Story 6

- [X] T026 [US6] Create ColumnMappingPreview component in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` and `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.css` — display source→target mapping table, confidence indicators, unmapped columns, and degradation impact
- [X] T027 [US6] Integrate ColumnMappingPreview into FileUpload in `frontend/src/components/FileUpload/FileUpload.tsx` — show preview after /analyze response, require user confirmation before calling /confirm

**Checkpoint**: US6 complete — users see clear column mapping results and can confirm before import proceeds.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and integration verification across all stories.

- [X] T028 Verify end-to-end flow per `quickstart.md` — upload → analyze → confirm → course list → recommend → conflict detection → timetable display
- [X] T029 Remove or deprecate old admin import endpoint in `backend/src/api/admin.py` — mark /admin/courses/import as deprecated or redirect to new /import flow
- [X] T030 Update API documentation and verify cookie device_id works across all new import endpoints

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately. All tasks T001-T005 can mostly run in parallel.
- **Phase 2 (US1)**: Depends on Phase 1 complete.
- **Phase 3 (US2)**: Depends on Phase 1 complete. Can run parallel with US1 but builds on ImportAnalyzer.
- **Phase 4 (US3)**: Depends on Phase 2 (US1) — degradation mode builds on the working import pipeline.
- **Phase 5 (US4)**: Depends on Phase 2 (US1) — needs session courses to recommend.
- **Phase 6 (US5)**: Depends on Phase 2 (US1) — validation builds on the import pipeline.
- **Phase 7 (US6)**: Depends on Phase 2 (US1) — preview shows mapping from ImportAnalyzer.
- **Phase 8 (Polish)**: Depends on all desired stories being complete.

### User Story Dependencies

```
Phase 1 (Foundational)
    ├── Phase 2 (US1 - Upload)          ← MVP
    ├── Phase 3 (US2 - Token saving)    ← Can parallel with US1
    ├── Phase 4 (US3 - Degradation)     ← Depends on US1
    ├── Phase 5 (US4 - Recommendations) ← Depends on US1
    ├── Phase 6 (US5 - Validation)      ← Depends on US1
    └── Phase 7 (US6 - Preview)         ← Depends on US1
            └── Phase 8 (Polish)        ← Depends on all
```

### Within Each User Story

- Models/schemas before services
- Services before endpoints
- Backend before frontend (when same story)
- Core implementation before integration

### Parallel Opportunities

- **Phase 1**: T001, T002, T005 can run in parallel (different files). T003 and T004 sequential (T004 uses T003).
- **Phase 2**: T006, T007, T008 can run in parallel (different files). T009-T011 sequential within frontend.
- **Phase 3**: T012 and T013 modify same file (sequential). T014 is verification only.
- **Phase 5**: T022 and T023 modify same file (sequential).
- **Different stories**: Once Phase 1 done, US1+US2 can be parallel. US3-US6 depend on US1.

---

## Parallel Example: Phase 1

```bash
# All schema/type tasks can run together:
Task: "Create import schemas in backend/src/schemas/import_result.py"
Task: "Add SessionCourse schema in backend/src/schemas/course.py"
Task: "Add frontend types in frontend/src/types/index.ts"
```

## Parallel Example: Phase 2 (US1)

```bash
# Backend services can run together:
Task: "Rewrite ImportParser in backend/src/services/import_parser.py"
Task: "Create ImportAnalyzer in backend/src/services/import_analyzer.py"
Task: "Create FieldNormalizer in backend/src/services/field_normalizer.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Foundational schemas, SessionStore, import router
2. Complete Phase 2: US1 — upload, LLM mapping, file upload component
3. **STOP and VALIDATE**: Upload an Excel, see columns mapped, courses in session
4. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 → Foundation ready
2. Phase 2 (US1) → Upload works → **MVP!**
3. Phase 3 (US2) → Token saving verified
4. Phase 4 (US3) → Graceful degradation works
5. Phase 5 (US4) → Recommendations + timetable → **Full value!**
6. Phase 6-7 → Polish validation and preview
7. Phase 8 → Cleanup

### Parallel Team Strategy

With 2 developers after Phase 1:
- Developer A: US1 (core upload pipeline)
- Developer B: US2 (token optimization on ImportAnalyzer)

After US1+US2 complete:
- Developer A: US4 (recommendation + conflict integration)
- Developer B: US3 + US5 (degradation + validation)
- Either: US6 (preview component)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing code to reuse: ConflictEngine (backend/src/services/conflict/), ScheduleView (frontend/src/components/ScheduleView/), CourseResponse schema (backend/src/schemas/course.py)
- LLM API key (MIMO_API_KEY) required for US1/US2 LLM features; US1 ImportAnalyzer has fallback for when LLM unavailable
