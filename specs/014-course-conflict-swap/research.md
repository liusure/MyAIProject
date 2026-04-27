# Research: Course Conflict Swap Selection

## Findings

### Decision: Build conflict graph from backend `conflicts` array

**Rationale**: The backend already provides `Conflict[]` with `course_a`, `course_b`, and `type: 'time'`. We build a bidirectional adjacency map (`Map<string, Set<string>>`) from this data. No need to re-detect conflicts on the frontend.

**Alternatives considered**:
- Re-detect conflicts on frontend by comparing schedule overlaps — rejected because backend already provides this data and the logic is complex (week ranges, period overlap)
- Extend backend to provide a pre-built conflict graph — unnecessary; simple map construction from existing data is trivial

### Decision: Per-plan selection state with `useState<Map<planIndex, Set<courseId>>>`

**Rationale**: Each recommendation plan needs its own selection state. Using a Map keyed by plan index allows independent swap behavior per plan. Default selection is computed once per plan using a pure function.

**Alternatives considered**:
- Single global selection state — rejected because different plans have independent conflicts
- Store selection in the plan object itself — rejected because `RecommendationPlan` is a backend type; we shouldn't mutate it
- Use `useReducer` — over-engineered for this simple toggle pattern

### Decision: Hover highlighting via state + prop drilling

**Rationale**: Track `hoveredCourseId` per plan in state. On hover, look up conflict partners from the graph and pass `isConflictHighlighted` boolean to each CourseCard. Simple and performant for typical plan sizes (<10 courses).

**Alternatives considered**:
- CSS-only approach using `data-*` attributes and sibling selectors — rejected because course cards aren't siblings in the DOM (they're in a list with different nesting levels)
- Context-based approach — over-engineered for this localized interaction
- Event delegation — unnecessary complexity for hover events

### Decision: Filter courses before passing to ScheduleView and PlanActions

**Rationale**: `ScheduleView` and `PlanActions` already work with course arrays. Filtering the selected courses before passing them means no changes needed to these components' internal logic.

**Alternatives considered**:
- Pass all courses + selection set and let each component filter — rejected because it distributes filtering logic across multiple components
- Add a `visible` flag to each course object — rejected because it mutates the backend data type
