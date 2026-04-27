# Data Model: 课程数据仅存会话，推荐历史持久化

## Entities

### SessionCourse（现有，无变更）

现有字段不变，仅存在于内存中。

- `id: str | None` — 自动生成 UUID
- `name: str`
- `credit: float`
- `course_no: str | None`
- `instructor: str | None`
- `capacity: int | None`
- `schedule: list[ScheduleItem]`
- `location, campus, category, semester, description`

**存储**: `SessionStore._store: dict[str, list[SessionCourse]]`（内存）

**变更**: 无结构变更。

### RecommendationPlan（现有，确保快照完整）

- `plan_name: str`
- `courses: list[CourseResponse]` — 每个课程包含完整信息（名称、学分、教师、schedule 等）
- `total_credits: float`
- `match_score: float`
- `conflicts: list[ConflictItem]`

**存储**: 序列化后存入 `Conversation.messages` JSONB 字段（作为 assistant 消息的 `recommendations` 数组）

**变更**: 无结构变更。确认 `_build_recommendation_plan()` 返回的 `CourseResponse` 列表包含完整快照数据（当前已包含 id, course_no, name, credit, instructor, schedule, location, campus, category, semester）。

### Conversation（现有，无变更）

- `id: UUID`
- `device_id: str`
- `messages: list[dict]` — JSONB，包含 user/assistant 消息，assistant 消息中嵌入 recommendations 快照
- `context: dict | None`
- `created_at, updated_at`

**变更**: 无结构变更。推荐历史已通过 messages 字段自然持久化。

## 关键变更：移除 DB 回退

### RecommendService.recommend() 变更

**当前逻辑**:
```python
if self.session_courses:
    courses = self.session_courses
else:
    courses = await self._get_active_courses()  # DB 查询
```

**变更后**:
```python
if self.session_courses:
    courses = self.session_courses
else:
    return {"reply": "请先上传课表文件，然后再进行选课推荐。", "recommendations": []}
```

**影响**: `_get_active_courses()` 方法不再被调用，可以保留或删除。

## Relationships

```
用户上传 Excel → SessionStore（内存，会话生命周期）
用户请求推荐 → RecommendService 使用 SessionStore 课程 → 生成 RecommendationPlan
推荐结果 → 存入 Conversation.messages（数据库，持久化）
用户刷新页面 → SessionStore 清空，Conversation.messages 保留
用户查看历史 → 从 Conversation.messages 读取 RecommendationPlan 快照（含完整课程信息）
```
