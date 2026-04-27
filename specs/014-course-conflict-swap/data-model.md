# Data Model: Course Conflict Swap Selection

## Entities

### Conflict Graph (frontend-only, derived)

- `conflictGraph: Map<string, Set<string>>` — bidirectional adjacency map
  - Key: course ID
  - Value: Set of course IDs that conflict with the key course
  - Built from `RecommendationPlan.conflicts` where `type === 'time'`

### Selection State (frontend-only, per plan)

- `selectedIds: Set<string>` — currently selected course IDs for a plan
  - Default: conflict-free subset (first-seen course in each conflict pair)
  - Updated on swap click

### Hover State (frontend-only, per plan)

- `hoveredId: string | null` — ID of the course card currently hovered
  - Used to derive `conflictPartnerIds` from the conflict graph
  - Reset on mouse leave

### Derived: Conflict Partners on Hover

- `conflictPartnerIds: Set<string>` — computed from `conflictGraph.get(hoveredId)`
  - Empty set when no course is hovered
  - Used by CourseCard to apply red border

## State Transitions

```
Initial load → selectedIds = defaultConflictFreeSubset(plan)
User clicks unselected course B →
  partner = conflictGraph.get(B) ∩ selectedIds
  selectedIds = (selectedIds - partner) ∪ {B}
User clicks selected course → no-op (FR-005)
User hovers course A → hoveredId = A, conflictPartnerIds = conflictGraph.get(A)
User leaves course → hoveredId = null, conflictPartnerIds = ∅
```

## Data Flow

```
RecommendationPlan (from backend)
  → conflictGraph (built once)
  → selectedIds (state, defaults to conflict-free subset)
  → selectedCourses = plan.courses.filter(c => selectedIds.has(c.id))
  → ScheduleView(selectedCourses)
  → PlanActions(selectedCourses) [for copy/favorite]
  → CourseCard for each course [with isSelected, isConflictHighlighted]
```
