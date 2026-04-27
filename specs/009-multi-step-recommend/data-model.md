# Data Model: Multi-Step Course Recommendation

本 feature 不引入新实体，复用现有数据模型。

## Existing Entities (no changes)

### SessionCourse (schemas/course.py)

```python
class SessionCourse(BaseModel):
    id: str | None = None
    name: str               # 第二步非敏感字段 ✓
    credit: float           # 第二步非敏感字段 ✓ (clarification 确认)
    course_no: str | None = None      # 第二步非敏感字段 ✓ (序号/回查标识)
    instructor: str | None = None     # 第二步非敏感字段 ✓
    capacity: int | None = None       # 敏感字段 ✗ (不发送给 LLM)
    schedule: list[ScheduleItem] = [] # 第二步非敏感字段 ✓ (时间)
    location: str | None = None       # 第二步非敏感字段 ✓
    campus: str | None = None         # 敏感字段 ✗
    category: str | None = None       # 第一步过滤关键字段
    semester: str | None = None       # 敏感字段 ✗
    description: str | None = None    # 不发送 (冗余)
```

### ScheduleItem (schemas/course.py)

```python
class ScheduleItem(BaseModel):
    day_of_week: int        # 1=Mon...7=Sun
    start_period: time
    end_period: time
    weeks: list[int] = []
```

### RecommendationPlan (schemas/plan.py)

```python
class RecommendationPlan(BaseModel):
    plan_name: str
    courses: list[CourseResponse]
    total_credits: float
    match_score: float
    conflicts: list[ConflictItem] = []
```

## Data Flow

```
SessionStore (全部课程, N 条)
    │
    ▼
Step 1: 提取所有唯一 category → 发送给 LLM (多选题)
    │
    │  LLM 返回: ["计算机科学与技术", "软件工程"]
    │
    ▼
本地过滤: courses where category in matched_subjects (M 条, M << N)
    │
    ▼
Step 2: 格式化非敏感字段 → 发送给 LLM (精细筛选)
    │
    │  LLM 返回: [{plan_name, course_ids: ["序号1", "序号2"], ...}]
    │
    ▼
本地回查: course_ids → SessionStore 查找完整课程详情
    │
    ▼
冲突检测 → RecommendationPlan (含完整课程信息 + 冲突报告)
```

## Validation Rules

- `category` 字段：去重后非空列表发送给第一步 LLM；若全部为空则跳过第一步
- `course_no` 字段：第二步 LLM 返回的 course_ids 中，序号必须能从过滤后的课程子集中找到
- 匹配策略（复用现有 `_build_recommendation_plan`）：精确 ID → 精确名称 → 课号 → 部分名称匹配
