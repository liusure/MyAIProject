# Research: Period-Based Scheduling Standardization

## Findings

### Decision: Standardize on integer period numbers (1-13) throughout

**Rationale**: The production codebase (both backend and frontend) already uses `start_period: int` / `end_period: int` exclusively. No clock time fields (`start_time`, `end_time`) exist in any production schema, model, parser, or component.

**Alternatives considered**:
- Keep clock times and convert on the fly — rejected because it adds complexity and school-specific configuration
- Use a hybrid approach (store periods, display times) — rejected because display times require per-school configuration that doesn't exist

### Decision: Fix test files to match period-based implementation

**Rationale**: Four test files still reference the old clock-time API (`datetime.time` objects, string clock times like `"10:40"`, wrong function names). These tests would fail against the current schema and need updating to use integer periods.

**Files affected**:
- `backend/tests/test_schemas.py` — uses `time(8, 0)` instead of `8`
- `backend/tests/test_conflict_time.py` — uses string clock times instead of integer periods
- `backend/tests/test_conflict_commute.py` — imports wrong function name `_time_gap_minutes` (should be `_period_gap_minutes`), uses string arguments
- `backend/tests/test_integration_pipeline.py` — expects `time(8, 0)` instead of `8`

### Decision: No new code needed for period standardization

**Rationale**: The production code is already correct. The schedule parser, conflict detection, import pipeline, frontend types, ScheduleView, and CourseCard all use integer periods. Only the test suite needs updating.

### Decision: 50-minute-per-period heuristic in commute detection

**Rationale**: The commute conflict detector uses `(start_period - end_period) * 50` to estimate minutes between periods. This is a reasonable approximation for Chinese universities and doesn't need changing.
