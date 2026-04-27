# Data Model: Enrich Favorites Page & Page State Preservation

## Entities

### SavedPlan (existing, unchanged)

- `id: string`
- `name: string`
- `course_ids: string[]` — used to derive course count
- `total_credits: number`
- `match_score: number | null`
- `notes: string | null`
- `created_at: string`

### Derived Fields (frontend-only, not stored)

- `course_count`: `course_ids.length`
- `weekly_periods`: Sum of `(end_period - start_period)` for all schedule slots across all courses in the plan. Calculated by matching `course_ids` to session course schedule data.

### TXT Export Format

```
方案名称：{plan_name}
总学分：{total_credits}
匹配度：{match_score}%
课程列表：
1. {course_name}（{course_no}）
2. {course_name}（{course_no}）
...
```

Each line is plain text, UTF-8 encoded.
