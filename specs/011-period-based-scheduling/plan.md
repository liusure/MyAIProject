# Implementation Plan: Period-Based Scheduling Standardization

**Branch**: `011-period-based-scheduling` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-period-based-scheduling/spec.md`

## Summary

Standardize all schedule data to use integer period numbers (1-13) instead of clock times. The production code (backend + frontend) is already fully period-based. The primary work is fixing 4 test files that still reference the old clock-time API (`datetime.time` objects, string clock times, wrong function names).

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, React 19, Vite 8
**Storage**: PostgreSQL with JSONB for schedule data
**Testing**: pytest (backend), TypeScript compiler + Vite build (frontend)
**Target Platform**: Modern browsers (ES2020+), Python 3.11+ server
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: No measurable impact — period-based comparison is O(1)
**Constraints**: Must not change backend API or data types (already correct)
**Scale/Scope**: 4 test files modified, ~50 lines changed, no production code changes

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | PASS | All changes maintain existing type annotations; test fixes ensure type consistency |
| Modular Design | PASS | Changes isolated to test files; no production code modified |
| Test Coverage | PASS | Fixing tests improves coverage from broken to passing |
| Performance | PASS | No performance impact — test-only changes |
| UX Consistency | PASS | No frontend changes needed; already period-based |

## Project Structure

### Documentation (this feature)

```text
specs/011-period-based-scheduling/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: data model
├── quickstart.md        # Phase 1: quickstart guide
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── schemas/course.py        # ScheduleItem (already period-based, unchanged)
│   ├── services/
│   │   ├── conflict/time.py     # Time conflict detection (already period-based, unchanged)
│   │   ├── conflict/commute.py  # Commute conflict (already period-based, unchanged)
│   │   └── schedule_parser.py   # Parser (already period-based, unchanged)
│   └── ...
└── tests/
    ├── test_schemas.py               # FIX: replace time() with int
    ├── test_conflict_time.py         # FIX: replace string times with int periods
    ├── test_conflict_commute.py      # FIX: fix import, replace strings with ints
    └── test_integration_pipeline.py  # FIX: replace time() with int

frontend/
├── src/
│   ├── types/index.ts           # ScheduleSlot (already period-based, unchanged)
│   ├── components/ScheduleView/ # Already uses periods, unchanged
│   ├── components/CourseCard/   # Already uses periods, unchanged
│   └── pages/CourseSelect.tsx   # Already uses periods, unchanged
└── ...
```

**Structure Decision**: Option 2 — Web application. Only test files modified; no production code changes needed.

## Phase 0: Research

All unknowns resolved. See [research.md](research.md) for details.

Key findings:
- Production code is 100% period-based already
- 4 test files need updating to match the period-based API
- No clock time fields exist anywhere in production

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md). No schema changes — `ScheduleItem` already uses `start_period: int` / `end_period: int`.

### Interface Changes

No API or interface changes. The test files need to match the existing period-based interfaces.

### Test File Fixes

**`backend/tests/test_schemas.py`**:
- Replace `start_period=time(8, 0)` → `start_period=8`
- Replace `end_period=time(9, 40)` → `end_period=9`

**`backend/tests/test_conflict_time.py`**:
- Replace string clock times like `"10:40"` → integer periods like `10`
- Replace helper function `_course("B", 1, "2", "10:40")` → `_course("B", 1, 3, 4)` (or similar period values)

**`backend/tests/test_conflict_commute.py`**:
- Fix import: `_time_gap_minutes` → `_period_gap_minutes`
- Fix import: `_get_commute_time` → remove (function doesn't exist) or update
- Replace string arguments `"2"`, `"3"` → integer `2`, `3`
- Update expected values: `20` minutes → `50` minutes (since `(3-2) * 50 = 50`)

**`backend/tests/test_integration_pipeline.py`**:
- Replace `assert ... == time(8, 0)` → `assert ... == 8`

### Quickstart

See [quickstart.md](quickstart.md).

## Complexity Tracking

No violations. No entries needed.
