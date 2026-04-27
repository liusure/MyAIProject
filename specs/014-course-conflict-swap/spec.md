# Feature Specification: Course Conflict Swap Selection

**Feature Branch**: `014-course-conflict-swap`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "现在的选择课程仍然有冲突，那么我们改变策略，在推荐课程中，展示有冲突的课程，例如ABC三个课程中A和B冲突但是和C不冲突，那么我们优先展示A、C课程，但是当我们点击B课程的card时，取消A课程在课程表中的展示，改为展示B+C课程，同时最终复制和导出的课程以我选择的为准。"

## Clarifications

### Session 2026-04-23

- Q: When a user clicks a course card that is already selected and has a conflicting alternative, what should happen? → A: No-op — user must click the specific alternative course card to swap
- Q: How should conflicting courses be visually highlighted on hover? → A: When hovering a course card, all other courses that conflict with it display a red border

---

## User Scenarios & Testing

### User Story 1 - Conflict-Aware Course Display with Swap (Priority: P1)

As a student viewing a recommended plan that contains conflicting courses, I see the conflict-free subset displayed by default in the schedule, but I can click on a conflicting course card to swap it in (replacing the course it conflicts with), so I can choose which course to keep without the system silently hiding options.

**Why this priority**: Currently, conflicting courses are all displayed together causing visual confusion, or some are silently dropped. Students need to see all available courses and make an informed choice about which conflicting course to keep.

**Independent Test**: Given a plan with courses A, B, C where A and B time-conflict but C conflicts with neither. The schedule initially shows A + C. Clicking B's card swaps A out and shows B + C. The course list and schedule stay in sync.

**Acceptance Scenarios**:

1. **Given** a recommendation plan with courses A, B, C where A and B time-conflict, **When** the user views the plan, **Then** the schedule displays A and C (the default conflict-free subset), and B is shown as a swappable alternative
2. **Given** the default display shows A + C, **When** the user clicks B's course card, **Then** A is removed from the schedule, B and C are displayed, and B's card shows a "selected" visual indicator
3. **Given** the user has swapped to B + C, **When** the user clicks A's course card, **Then** B is removed and A + C is displayed again
4. **Given** the user has selected a specific course combination, **When** the user copies or exports the plan, **Then** only the currently selected courses are included
5. **Given** a plan with conflicting courses A and B, **When** the user hovers over course card A, **Then** course card B displays a red border, and vice versa

---

### User Story 2 - Multi-Conflict Groups (Priority: P2)

As a student with a plan containing multiple independent conflict groups (e.g., A conflicts with B, and D conflicts with E, but the two groups are independent), I can swap courses within each group independently.

**Why this priority**: Real course plans often have multiple unrelated time conflicts. Swapping in one group should not affect the other.

**Independent Test**: Given two independent conflict groups, swap in one group and verify the other group remains unchanged.

**Acceptance Scenarios**:

1. **Given** conflict group 1 (A↔B) and conflict group 2 (D↔E) with C having no conflicts, **When** the user swaps B for A, **Then** D and E remain in their default state
2. **Given** the user has made swaps in both groups, **When** the user views the schedule, **Then** the schedule reflects both swaps correctly

---

### Edge Cases

- A plan where all courses conflict with each other (complete conflict) — the system should still display all cards and let the user pick one
- A course that conflicts with multiple other courses (e.g., A conflicts with both B and C) — clicking B removes A, but C remains available as an alternative to A in a separate swap
- Three or more courses in a single conflict chain (A↔B, B↔C, A↔C) — treat as one conflict group; only non-conflicting pairs can coexist
- User swaps back and forth rapidly — state should update immediately each time

## Requirements

### Functional Requirements

- **FR-001**: The system MUST identify time-conflicting course pairs within each recommendation plan
- **FR-002**: By default, the schedule MUST display the largest conflict-free subset of courses (prefer the first-seen course in each conflict pair)
- **FR-003**: Course cards for ALL courses in the plan (including conflicting ones) MUST be displayed in the course list
- **FR-004**: Clicking a conflicting course card MUST swap it into the schedule, removing the course it conflicts with
- **FR-005**: Clicking a course card that is already selected (displayed in the schedule) MUST be a no-op; the user must click the specific alternative course card to swap
- **FR-006**: The schedule view MUST update immediately to reflect the current selection
- **FR-007**: The copy-to-clipboard function MUST include only the currently selected (displayed) courses
- **FR-008**: The favorite/save action MUST reflect the user's current course selection
- **FR-009**: Course cards MUST show a visual indicator distinguishing selected courses from unselected/conflicting alternatives
- **FR-010**: When the user hovers over a course card, all other course cards that conflict with it MUST display a red border

### Key Entities

- **RecommendationPlan**: Contains `courses` (all recommended courses) and `conflicts` (list of conflict pairs). The plan as delivered includes all courses; the UI determines which to display.
- **Course**: Individual course with `schedule` (time slots). Used to detect time conflicts by comparing schedule overlap.
- **Conflict**: Records `course_a`, `course_b`, `type` (time), `severity`, and `message`. Defines which courses cannot coexist.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of recommendation plans with conflicts show a conflict-free default display in the schedule
- **SC-002**: Clicking a conflicting course card swaps the selection within 200ms (perceived as instant)
- **SC-003**: Copy/export always reflects the user's current selection — 0 instances of exporting deselected courses
- **SC-004**: Users can identify which courses are selected vs. alternatives at a glance via visual indicators

## Assumptions

- Conflict detection is based on schedule time overlap (same `day_of_week` with overlapping `start_period`–`end_period` ranges)
- The default conflict-free subset is determined by keeping the first-seen course in each conflict pair (order from the recommendation response)
- Swapping is one-at-a-time within a conflict pair — selecting B replaces A, not adds to A
- This feature only affects the frontend display; backend conflict data and recommendation logic remain unchanged
