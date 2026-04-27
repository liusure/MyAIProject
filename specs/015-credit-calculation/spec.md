# Feature Specification: Fix Credit Calculation & Add Category Credit Breakdown

**Feature Branch**: `015-credit-calculation`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "现在的学分统计有问题，比如一个课程上两节算了两次分，修改为一个课程永远只算一次分。其次课程学分除了总学分以外，还应该分别显示课程种类的分数（如公选课分数、必修课分数，具体key从上传文件和推荐的课程记录中获取）"

## Clarifications

### Session 2026-04-23

*None yet*

---

## User Scenarios & Testing

### User Story 1 - Fix Saved Plan Credit Display (Priority: P1)

As a student viewing my saved plans, the total credits should reflect the actual sum of course credits, not zero.

**Why this priority**: Currently all saved plans show "总学分：0" because the backend hardcodes `total_credits = 0` when saving. This is a critical data correctness bug.

**Independent Test**: Save a plan with courses totaling 15 credits. Navigate to "我的方案". The plan card should show "总学分：15", not "总学分：0".

**Acceptance Scenarios**:

1. **Given** a recommendation plan with total credits 15, **When** the user saves it, **Then** the saved plan's `total_credits` is 15
2. **Given** a saved plan with `total_credits` = 15, **When** the user views "我的方案", **Then** the card shows "总学分：15"
3. **Given** a saved plan, **When** the user exports it as TXT, **Then** the file shows the correct total credits

---

### User Story 2 - Category Credit Breakdown (Priority: P1)

As a student viewing a recommendation plan or saved plan, I see credits broken down by course category (e.g., "必修课 8 学分 · 公选课 4 学分") in addition to the total, so I can quickly verify I'm meeting requirements for each category.

**Why this priority**: Students need to balance credits across categories (required vs. elective). Showing only total credits doesn't reveal whether the plan meets category-specific requirements.

**Independent Test**: View a plan with courses from multiple categories. Verify that credit breakdown by category is displayed alongside the total.

**Acceptance Scenarios**:

1. **Given** a plan with 3 courses: 2 required (8 credits) and 1 elective (4 credits), **When** the user views the plan, **Then** it shows "必修课 8 学分 · 公选课 4 学分" (or equivalent breakdown)
2. **Given** a plan where all courses are the same category, **When** the user views the plan, **Then** only the total is shown (no redundant breakdown)
3. **Given** a saved plan with category breakdown, **When** the user exports as TXT, **Then** the file includes the category credit breakdown

---

### Edge Cases

- A course with `category = null` — group under "其他" (Other) or exclude from breakdown
- A plan with 0 courses — show "总学分：0" with no breakdown
- Very long category names — truncate or abbreviate in the UI
- Backend `SavedPlan.total_credits` currently stores 0 for all existing plans — after fix, only newly saved plans will have correct values (existing plans remain 0)

## Requirements

### Functional Requirements

- **FR-001**: The backend MUST compute `total_credits` from `course_ids` when saving a plan, not hardcode it to 0
- **FR-002**: Each course's credit MUST be counted exactly once regardless of how many schedule slots it has
- **FR-003**: The system MUST display a credit breakdown by course category on recommendation plan cards
- **FR-004**: The system MUST display a credit breakdown by course category on saved plan cards (MyPlans)
- **FR-005**: The category breakdown MUST use category values from the uploaded course data (e.g., "必修课", "公选课", "通识选修")
- **FR-006**: The TXT export MUST include the category credit breakdown
- **FR-007**: If all courses belong to a single category, the breakdown MAY be omitted to avoid redundancy

### Key Entities

- **Course**: Has `credit: number` and `category: string | null`. Category comes from uploaded Excel data or LLM inference.
- **SavedPlan**: Has `total_credits: number` — currently always 0 (bug). Should be sum of constituent course credits.
- **RecommendationPlan**: Has `total_credits: number` and `courses: Course[]`. Category breakdown is derived from courses.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of newly saved plans have correct `total_credits` (not 0)
- **SC-002**: Category credit breakdown is displayed on 100% of plan cards with multi-category courses
- **SC-003**: Exported TXT files contain correct total credits and category breakdown

## Assumptions

- Category values are strings from the uploaded course data (e.g., "必修课", "公选课", "通识选修", "专业基础")
- The `category` field on each course is already populated (either from Excel or LLM inference)
- Category breakdown is computed on the frontend from the course list — no backend schema changes needed for the breakdown itself
- The `total_credits` fix requires a backend change to the save endpoint
