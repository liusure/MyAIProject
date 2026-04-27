# Tasks: Period-Based Scheduling Standardization

**Input**: Design documents from `/specs/011-period-based-scheduling/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Test fixing is the primary work — the production code is already period-based.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Fix Schema Tests (US1 — Period Number Display)

**Goal**: Fix `test_schemas.py` so `ScheduleItem` tests use integer periods instead of `datetime.time` objects.

**Independent Test**: `python -m pytest backend/tests/test_schemas.py -v` passes

- [ ] T001 [US1] Remove unused `datetime.time` import in `backend/tests/test_schemas.py`
- [ ] T002 [US1] Replace `start_period=time(8, 0)` with `start_period=1` and `end_period=time(9, 40)` with `end_period=2` in `backend/tests/test_schemas.py`

**Checkpoint**: `test_schemas.py` passes — ScheduleItem schema validated with integer periods

---

## Phase 2: Fix Conflict Time Tests (US3 — Period-Based Conflict Detection)

**Goal**: Fix `test_conflict_time.py` so all period values are integers and clock time strings are replaced with proper period numbers.

**Independent Test**: `python -m pytest backend/tests/test_conflict_time.py -v` passes

- [ ] T003 [US3] Replace all string period values `"1"`, `"2"` with integers `1`, `2` in `backend/tests/test_conflict_time.py`
- [ ] T004 [US3] Replace clock time `"10:40"` with period `3` in `_course("B", 1, "2", "10:40")` calls in `backend/tests/test_conflict_time.py`
- [ ] T005 [US3] Replace clock time `"11:20"` with period `4` in `_course("B", 1, "2", "11:20")` call in `backend/tests/test_conflict_time.py`

**Checkpoint**: `test_conflict_time.py` passes — time conflict detection validated with integer periods

---

## Phase 3: Fix Commute Conflict Tests (US3 — Period-Based Conflict Detection)

**Goal**: Fix `test_conflict_commute.py` — fix wrong import, wrong function name, string period values, and incorrect expected values.

**Independent Test**: `python -m pytest backend/tests/test_conflict_commute.py -v` passes

- [ ] T006 [US3] Fix import: replace `_time_gap_minutes` with `_period_gap_minutes` and remove `_get_commute_time` in `backend/tests/test_conflict_commute.py`
- [ ] T007 [US3] Replace all string period values `"1"`-`"4"` with integers `1`-`4` in `_course()` calls in `backend/tests/test_conflict_commute.py`
- [ ] T008 [US3] Rewrite `TestTimeGapMinutes` class: fix function name to `_period_gap_minutes`, use integer args, update expected values to match `(start - end) * 50` formula in `backend/tests/test_conflict_commute.py`
- [ ] T009 [US3] Fix `test_conflict_insufficient_gap`: use adjacent periods (e.g., periods 1-2 and 2-3) or adjust test expectations to match the `*50` minute formula in `backend/tests/test_conflict_commute.py`

**Checkpoint**: `test_conflict_commute.py` passes — commute conflict detection validated with integer periods

---

## Phase 4: Fix Integration Pipeline Test (US1 — Period Number Display)

**Goal**: Fix `test_integration_pipeline.py` so the import pipeline assertion uses integer periods.

**Independent Test**: `python -m pytest backend/tests/test_integration_pipeline.py -v` passes

- [ ] T010 [US1] Remove unused `from datetime import time` import in `backend/tests/test_integration_pipeline.py`
- [ ] T011 [US1] Replace `assert session_courses[0].schedule[0].start_period == time(8, 0)` with `assert session_courses[0].schedule[0].start_period == 1` in `backend/tests/test_integration_pipeline.py`

**Checkpoint**: `test_integration_pipeline.py` passes — import pipeline validated producing integer periods

---

## Phase 5: Validate All Tests Pass

**Goal**: Run the full test suite to confirm all fixes work together.

**Independent Test**: `python -m pytest backend/tests/ -v` passes with 0 failures

- [ ] T012 Run full backend test suite: `cd backend && python -m pytest tests/ -v`
- [ ] T013 Verify frontend builds cleanly: `cd frontend && npx tsc --noEmit`

**Checkpoint**: All tests pass, frontend type-checks clean. Period-based standardization complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** (Schema tests): No dependencies — can start immediately
- **Phase 2** (Conflict time tests): No dependencies — can start in parallel with Phase 1
- **Phase 3** (Commute conflict tests): No dependencies — can start in parallel with Phase 1
- **Phase 4** (Integration test): No dependencies — can start in parallel with Phase 1
- **Phase 5** (Validation): Depends on Phases 1-4 all completing

### Parallel Opportunities

- All 4 fix phases (T001-T011) modify different files and can run in parallel
- Phase 5 validation must run after all fixes are applied

### Parallel Example

```bash
# All four test file fixes can happen in parallel:
Task: "Fix test_schemas.py (T001-T002)"
Task: "Fix test_conflict_time.py (T003-T005)"
Task: "Fix test_conflict_commute.py (T006-T009)"
Task: "Fix test_integration_pipeline.py (T010-T011)"
```

---

## Implementation Strategy

### Complete Fix → Validate

1. Fix all 4 test files (Phases 1-4)
2. Run full test suite (Phase 5)
3. Verify frontend type-checks clean
4. Done

### Incremental Validation

1. Fix `test_schemas.py` → verify passes
2. Fix `test_conflict_time.py` → verify passes
3. Fix `test_conflict_commute.py` → verify passes
4. Fix `test_integration_pipeline.py` → verify passes
5. Run full suite → verify all green
