# Feature Specification: Plan Favorite & Copy to Clipboard

**Feature Branch**: `012-plan-favorite-copy`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "在推荐课程界面，增加收藏与复制到剪贴板两个按钮，分别实现收藏课程方案推荐和复制课程名称及课程编号到剪贴板的功能"

## User Scenarios & Testing

### User Story 1 - Favorite a Recommended Course Plan (Priority: P1)

As a student browsing recommended course plans, I can click a "favorite" button on any recommendation plan to save it for later reference, so that I can easily find promising plans without scrolling through all recommendations again.

**Why this priority**: Favoriting lets students shortlist the best plans during their selection process. Without this, students must mentally track which plans they liked or re-run the recommendation query.

**Independent Test**: View a recommendation plan, click the favorite button, and verify the plan is visually marked as favorited and persists in a favorites list.

**Acceptance Scenarios**:

1. **Given** a recommendation plan is displayed, **When** the user clicks the favorite button, **Then** the button changes to a "favorited" state (e.g., filled icon) and the plan is added to the favorites list
2. **Given** a plan is already favorited, **When** the user clicks the favorite button again, **Then** the plan is unfavorited (unfilled icon) and removed from the favorites list
3. **Given** multiple plans are favorited, **When** the user views the favorites list, **Then** all favorited plans are displayed with their plan name, match score, and total credits

---

### User Story 2 - Copy Course Names and Numbers to Clipboard (Priority: P1)

As a student reviewing a recommended course plan, I can click a "copy to clipboard" button to copy all course names and course numbers from that plan to my system clipboard, so that I can paste them into another application (e.g., a note-taking app, registration system, or chat).

**Why this priority**: Students often need to share or record course selections outside the app. Manual copy-pasting from individual course cards is tedious and error-prone. One-click clipboard copy saves significant time.

**Independent Test**: View a recommendation plan, click the copy button, and paste into any text field to verify all course names and numbers are copied.

**Acceptance Scenarios**:

1. **Given** a recommendation plan with courses, **When** the user clicks the copy to clipboard button, **Then** all course names and course numbers are copied to the clipboard in a readable format
2. **Given** the copy succeeds, **When** the user sees the button, **Then** a brief visual confirmation (e.g., "已复制" tooltip or icon change) is shown
3. **Given** a course has no course number, **When** the copy happens, **Then** only the course name is included for that course

---

### Edge Cases

- A plan with no courses (empty plan) — copy button should indicate nothing to copy or copy an empty result gracefully
- Browser does not support clipboard API — fallback to a text selection method or show an error message
- A plan is favorited, then a new recommendation query replaces all plans — favorites should persist independently of the current recommendation results
- Rapid repeated clicks on favorite button — should toggle correctly without duplicate entries

## Requirements

### Functional Requirements

- **FR-001**: Each recommendation plan MUST display a favorite button (heart or star icon)
- **FR-002**: Clicking the favorite button MUST toggle the plan between favorited and unfavorited states
- **FR-003**: Favorited plans MUST be visually distinguishable from unfavorited plans (e.g., filled vs outline icon)
- **FR-004**: A favorites list MUST be accessible showing all favorited plans with their key details (plan name, match score, credits, courses)
- **FR-005**: Favorites MUST persist across recommendation queries within the same session
- **FR-006**: Each recommendation plan MUST display a copy to clipboard button
- **FR-007**: Clicking the copy button MUST copy all course names and course numbers from that plan to the system clipboard
- **FR-008**: The copied format MUST be human-readable, with each course on its own line showing name and number
- **FR-009**: After a successful copy, a brief visual confirmation MUST be shown to the user
- **FR-010**: Courses without a course number MUST include only the course name in the copied text

### Key Entities

- **FavoritePlan**: A saved reference to a recommended course plan, containing the plan data (name, courses, credits, match score) for later viewing
- **PlanAction**: The favorite and copy actions available on each recommendation plan card

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can favorite a plan with a single click, and the favorited state is immediately visible
- **SC-002**: Users can view all favorited plans in a dedicated list at any time
- **SC-003**: Users can copy all course names and numbers from a plan with a single click, and paste them correctly in any text field
- **SC-004**: 100% of course names and numbers are accurately copied (no truncation or format corruption)
- **SC-005**: Visual confirmation appears within 1 second of clicking the copy button

## Assumptions

- Browser supports the Clipboard API (navigator.clipboard.writeText) — standard in all modern browsers
- Favorites are session-based (stored in component state), not persisted to backend/database
- The copy format is plain text (not rich text or structured data)
- Course numbers are optional — some imported courses may not have them
- The UI follows existing design patterns in the recommendation plan cards (inline action buttons)
