# Data Model: Schedule Periods & Card Deduplication

No new entities introduced. This feature restructures display logic only.

## Existing Entities (unchanged)

### ScheduleSlot
- `day_of_week: number` — 1=Monday through 7=Sunday
- `start_period: string` — e.g. "1", "3"
- `end_period: string` — e.g. "3", "12:00"
- `weeks: number[]` — which weeks the slot applies to

### Course
- `id: string` — unique identifier (used for dedup key)
- `name: string`
- `schedule: ScheduleSlot[]` — zero or more time slots
- ... other fields unchanged

### ScheduleView (component)
- Props: `courses: ScheduleCourse[]`, `conflicts?: Conflict[]`
- `slotMap`: `Map<string, ScheduleCourse[]>` keyed by `"${day_of_week}-${period}"`
- Each period row maps to one or more courses

### CourseCard (component)
- Props: `course: Course`
- Renders one card per course — deduplication ensures no duplicates in the list
