# Tasks: Enrich Favorites Page & Page State Preservation

**Input**: Design documents from `/specs/013-enrich-favorites-page/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: No test tasks included — not requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `backend/src/`

---

## Phase 1: Setup

**Purpose**: Verify the project builds and existing pages load correctly before making changes.

- [X] T001 Verify frontend builds with `npx tsc --noEmit` and `npx vite build` from `frontend/`

---

## Phase 2: User Story 1 - Enriched Favorites Plan Cards (Priority: P1)

**Goal**: Each saved plan card displays course count ("X 门课程") and weekly periods ("每周 X 节") so users can quickly compare plans.

**Independent Test**: Save a plan with multiple courses, navigate to "我的方案", verify each card shows course count and weekly periods alongside existing info (name, credits, match score).

### Implementation for User Story 1

- [X] T002 [US1] Read `frontend/src/pages/MyPlans.tsx` to understand current plan card rendering and data flow
- [X] T003 [US1] Read `frontend/src/types/index.ts` to confirm `SavedPlan` and `ScheduleSlot` types
- [X] T004 [US1] Add course count display (`plan.course_ids.length` as "X 门课程") to plan cards in `frontend/src/pages/MyPlans.tsx`
- [X] T005 [US1] Add weekly periods calculation by matching `course_ids` to session course schedule data and displaying as "每周 X 节" in `frontend/src/pages/MyPlans.tsx`

**Checkpoint**: Plan cards show course count and weekly periods. Feature is independently testable.

---

## Phase 3: User Story 2 - Export as TXT Instead of PDF (Priority: P1)

**Goal**: Export button generates a `.txt` file with plan details instead of opening a backend PDF, making plan data universally accessible.

**Independent Test**: Click the export button on a saved plan, verify a `.txt` file downloads containing plan name, total credits, match score, and numbered course list.

### Implementation for User Story 2

- [X] T006 [US2] Read `frontend/src/components/PlanExporter/PlanExporter.tsx` to understand current PDF export implementation
- [X] T007 [US2] Replace backend PDF export with client-side TXT generation (Blob + download) in `frontend/src/components/PlanExporter/PlanExporter.tsx`
- [X] T008 [US2] Update export button label from "导出 PDF" to "导出" in `frontend/src/components/PlanExporter/PlanExporter.tsx`
- [X] T009 [US2] Format TXT content: plan name, total credits, match score, and numbered course list (name + course_no) in `frontend/src/components/PlanExporter/PlanExporter.tsx`

**Checkpoint**: TXT export works independently. Downloaded file is human-readable plain text.

---

## Phase 4: User Story 3 - Page State Preservation on Navigation (Priority: P2)

**Goal**: Navigating between "智能选课" and "我的方案" preserves page state (recommendations, chat history, favorites) by keeping components mounted.

**Independent Test**: Request recommendations on CourseSelect, navigate to "我的方案", navigate back to "智能选课", verify recommendations and chat history are still displayed.

### Implementation for User Story 3

- [X] T010 [US3] Read `frontend/src/App.tsx` to understand current route structure
- [X] T011 [US3] Create a layout route wrapping `/select` and `/plans` with `<Outlet />` in `frontend/src/App.tsx` so both page components stay mounted during navigation

**Checkpoint**: Page state is preserved across route changes. All three user stories are now independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all changes.

- [X] T012 Run `npx tsc --noEmit` in `frontend/` to verify type correctness
- [X] T013 Run `npx vite build` in `frontend/` to verify production build succeeds
- [ ] T014 Manual verification using quickstart.md test scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify build works first
- **User Story 1 (Phase 2)**: Depends on Phase 1. Modifies `MyPlans.tsx`.
- **User Story 2 (Phase 3)**: Depends on Phase 1. Modifies `PlanExporter.tsx`. Can run in parallel with US3 (different files).
- **User Story 3 (Phase 4)**: Depends on Phase 1. Modifies `App.tsx`. Can run in parallel with US2 (different files).
- **Polish (Phase 5)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 and US2**: Both involve `MyPlans.tsx` (US1 adds display fields, US2 uses PlanExporter rendered within MyPlans). Implement US1 before US2 for cleanest diff, but they are independently testable.
- **US3**: Fully independent — only touches `App.tsx`. Can be done in parallel with US1/US2.

### Parallel Opportunities

- T004 and T005 (both US1) are sequential — same file
- US2 tasks (T007-T009) can run after US3 (T011) since they modify different files
- T012 and T013 can run in parallel (both are validation commands)

---

## Parallel Example

```bash
# After Phase 1, US2 and US3 can run in parallel:
Task: "Replace PDF export with client-side TXT generation in frontend/src/components/PlanExporter/PlanExporter.tsx"
Task: "Create layout route wrapping /select and /plans with Outlet in frontend/src/App.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify build)
2. Complete Phase 2: User Story 1 (enriched plan cards)
3. **STOP and VALIDATE**: Check "我的方案" page shows course count and weekly periods
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → verify build works
2. Add US1 (enriched cards) → test independently
3. Add US2 (TXT export) → test independently
4. Add US3 (state preservation) → test independently
5. Final validation (type check + build + quickstart)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Then:
   - Developer A: User Story 1 (MyPlans.tsx enrichment)
   - Developer B: User Story 3 (App.tsx layout route) — can start immediately
3. After US1 complete:
   - Developer A: User Story 2 (PlanExporter.tsx TXT export)
4. All stories integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No backend changes required — all modifications are frontend-only
