# Feature Specification: Schedule Periods & Card Deduplication

**Feature Branch**: `010-schedule-periods-fix`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "课程表的时间列修改为每日的课程序号即可，如1-13节，无需精准对应时间。对于推荐方案中的课程card现在有重复的问题，例如一个课程一天上两节，那么视为一个课程，而不是两个课程。"

## User Scenarios & Testing

### User Story 1 - Schedule View Shows Period Numbers (Priority: P1)

As a student viewing recommended course plans, I see the schedule grid with period numbers (1-13节) as row labels instead of exact clock times (08:00-18:00).

**Why this priority**: The current time-based rows (08:00-18:00) don't match how students actually think about class periods. Students refer to "第3节" not "3". Period numbers are the standard way Chinese universities organize schedules.

**Independent Test**: View any recommendation plan's schedule grid and verify the left column shows "1", "2", ... "13" instead of "1", "2", etc.

**Acceptance Scenarios**:

1. **Given** a recommendation plan with scheduled courses, **When** the user views the schedule grid, **Then** the time column shows period numbers 1 through 13
2. **Given** a course scheduled at period 3-4, **When** the user views the schedule, **Then** the course appears in rows 3 and 4

### User Story 2 - Course Card Deduplication (Priority: P1)

As a student viewing recommended course plans, I see each course listed as exactly one card in the course list, even when that course has multiple time slots on the same day.

**Why this priority**: Duplicate cards confuse students into thinking there are more courses in the plan than actually exist. A course meeting twice on the same day should appear once, not twice.

**Independent Test**: View a recommendation plan where a course has 2 consecutive schedule slots (e.g., periods 3-4 on Monday). Verify the course list shows only one card for that course.

**Acceptance Scenarios**:

1. **Given** a course with schedule slots at periods 3 and 4 on Monday, **When** the user views the recommendation plan, **Then** only one CourseCard is displayed for that course
2. **Given** a course with schedule slots on different days, **When** the user views the recommendation plan, **Then** only one CourseCard is displayed for that course

### Edge Cases

- A course with no schedule data still displays as a single card
- Courses that appear in both morning and afternoon on the same day are still one card
- The schedule grid cells correctly show the course in all occupied period rows (not just the first)

## Requirements

### Functional Requirements

- **FR-001**: Schedule grid row labels MUST display period numbers (1, 2, 3, ... 13) instead of clock times
- **FR-002**: Schedule grid MUST have exactly 13 rows, one per period
- **FR-003**: Each course MUST appear exactly once in the course card list, regardless of how many schedule slots it has
- **FR-004**: Schedule grid cells MUST still correctly place the course in all period rows it occupies

### Key Entities

- **ScheduleView**: Component that renders the timetable grid; receives `courses` and `conflicts` props
- **Course**: Entity with `schedule` array of time slots; each slot has `day_of_week`, `start_period`, `end_period`
- **CourseCard**: Component that displays course summary; currently rendered once per schedule slot occurrence

## Success Criteria

### Measurable Outcomes

- **SC-001**: Schedule grid shows exactly 13 rows labeled 1-13, with no clock time references
- **SC-002**: Each unique course ID produces exactly one CourseCard in the recommendation plan's course list
- **SC-003**: Course placement in the schedule grid remains accurate — a course occupying periods 3 and 4 appears in both rows

## Assumptions

- Period numbering follows standard Chinese university convention: 13 periods per day (roughly 08:00 to 21:00)
- `start_period` / `end_period` in schedule slots can be mapped to period numbers (e.g., "1" → period 1, "3" → period 3)
- The `courses` array passed to ScheduleView may contain duplicate entries for the same course (multiple schedule slots); deduplication groups by course identity
