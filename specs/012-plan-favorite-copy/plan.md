# Implementation Plan: Plan Favorite & Copy to Clipboard

**Branch**: `012-plan-favorite-copy` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-plan-favorite-copy/spec.md`

## Summary

Add two action buttons (favorite and copy to clipboard) to each recommendation plan card in the CourseSelect page. Favorite toggles a plan into a session-based favorites list. Copy copies all course names and numbers to the system clipboard as plain text. Both are frontend-only features — no backend changes.

## Technical Context

**Language/Version**: TypeScript 5.x, React 19
**Primary Dependencies**: Vite 8, React Router
**Storage**: N/A (session state only)
**Testing**: TypeScript type checker (`tsc --noEmit`), Vite production build
**Target Platform**: Modern browsers (ES2020+)
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: No measurable impact — clipboard copy is O(n) on course count, favorites toggle is O(1)
**Constraints**: Must not change backend API or data types
**Scale/Scope**: 2-3 files modified, ~80-100 lines added

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | PASS | New state and functions maintain existing TypeScript types |
| Modular Design | PASS | Changes isolated to CourseSelect page and a new PlanActions component |
| Test Coverage | PASS | TypeScript compiler validates type correctness; production build validates rendering |
| Performance | PASS | O(1) favorite toggle, O(n) clipboard copy, no re-render bottlenecks |
| UX Consistency | PASS | Action buttons follow existing inline-button design pattern |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/012-plan-favorite-copy/
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
├── components/
│   └── PlanActions/
│       └── PlanActions.tsx    # New: favorite + copy button component
├── pages/
│   └── CourseSelect.tsx       # Modified: add favorites state, render PlanActions + favorites list
└── types/
    └── index.ts               # Unchanged (RecommendationPlan already has needed fields)
```

**Structure Decision**: Option 2 — Web application. Only frontend files modified; backend untouched.

## Phase 0: Research

No unknowns. All technical decisions are straightforward:

- **Clipboard API**: Use `navigator.clipboard.writeText()` — standard in all modern browsers
- **Favorites state**: Store in CourseSelect component as `useState<RecommendationPlan[]>`
- **Button placement**: At the plan card level (not per-course), in the plan header area
- **Copy format**: Plain text, one course per line, "课程名称（课程编号）" format

See [research.md](research.md) for details.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md). No new entities — `RecommendationPlan` is reused as the favorite item.

### Interface Changes

**New file: `PlanActions.tsx`**:
- Props: `plan: RecommendationPlan`, `isFavorited: boolean`, `onToggleFavorite: () => void`
- Renders two icon buttons: favorite (heart) and copy (clipboard)
- Copy button calls `navigator.clipboard.writeText()` with formatted course list
- Shows "已复制" confirmation for 2 seconds after copy

**Modified: `CourseSelect.tsx`**:
- Add `const [favorites, setFavorites] = useState<RecommendationPlan[]>([]);`
- Add toggle handler: `handleToggleFavorite(plan)` — adds/removes plan from favorites
- Render `<PlanActions>` inside each recommendation plan card header
- Add a favorites section below the recommendations, showing all favorited plans

### Contracts

No API changes. Frontend-only modification.

### Quickstart

See [quickstart.md](quickstart.md).

## Complexity Tracking

No violations. No entries needed.
