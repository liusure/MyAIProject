# Research: Enrich Favorites Page & Page State Preservation

## Findings

### Decision: Calculate course count and weekly periods on the frontend

**Rationale**: The `SavedPlanResponse` already includes `course_ids` (list of UUIDs), so course count = `course_ids.length`. Weekly periods can be calculated from the session courses already loaded in the CourseSelect page by matching course IDs to their schedule data.

**Alternatives considered**:
- Add `course_count` and `weekly_periods` to backend `SavedPlan` model — rejected because it adds DB migration complexity and the data can be derived from existing fields
- Fetch course details from backend on MyPlans page load — possible but adds API calls; frontend calculation is simpler

### Decision: Client-side TXT export instead of backend PDF

**Rationale**: TXT export is simpler — format the plan data as plain text in the browser and trigger a download via Blob URL. No backend changes needed.

**Alternatives considered**:
- Keep backend PDF endpoint and add TXT endpoint — over-engineered for plain text
- Use a third-party TXT library — unnecessary for string concatenation

### Decision: Layout route pattern for page state preservation

**Rationale**: React Router v7 supports layout routes. By wrapping CourseSelect and MyPlans under a shared layout route with `<Outlet />`, both page components stay mounted when navigating between them. State is preserved because the component is never unmounted.

**Alternatives considered**:
- React `keep-alive` library — third-party dependency, not standard
- State persistence to localStorage — doesn't preserve chat streaming state
- `useOutletContext` — not needed, each page manages its own state
