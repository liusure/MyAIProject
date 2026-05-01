# Implementation Plan: Enrich Favorites Page & Page State Preservation

**Branch**: `013-enrich-favorites-page` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-enrich-favorites-page/spec.md`

## Summary


## Technical Context

**Language/Version**: TypeScript 5.x, React 19
**Primary Dependencies**: Vite 8, React Router 7
**Storage**: N/A (frontend-only changes; backend SavedPlan model unchanged)
**Testing**: TypeScript type checker (`tsc --noEmit`), Vite production build
**Target Platform**: Modern browsers (ES2020+)
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: No measurable impact — client-side text generation is O(n) on course count
**Constraints**: Must not change backend API or data types
**Scale/Scope**: 3-4 files modified, ~80-100 lines changed

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | PASS | All changes maintain existing TypeScript types |
| Modular Design | PASS | Changes isolated to MyPlans, PlanExporter, App routing |
| Test Coverage | PASS | TypeScript compiler validates type correctness |
| Performance | PASS | O(n) text generation, no re-render bottlenecks |
| UX Consistency | PASS | Visual style unchanged; button label and export format changed |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/013-enrich-favorites-page/
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
frontend/src/
├── App.tsx                              # Modified: layout route pattern for state preservation
├── pages/
│   ├── MyPlans.tsx                      # Modified: show course count + weekly periods
│   └── CourseSelect.tsx                 # Unchanged
├── components/
│   └── PlanExporter/
│       └── PlanExporter.tsx             # Modified: client-side TXT export instead of PDF
└── types/
    └── index.ts                         # Unchanged
```

**Structure Decision**: Option 2 — Web application. Only frontend files modified; backend untouched.

## Phase 0: Research

No unknowns. All technical decisions are straightforward:

- **Course count**: Derived from `SavedPlan.course_ids.length`
- **Weekly periods**: Calculated by matching `course_ids` to session courses' schedule data on the frontend
- **TXT export**: Generate plain text string in browser, create Blob, trigger download via `<a>` element
- **State preservation**: React Router layout route with `<Outlet />` keeps page components mounted

See [research.md](research.md) for details.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md). No backend model changes — derived fields are calculated on the frontend.

### Interface Changes

**Modified: `App.tsx`**:
- Wrap `/select` and `/plans` routes in a layout route that keeps both components mounted
- Use `<Outlet />` pattern so navigating between routes doesn't unmount page components

**Modified: `MyPlans.tsx`**:
- Display `plan.course_ids.length` as "X 门课程"
- Calculate weekly periods from session course data and display as "每周 X 节"

**Modified: `PlanExporter.tsx`**:
- Replace `window.open(exportPlan(planId))` with client-side TXT generation
- Format plan data as plain text, create Blob, trigger download as `.txt` file
- Button label: "导出" instead of "导出 PDF"

### Contracts

No API changes. Frontend-only modification.

### Quickstart

See [quickstart.md](quickstart.md).

## Complexity Tracking

No violations. No entries needed.
