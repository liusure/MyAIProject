# Data Model: Period-Based Scheduling

## Entities

### ScheduleItem (unchanged)
- `day_of_week: int` — 1=Monday, 7=Sunday
- `start_period: int` — 1-13
- `end_period: int` — 1-13 (exclusive: range is [start_period, end_period))
- `weeks: list[int]` — e.g., [1, 2, 3, ..., 16]

### Course (unchanged)
- `id: string/UUID`
- `name: string`
- `schedule: ScheduleSlot[]` — list of period-based time slots

### ConflictItem (unchanged)
- `type: 'time' | 'location' | 'prerequisite' | 'commute'`
- `severity: 'error' | 'warning'`
- `course_a: UUID`, `course_b: UUID`
- `message: string`

## Validation Rules

- `start_period` and `end_period` MUST be integers in range [1, 13]
- `end_period` MUST be greater than `start_period`
- `day_of_week` MUST be integer in range [1, 7]
- `weeks` entries MUST be positive integers

## Period-to-Time-of-Day Mapping (display only)

| Periods | Time of Day |
|---------|-------------|
| 1-4     | Morning     |
| 5-8     | Afternoon   |
| 9-13    | Evening     |

This mapping is used for visual grouping in the schedule grid. No clock times are stored or displayed.
