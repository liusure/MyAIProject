# Tasks: Plan Favorite & Copy to Clipboard

**Input**: Design documents from `/specs/012-plan-favorite-copy/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Not explicitly requested in spec. TypeScript type checking and build validation used instead.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the PlanActions component shell that both user stories depend on

- [x] T001 Create PlanActions component file at `frontend/src/components/PlanActions/PlanActions.tsx` with props interface accepting plan, isFavorited, onToggleFavorite, onCopy
- [x] T002 Add PlanActions component CSS at `frontend/src/components/PlanActions/PlanActions.css`

---

## Phase 2: User Story 1 - Favorite a Recommended Course Plan (Priority: P1)

**Goal**: Users can click a favorite button on each recommendation plan to toggle it into a session-based favorites list.

**Independent Test**: View a recommendation plan, click the favorite button, verify the plan is marked as favorited and appears in a favorites list. Click again to unfavorite.

### Implementation for User Story 1

- [x] T003 [US1] Add `favorites` state and `handleToggleFavorite` function in `frontend/src/pages/CourseSelect.tsx`
- [x] T004 [US1] Implement favorite button (heart icon) with toggle logic in `frontend/src/components/PlanActions/PlanActions.tsx`
- [x] T005 [US1] Render `<PlanActions>` in each recommendation plan header in `frontend/src/pages/CourseSelect.tsx`
- [x] T006 [US1] Add favorites list section below recommendations in `frontend/src/pages/CourseSelect.tsx`, showing favorited plans with name, score, credits, and courses
- [x] T007 [US1] Style favorite button states (outline vs filled heart) in `frontend/src/components/PlanActions/PlanActions.css`

**Checkpoint**: User can favorite/unfavorite plans and see them in a persistent favorites list

---

## Phase 3: User Story 2 - Copy Course Names and Numbers to Clipboard (Priority: P1)

**Goal**: Users can click a copy button on each recommendation plan to copy all course names and course numbers to the system clipboard as plain text.

**Independent Test**: View a recommendation plan, click the copy button, paste into any text field and verify all course names + numbers are present.

### Implementation for User Story 2

- [x] T008 [US2] Implement `handleCopy` function that formats courses as "课程名称（课程编号）" plain text and calls `navigator.clipboard.writeText()` in `frontend/src/components/PlanActions/PlanActions.tsx`
- [x] T009 [US2] Add copy to clipboard button (clipboard icon) in `frontend/src/components/PlanActions/PlanActions.tsx`
- [x] T010 [US2] Add "已复制" visual confirmation (icon change or tooltip) that auto-dismisses after 2 seconds in `frontend/src/components/PlanActions/PlanActions.tsx`
- [x] T011 [US2] Handle edge case: courses without course number show only name in copied text in `frontend/src/components/PlanActions/PlanActions.tsx`
- [x] T012 [US2] Style copy button and confirmation state in `frontend/src/components/PlanActions/PlanActions.css`

**Checkpoint**: User can copy all course names and numbers from a plan with one click and see confirmation

---

## Phase 4: Polish & Validation

**Purpose**: Verify the implementation works end-to-end

- [x] T013 Run TypeScript type checker: `cd frontend && npx tsc --noEmit`
- [x] T014 Run Vite production build: `cd frontend && npx vite build`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** (Setup): No dependencies — create PlanActions shell first
- **Phase 2** (US1 Favorite): Depends on Phase 1 (PlanActions component exists)
- **Phase 3** (US2 Copy): Depends on Phase 1 (PlanActions component exists) — can run in parallel with Phase 2
- **Phase 4** (Polish): Depends on Phase 2 + Phase 3

### User Story Dependencies

- **US1 (Favorite)**: Depends on Phase 1 — no dependency on US2
- **US2 (Copy)**: Depends on Phase 1 — no dependency on US1

### Parallel Opportunities

- Phase 2 (US1) and Phase 3 (US2) can proceed in parallel since they modify different parts of PlanActions.tsx
- T004 + T009 (button implementations) can be done together since they're in the same file
- T007 + T012 (CSS) can be done together

### Parallel Example: User Story 1 + 2 together

```bash
# Both stories share the same component file, so sequential within file:
Task: "Implement favorite button in PlanActions.tsx (T004)"
Task: "Implement copy button in PlanActions.tsx (T009)"
# But CourseSelect changes are independent:
Task: "Add favorites state in CourseSelect.tsx (T003)" ← parallel with T004/T009
Task: "Add favorites list section in CourseSelect.tsx (T006)" ← after T003
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Create PlanActions shell
2. Complete Phase 2: Implement favorite button + favorites list
3. **STOP and VALIDATE**: Test favorite toggle and favorites list
4. This alone delivers significant value

### Incremental Delivery

1. Complete Phase 1 → Component shell ready
2. Add US1 (Favorite) → Test independently → Value: save plans
3. Add US2 (Copy) → Test independently → Value: share plans
4. Each story adds value without breaking the other

### Parallel Team Strategy

With two developers:
1. Both complete Phase 1 together
2. Once Phase 1 done:
   - Developer A: US1 (Favorite) — CourseSelect state + PlanActions favorite button
   - Developer B: US2 (Copy) — PlanActions copy button + confirmation
3. Stories integrate in the same component file
