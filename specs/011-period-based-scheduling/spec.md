# Feature Specification: Period-Based Scheduling Standardization

**Feature Branch**: `011-period-based-scheduling`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "由于每个学校的课程时间不统一，因此整个项目对于课程的规划基于课程在每一天的序号，认为每天有13节课，然后每个课程分为1-13，其中1-4是上午 5-8是下午 9-13为晚上。"

## User Scenarios & Testing

### User Story 1 - Standardized Period Numbers in Course Schedule (Priority: P1)

As a student, I see all course schedules represented as period numbers (1-13) rather than clock times, so that the system works correctly regardless of which school's timetable convention I follow.

**Why this priority**: This is the core design decision. Different universities use different time slots for each period. By standardizing on period numbers, the system becomes universally applicable. Morning periods (1-4), afternoon periods (5-8), and evening periods (9-13) give students a clear mental model.

**Independent Test**: Upload a course file, view any course's schedule, and verify all time references use period numbers 1-13 instead of specific clock times like "08:00".

**Acceptance Scenarios**:

1. **Given** a course with schedule data, **When** the user views the course card, **Then** the schedule displays as "周一（3-4节）" instead of "周一 10:00-11:40"
2. **Given** a course imported from Excel with clock times, **When** the system processes the import, **Then** clock times are converted to period numbers 1-13
3. **Given** a recommendation plan, **When** the user views the weekly schedule grid, **Then** rows are labeled 1-13 with period number labels, not clock times

---

### User Story 2 - Time-of-Day Grouping Awareness (Priority: P2)

As a student, I understand that periods 1-4 are morning, 5-8 are afternoon, and 9-13 are evening, so I can mentally map periods to approximate times at my own school.

**Why this priority**: Students need to relate period numbers to real-world time. The morning/afternoon/evening grouping provides context without hardcoding specific clock times.

**Independent Test**: View the schedule grid and verify that the period grouping (morning/afternoon/evening) is visually or textually indicated.

**Acceptance Scenarios**:

1. **Given** the schedule grid, **When** the user views periods 1-4, **Then** they are visually grouped or labeled as morning
2. **Given** the schedule grid, **When** the user views periods 5-8, **Then** they are visually grouped or labeled as afternoon
3. **Given** the schedule grid, **When** the user views periods 9-13, **Then** they are visually grouped or labeled as evening

---

### User Story 3 - Conflict Detection Uses Period Numbers (Priority: P1)

As a student, I expect the conflict detection system to correctly identify overlapping courses based on period numbers, so that I don't accidentally select courses that overlap in time.

**Why this priority**: Accurate conflict detection is critical for course selection. If clock times were used instead of periods, conflicts might be missed or falsely detected when schools have different time conventions.

**Independent Test**: Select two courses that occupy the same period on the same day, and verify the system flags them as conflicting.

**Acceptance Scenarios**:

1. **Given** two courses both scheduled at period 3 on Monday, **When** the user selects both, **Then** the system detects a time conflict
2. **Given** two courses at periods 3 and 5 on Monday, **When** the user selects both, **Then** the system reports no conflict (different periods)

---

### Edge Cases

- A course spanning the boundary between morning and afternoon (e.g., periods 4-5) should display correctly across both groups
- Courses with no schedule data should still appear as cards but be listed separately as "时间未指定"
- Imported data with no recognizable time or period format should produce a clear error message

## Requirements

### Functional Requirements

- **FR-001**: All course schedule data throughout the system MUST use period numbers 1-13, not clock times
- **FR-002**: The system MUST define 13 periods per day as the standard schedule model
- **FR-003**: Periods 1-4 MUST be classified as morning, 5-8 as afternoon, 9-13 as evening
- **FR-004**: Course import from Excel MUST convert any clock-time data to period numbers before storage
- **FR-005**: The weekly schedule grid MUST display rows labeled 1 through 13
- **FR-006**: Course cards MUST display schedule as period numbers (e.g., "3-4节") not clock times
- **FR-007**: Conflict detection MUST operate on period number overlap, not clock time overlap
- **FR-008**: The recommendation engine MUST use period numbers when checking for scheduling feasibility

### Key Entities

- **Period**: A numbered time slot in a day, ranging from 1 to 13. Periods 1-4 are morning, 5-8 are afternoon, 9-13 are evening.
- **ScheduleSlot**: Represents when a course meets — consists of day_of_week, start_period, end_period, and weeks. No clock times.
- **Course**: A selectable course with schedule slots using period numbers. All time references are period-based.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of schedule displays (course cards, grid view, conflict reports) use period numbers, with zero clock time references visible to users
- **SC-002**: Course import from Excel correctly converts clock times to period numbers with no data loss
- **SC-003**: Conflict detection accuracy is 100% when comparing courses using period numbers on the same day
- **SC-004**: The schedule grid renders exactly 13 rows, one per period, with clear morning/afternoon/evening grouping

## Assumptions

- The 13-period model is a reasonable universal abstraction; individual schools can map periods to their own clock times
- Period numbering follows standard Chinese university convention where morning starts at period 1
- Clock-time-to-period conversion during import is a best-effort mapping and may need school-specific configuration in the future
- All schedule-related data in the backend (database, API responses) already uses or will be standardized to `start_period` / `end_period` integer fields
