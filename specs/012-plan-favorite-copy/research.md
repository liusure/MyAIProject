# Research: Plan Favorite & Copy to Clipboard

## Findings

### Decision: Frontend-only implementation with session state

**Rationale**: Both features (favorite and copy) are purely UI interactions that don't require backend persistence. Favorites use React state; clipboard uses the browser Clipboard API.

**Alternatives considered**:
- Backend-persisted favorites — rejected because the spec assumes session-based favorites and adding a backend API + DB table would expand scope significantly
- LocalStorage persistence — possible enhancement but not required for v1

### Decision: Clipboard API with fallback

**Rationale**: `navigator.clipboard.writeText()` is the standard approach. For older browsers, a fallback using a hidden textarea + `document.execCommand('copy')` can be added.

**Alternatives considered**:
- Third-party clipboard library (e.g., clipboard.js) — unnecessary for a single copy operation
- No fallback — acceptable for modern browsers; error message suffices

### Decision: Favorites stored in CourseSelect component state

**Rationale**: The `CourseSelect` component already manages `recommendations` state. Adding a `favorites` state here keeps the data flow simple. Favorites are keyed by plan identity (plan name + courses).

**Alternatives considered**:
- Separate favorites context/provider — over-engineered for session-only data
- Zustand/Redux store — unnecessary for this scope

### Decision: Action buttons in recommendation plan header

**Rationale**: The favorite and copy buttons belong at the plan level (not per-course), since they operate on the entire plan. The natural placement is in the plan header alongside the plan name and match score.

**Alternatives considered**:
- Buttons on each CourseCard — wrong scope (actions are per-plan, not per-course)
- Floating toolbar — adds visual complexity
