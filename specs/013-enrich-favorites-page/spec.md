# Feature Specification: Enrich Favorites Page & Page State Preservation

**Feature Branch**: `013-enrich-favorites-page`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "我的收藏界面显示信息更加丰富，显示课程门数与每周上课总节数，导出PDF功能改为导出TXT功能即可。同时修改页面切换时，原有页面不丢弃，比如切换到我的收藏，那么切换回推荐课程页面时保持原有状态。"

## User Scenarios & Testing

### User Story 1 - Enriched Favorites Plan Cards (Priority: P1)

As a student viewing my saved course plans, I see the number of courses and total weekly periods for each plan on the card, so I can quickly compare plans without opening each one.

**Why this priority**: Course count and weekly period load are key decision factors when comparing plans. Currently the card only shows credits and match score, which doesn't convey schedule intensity.

**Independent Test**: Save a plan, navigate to "我的方案", and verify each card shows "X 门课程" and "每周 X 节".

**Acceptance Scenarios**:

1. **Given** a saved plan with 5 courses totaling 18 periods per week, **When** the user views the favorites list, **Then** the card shows "5 门课程" and "每周 18 节"
2. **Given** a saved plan, **When** the user views the card, **Then** existing info (name, credits, match score, save time) is still displayed alongside the new fields

---

### User Story 2 - Export as TXT Instead of PDF (Priority: P1)

As a student, I can export a saved plan as a plain text file instead of a PDF, so I can quickly copy or share the plan details without needing a PDF reader.

**Why this priority**: TXT is universally accessible, lightweight, and easy to paste into registration systems or chat apps. PDF export adds unnecessary complexity for this use case.

**Independent Test**: Click the export button on a saved plan, and verify a `.txt` file is downloaded with the plan name, credits, and each course's name and number.

**Acceptance Scenarios**:

1. **Given** a saved plan, **When** the user clicks the export button, **Then** a `.txt` file is downloaded containing the plan name, total credits, and each course (name + course number)
2. **Given** the TXT export, **When** the user opens the file, **Then** the content is human-readable plain text

---

### User Story 3 - Page State Preservation on Navigation (Priority: P2)

As a student using the course recommendation page, when I navigate away (e.g., to "我的方案") and come back, my recommendation results and conversation history are still there, so I don't lose my work.

**Why this priority**: Currently, React Router unmounts the CourseSelect page when navigating to MyPlans, losing all state (recommendations, chat history, favorites). This forces users to re-run their query every time they check their saved plans.

**Independent Test**: Request recommendations on the course selection page, navigate to "我的方案", then navigate back to "智能选课". Verify recommendations and chat history are still visible.

**Acceptance Scenarios**:

1. **Given** the user has received recommendation results, **When** the user navigates to "我的方案" and back, **Then** the recommendation plans and chat messages are still displayed
2. **Given** the user has favorited plans, **When** the user navigates away and back, **Then** the favorited state is preserved

---

### Edge Cases

- A plan with 0 courses (edge case from data) — show "0 门课程" and "每周 0 节"
- Plan export with no courses — TXT file should still be generated with empty course list
- Very long plan name — TXT filename should be truncated or sanitized for filesystem safety

## Requirements

### Functional Requirements

- **FR-001**: Each saved plan card MUST display the number of courses (e.g., "5 门课程")
- **FR-002**: Each saved plan card MUST display the total weekly periods (e.g., "每周 18 节")
- **FR-003**: The export button MUST generate a `.txt` file instead of opening a PDF
- **FR-004**: The TXT file MUST contain the plan name, total credits, and each course with name and course number
- **FR-005**: The export button label MUST say "导出" (not "导出 PDF")
- **FR-006**: Page components MUST NOT be unmounted when navigating between routes — state must be preserved
- **FR-007**: Returning to a page MUST show the same content as when the user left it

### Key Entities

- **SavedPlan**: Backend entity storing plan data. Currently includes `course_ids` (list of course UUIDs). Needs to include or derive course count and weekly period total for display.
- **Course**: Each course has `schedule` with `start_period` and `end_period`. Weekly period total is the sum of `(end_period - start_period)` across all schedule slots across all courses.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of saved plan cards display course count and weekly period total
- **SC-002**: TXT export produces a valid, human-readable text file for every plan
- **SC-003**: Navigating away and back to the recommendation page preserves 100% of displayed state (recommendations, chat, favorites)

## Assumptions

- Weekly period total is calculated as: sum of `(end_period - start_period)` for all schedule slots across all courses in the plan
- TXT export is generated client-side (no backend changes needed for the text formatting)
- Page state preservation uses React Router's route-level caching pattern (keeping components mounted)
- The backend `SavedPlan` response already includes enough data, or course details can be fetched on demand
