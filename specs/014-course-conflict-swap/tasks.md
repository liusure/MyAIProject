# Tasks: Course Conflict Swap Selection

**Input**: Design documents from `/specs/014-course-conflict-swap/`
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

## Phase 2: User Story 1 - Conflict-Aware Course Display with Swap (Priority: P1)

**Goal**: All course cards are displayed, but the schedule shows only the conflict-free subset by default. Clicking an unselected conflicting course swaps it in. Hovering highlights conflict partners with a red border.

**Independent Test**: Given a plan with A, B, C where A and B time-conflict: schedule shows A+C by default, all 3 cards visible, clicking B swaps to B+C, hovering A highlights B with red border.

### Implementation for User Story 1

- [X] T002 [US1] Read `frontend/src/pages/CourseSelect.tsx` to understand current recommendation rendering
- [X] T003 [US1] Read `frontend/src/components/CourseCard/CourseCard.tsx` to understand current card props and styling
- [X] T004 [US1] Build conflict graph (`Map<string, Set<string>>`) from `plan.conflicts` and compute default selected IDs in `frontend/src/pages/CourseSelect.tsx`
- [X] T005 [US1] Add per-plan `selectedIds` state and `hoveredId` state in `frontend/src/pages/CourseSelect.tsx`
- [X] T006 [US1] Implement swap handler: clicking unselected course removes its conflict partner from selection, adds itself in `frontend/src/pages/CourseSelect.tsx`
- [X] T007 [US1] Filter `plan.courses` by `selectedIds` before passing to `ScheduleView` and `PlanActions` in `frontend/src/pages/CourseSelect.tsx`
- [X] T008 [US1] Add `onClick`, `isSelected`, `isConflictHighlighted` props to `frontend/src/components/CourseCard/CourseCard.tsx`
- [X] T009 [US1] Style CourseCard: selected=normal, unselected=dimmed, hover-conflict=red border in `frontend/src/components/CourseCard/CourseCard.tsx`

**Checkpoint**: Conflict-aware display and swap work. Schedule shows selected courses only. Hover highlights conflict partners.

---

## Phase 3: User Story 2 - Multi-Conflict Groups (Priority: P2)

**Goal**: Multiple independent conflict groups can be swapped independently. Swapping in one group doesn't affect another.

**Independent Test**: Given two independent conflict groups (A↔B and D↔E) plus course C with no conflicts: swap B for A, verify D/E unchanged.

### Implementation for User Story 2

- [X] T010 [US2] Verify that the conflict graph and selection logic from US1 handles multiple independent groups correctly — each conflict pair is evaluated independently in `frontend/src/pages/CourseSelect.tsx`

**Checkpoint**: All user stories independently functional.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all changes.

- [X] T011 Run `npx tsc --noEmit` in `frontend/` to verify type correctness
- [X] T012 Run `npx vite build` in `frontend/` to verify production build succeeds
- [ ] T013 Manual verification using quickstart.md test scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify build works first
- **User Story 1 (Phase 2)**: Depends on Phase 1. Modifies `CourseSelect.tsx` and `CourseCard.tsx`.
- **User Story 2 (Phase 3)**: Depends on US1 (uses the same conflict graph logic). Verification task only.
- **Polish (Phase 4)**: Depends on all user stories being complete.

### Parallel Opportunities

- T008 and T009 (CourseCard changes) can conceptually be done together since they're in the same file
- T004-T007 are sequential — all in CourseSelect.tsx
- T011 and T012 can run in parallel (both are validation commands)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify build)
2. Complete Phase 2: US1 (conflict graph, selection state, swap, hover, visual indicators)
3. **STOP and VALIDATE**: Test conflict-aware display and swap in browser
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → verify build works
2. Add US1 → test independently (core feature)
3. Verify US2 → multi-group independence (automatically works with US1's design)
4. Final validation (type check + build + quickstart)
