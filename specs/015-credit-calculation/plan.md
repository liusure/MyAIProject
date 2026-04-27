# Implementation Plan: Fix Credit Calculation & Add Category Credit Breakdown

**Branch**: `015-credit-calculation` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-credit-calculation/spec.md`

## Summary

Two changes: (1) fix backend `total_credits` bug — currently hardcoded to 0 when saving plans, compute from session courses instead; (2) add frontend credit breakdown by course category on plan cards and exports.

## Technical Context

**Language/Version**: TypeScript 5.x / Python 3.12, React 19, FastAPI
**Primary Dependencies**: Vite 8, React Router 7, SQLAlchemy 2, Pydantic
**Storage**: PostgreSQL (SavedPlan table, `total_credits` column exists but always 0)
**Testing**: TypeScript type checker (`tsc --noEmit`), Vite production build
**Target Platform**: Modern browsers (ES2020+) + Python 3.12 server
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: No measurable impact — credit summation is O(n) on course count
**Constraints**: Category values are dynamic strings from uploaded data; no fixed enum
**Scale/Scope**: 4-5 files modified, ~60-80 lines changed

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | PASS | All changes maintain existing types |
| Modular Design | PASS | Bug fix in API layer, breakdown in frontend display |
| Test Coverage | PASS | Type checkers validate correctness |
| Performance | PASS | O(n) credit summation |
| UX Consistency | PASS | Extends existing display patterns |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/015-credit-calculation/
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
backend/src/
├── api/
│   └── plan.py                           # Modified: compute total_credits from session courses

frontend/src/
├── pages/
│   ├── CourseSelect.tsx                  # Modified: category credit breakdown on plan headers
│   └── MyPlans.tsx                       # Modified: category credit breakdown on saved plan cards
├── components/
│   └── PlanExporter/
│       └── PlanExporter.tsx              # Modified: category credit breakdown in TXT export
└── types/
    └── index.ts                          # Unchanged
```

**Structure Decision**: Option 2 — Web application. Both backend and frontend modified.

## Phase 0: Research

Key findings:

- **No duplicate credit counting**: Backend `recommend.py` sums `c.credit` once per course, not per schedule slot. The user's perception of "double counting" is likely due to the `total_credits = 0` bug making saved plans appear broken.
- **Root cause**: `backend/src/api/plan.py:24` hardcodes `total_credits = 0`. The `SavedPlanCreate` schema doesn't include `total_credits`.
- **Fix approach**: Backend looks up session courses from import state, matches against `course_ids`, sums credits. Frontend computes category breakdown from available course data.
- **Category source**: `Course.category` field (string, e.g., "必修课", "公选课"). Dynamic values from uploaded Excel or LLM inference.

See [research.md](research.md) for details.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md).

### Interface Changes

**Modified: `backend/src/api/plan.py`**:
- Import session courses lookup function
- Look up each `course_id` in session courses, sum `credit` field
- Pass computed `total_credits` to `PlanService.save()`

**Modified: `frontend/src/pages/CourseSelect.tsx`**:
- Compute `categoryCredits: Map<string, number>` from `selectedCourses`
- Display breakdown: "必修课 X 学分 · 公选课 Y 学分"

**Modified: `frontend/src/pages/MyPlans.tsx`**:
- Compute `categoryCredits` from session courses matching `plan.course_ids`
- Display breakdown on each saved plan card

**Modified: `frontend/src/components/PlanExporter/PlanExporter.tsx`**:
- Add category credit breakdown to TXT export

### Quickstart

See [quickstart.md](quickstart.md).

## Complexity Tracking

No violations. No entries needed.
