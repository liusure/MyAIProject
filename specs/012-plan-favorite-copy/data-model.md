# Data Model: Plan Favorite & Copy to Clipboard

## Entities

### FavoritePlan (in-memory only, not persisted)

- `plan_name: string`
- `courses: Course[]` — full course list from the recommendation
- `total_credits: number`
- `match_score: number`
- `favorited_at: number` — timestamp for ordering

### RecommendationPlan (existing, unchanged)

- `plan_name: string`
- `courses: Course[]`
- `total_credits: number`
- `match_score: number`
- `conflicts: Conflict[]`

## State Shape

```typescript
// In CourseSelect component
const [favorites, setFavorites] = useState<RecommendationPlan[]>([]);
```

## Clipboard Output Format

```
课程名称 1（课程编号 1）
课程名称 2（课程编号 2）
课程名称 3
```

- Each course on its own line
- Course number shown in parentheses if present
- Courses without course number show only the name
