# Implementation Plan: Course Conflict Swap Selection

**Branch**: `014-course-conflict-swap` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-course-conflict-swap/spec.md`

## Summary

Frontend-only feature: when a recommendation plan contains time-conflicting courses, display all course cards but only render the conflict-free subset in the schedule by default. Users can click unselected conflicting course cards to swap them in (replacing their conflict partner). Hovering a course card highlights its conflicting alternatives with a red border. Copy and favorite actions use the current selection only.

## Technical Context

**Language/Version**: TypeScript 5.x, React 19
**Primary Dependencies**: Vite 8, React Router 7
**Storage**: N/A (frontend-only state management via React `useState`)
**Testing**: TypeScript type checker (`tsc --noEmit`), Vite production build
**Target Platform**: Modern browsers (ES2020+)
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: Swap in <50ms (pure state update + re-render), hover highlight instant (CSS-driven)
**Constraints**: Must not change backend API, data types, or conflict detection logic
**Scale/Scope**: 3-4 files modified, ~100-150 lines changed

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | PASS | All changes maintain existing TypeScript types |
| Modular Design | PASS | Conflict swap logic isolated to CourseSelect; visual changes in CourseCard/ScheduleView |
| Test Coverage | PASS | TypeScript compiler validates type correctness |
| Performance | PASS | O(n²) conflict graph build on plan load; O(1) swap/hover operations |
| UX Consistency | PASS | Extends existing card/schedule visual patterns; no new UI paradigms |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/014-course-conflict-swap/
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
├── pages/
│   └── CourseSelect.tsx                 # Modified: conflict graph, selection state, swap handler, hover handler
├── components/
│   ├── CourseCard/
│   │   └── CourseCard.tsx               # Modified: accept hover/click callbacks, selected/conflict visual states
│   └── ScheduleView/
│       └── ScheduleView.tsx             # Modified: receive only selected courses, not all courses
└── types/
    └── index.ts                          # Unchanged (Conflict type already defined)
```

**Structure Decision**: Option 2 — Web application. Only frontend files modified; backend untouched.

## Phase 0: Research

No unknowns. All technical decisions are straightforward:

- **Conflict graph**: Build from `plan.conflicts` (already provided by backend). Each conflict pair (A↔B) is an edge.
- **Default selection**: For each conflict pair, keep the first-seen course (index order in `plan.courses`). Build a `Set<string>` of selected course IDs.
- **Swap**: When user clicks unselected course B, remove its conflict partner A from the selected set, add B.
- **Hover**: Track `hoveredCourseId` in state; derive `conflictPartnerIds` from the conflict graph; pass to CourseCard for red border styling.
- **Selection propagation**: `mergeCourses()` → filtered to selected IDs → passed to `ScheduleView`, `PlanActions` copy, and favorite.

See [research.md](research.md) for details.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md). No backend model changes — all state is frontend-only.

### Interface Changes

**Modified: `CourseSelect.tsx`**:
- Build conflict graph (`Map<string, Set<string>>`) from `plan.conflicts` on each recommendation plan
- Compute default `selectedCourseIds: Set<string>` (conflict-free subset)
- Track `selectedIds` and `hoveredId` per plan via `useState`
- Pass selected courses (filtered) to `ScheduleView` and `PlanActions`
- Pass `onSwap`, `isSelected`, `isConflictHighlighted` to each `CourseCard`

**Modified: `CourseCard.tsx`**:
- Accept optional `onClick`, `isSelected`, `isConflictHighlighted` props
- When `isConflictHighlighted`: apply red border style
- When `isSelected=false`: apply dimmed/alternative visual style
- Click handler triggers swap callback

**Modified: `ScheduleView.tsx`**:
- No structural changes — already receives `courses` prop; just receives filtered set now

### Contracts

No API changes. Frontend-only modification.

### Quickstart

See [quickstart.md](quickstart.md).

## Complexity Tracking

No violations. No entries needed.
