# Research: Fix Credit Calculation & Add Category Credit Breakdown

## Findings

### Decision: Compute total_credits on backend from session courses

**Rationale**: The backend API endpoint (`api/plan.py`) currently hardcodes `total_credits = 0`. The session courses (from the import flow) are accessible via the backend's session state. By looking up each `course_id` in the session courses and summing their `credit` fields, we get the correct total without changing the database schema or API contract.

**Alternatives considered**:
- Frontend sends `total_credits` in the request body — possible but doesn't fix the root cause; also doesn't help with category breakdown needing course data
- Database migration to add `credit_breakdown` column — over-engineered; breakdown is derived data

### Decision: Compute category breakdown on frontend from course data

**Rationale**: The frontend already has access to course data (session courses in MyPlans, plan courses in CourseSelect). Computing a `Map<string, number>` of category→credits is trivial and doesn't require backend changes. Category values are dynamic strings from uploaded data.

**Alternatives considered**:
- Backend computes and returns breakdown in API response — adds API complexity for a display concern
- Store breakdown in SavedPlan — unnecessary; always derivable from course_ids

### Decision: Backend fix uses getSessionCourses API or session state

**Rationale**: The backend already has session courses accessible (used by the recommendation flow). The save endpoint can look up courses by ID from the same session state.

**Implementation note**: The `get_session_courses` equivalent is available via the import module's session state. The API endpoint can import and use it to look up courses by `course_id`.

### Decision: Category display — show only when multi-category

**Rationale**: If all courses in a plan share the same category, showing "必修课 12 学分" alongside "总学分：12" is redundant. Only show breakdown when there are 2+ categories.
