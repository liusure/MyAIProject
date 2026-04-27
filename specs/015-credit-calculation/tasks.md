# Tasks: Fix Credit Calculation & Add Category Credit Breakdown

**Input**: Design documents from `/specs/015-credit-calculation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: No test tasks included — not requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `backend/src/`

---

## Phase 1: Setup

**Purpose**: Verify the project builds before making changes.

- [X] T001 Verify frontend builds with `npx tsc --noEmit` and `npx vite build` from `frontend/`

---

## Phase 2: User Story 1 - Fix Saved Plan Credit Display (Priority: P1)

**Goal**: Saved plans show correct total credits instead of 0. The backend computes `total_credits` from session courses when saving a plan.

**Independent Test**: Save a plan with courses totaling 15 credits. Navigate to "我的方案". The plan card should show "总学分：15".

### Implementation for User Story 1

- [X] T002 [US1] Read `backend/src/api/plan.py` to understand current save endpoint
- [X] T003 [US1] Read `backend/src/services/plan_service.py` to understand the save service
- [X] T004 [US1] Modify `backend/src/api/plan.py` to look up session courses by `course_ids` and compute `total_credits` as the sum of matching courses' `credit` fields
- [X] T005 [US1] Pass computed `total_credits` to `PlanService.save()` in `backend/src/api/plan.py`

**Checkpoint**: Saved plans have correct total credits. US1 is independently testable.

---

## Phase 3: User Story 2 - Category Credit Breakdown (Priority: P1)

**Goal**: Plan cards display credit breakdown by course category (e.g., "必修课 10 学分 · 公选课 5 学分") on recommendation plans, saved plans, and TXT exports.

**Independent Test**: View a plan with courses from multiple categories. Verify category credit breakdown is displayed alongside the total.

### Implementation for User Story 2

- [X] T006 [US2] Read `frontend/src/pages/CourseSelect.tsx` to understand current credit display
- [X] T007 [P] [US2] Add category credit breakdown display to recommendation plan headers in `frontend/src/pages/CourseSelect.tsx`
- [X] T008 [P] [US2] Add category credit breakdown display to saved plan cards in `frontend/src/pages/MyPlans.tsx`
- [X] T009 [US2] Add category credit breakdown to TXT export in `frontend/src/components/PlanExporter/PlanExporter.tsx`

**Checkpoint**: Category credit breakdown is visible on all plan displays. US2 is independently testable.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all changes.

- [X] T010 Run `npx tsc --noEmit` in `frontend/` to verify type correctness
- [X] T011 Run `npx vite build` in `frontend/` to verify production build succeeds
- [ ] T012 Manual verification using quickstart.md test scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify build works first
- **User Story 1 (Phase 2)**: Depends on Phase 1. Modifies `backend/src/api/plan.py`.
- **User Story 2 (Phase 3)**: Depends on Phase 1. Modifies frontend files. Can run in parallel with US1 (different files, different layers).
- **Polish (Phase 4)**: Depends on all user stories being complete.

### Parallel Opportunities

- US1 (backend) and US2 (frontend) can run in parallel — different layers, no shared files
- T007 and T008 can run in parallel — different files (CourseSelect.tsx vs MyPlans.tsx)
- T010 and T011 can run in parallel — both are validation commands

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify build)
2. Complete Phase 2: US1 (fix total_credits bug)
3. **STOP and VALIDATE**: Save a plan, verify correct credits in MyPlans
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → verify build works
2. Add US1 → test independently (fixes critical bug)
3. Add US2 → test independently (enhances display)
4. Final validation (type check + build + quickstart)
