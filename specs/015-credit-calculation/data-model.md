# Data Model: Fix Credit Calculation & Add Category Credit Breakdown

## Entities

### Course (existing, unchanged)

- `id: string`
- `name: string`
- `credit: number`
- `category: string | null` — e.g., "必修课", "公选课", "通识选修"

### SavedPlan (existing, unchanged)

- `id: string`
- `name: string`
- `course_ids: string[]`
- `total_credits: number` — currently always 0 (bug), will be computed correctly after fix

### Derived Fields (frontend-only)

- `categoryCredits: Map<string, number>` — credit sum grouped by category
  - Key: category string (e.g., "必修课", "公选课")
  - Value: sum of credits for courses with that category
  - Courses with `category = null` are grouped under "其他"

## Credit Calculation

### Backend (fix)

```
total_credits = sum(course.credit for course_id in plan.course_ids
                    for course in session_courses if course.id == course_id)
```

Each course is counted exactly once. A course with multiple schedule slots is still one course with one `credit` value.

### Frontend (breakdown)

```
categoryCredits = new Map()
for course in selectedCourses:
    key = course.category || "其他"
    categoryCredits.set(key, (categoryCredits.get(key) || 0) + course.credit)
```

## Display Format

```
总学分：15（必修课 10 学分 · 公选课 5 学分）
```

Single-category case:
```
总学分：12
```
