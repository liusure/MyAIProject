# Data Model: 学生课表智能导入与推荐

## 实体关系

```
SessionCourse (内存)
    ↓ 用于
RecommendService → ConflictEngine → ConflictItem
    ↓ 生成
RecommendationPlan → SavedPlan (DB, cookie关联)
```

## 1. SessionCourse (会话课程 - 内存)

课程数据存在于内存中，随会话结束清除。不建 DB 表。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | str (UUID) | 自动生成 | 会话内唯一标识 |
| name | str | **核心** | 课程名称 |
| credit | float | **核心** | 学分 |
| course_no | str | 可选 | 课程编号，缺失时用 name 去重 |
| instructor | str | 可选 | 主讲人，缺失时跳过教师筛选 |
| capacity | int | 可选 | 容量 |
| location | str | 可选 | 上课地点 |
| campus | str | 可选 | 校区 |
| category | str | 可选 | 分类，缺失时 LLM 推断 |
| semester | str | 可选 | 学期，缺失时跳过学期筛选 |
| schedule | list[ScheduleItem] | 可选 | 上课时间，缺失时跳过冲突检测 |
| description | str | 可选 | 课程描述 |

### ScheduleItem (内存)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| day_of_week | int | 是 | 1-7 (周一至周日) |
| start_period | str | 是 | HH:MM 格式 |
| end_period | str | 是 | HH:MM 格式 |
| weeks | list[int] | 可选 | 周次列表，默认 [1-16] |

## 2. FieldSchema (字段定义 - 代码常量)

定义在 `field_normalizer.py` 中，不存 DB。

```python
FIELD_DEFINITIONS: dict[str, FieldSchema] = {
    "name":       FieldSchema(label="课程名称",  aliases=["课程名称","课程名","course","name","课程","course_name"],  required=True),
    "credit":     FieldSchema(label="学分",      aliases=["学分","credit","credits","score"],                         required=True),
    "course_no":  FieldSchema(label="课程编号",  aliases=["课程编号","编号","code","course_no","course_code","id"],    required=False),
    "instructor": FieldSchema(label="主讲人",    aliases=["主讲人","教师","老师","instructor","teacher","lecturer"],   required=False),
    "capacity":   FieldSchema(label="容量",      aliases=["容量","名额","capacity","seats","max_students"],             required=False),
    "location":   FieldSchema(label="上课地点",  aliases=["上课地点","地点","教室","location","room","classroom"],      required=False),
    "campus":     FieldSchema(label="校区",      aliases=["校区","campus","area"],                                      required=False),
    "category":   FieldSchema(label="分类",      aliases=["分类","类别","category","type","kind"],                      required=False),
    "semester":   FieldSchema(label="学期",      aliases=["学期","semester","term"],                                    required=False),
    "schedule":   FieldSchema(label="上课时间",  aliases=["上课时间","时间","schedule","time","上课安排"],              required=False),
}
```

## 3. ColumnMapping (列映射 - LLM 返回)

```python
class ColumnMapping(BaseModel):
    source: str          # 原始 Excel 列名
    target: str          # 系统字段名 (FIELD_DEFINITIONS 的 key)
    confidence: float    # LLM 置信度 0-1

class MappingResult(BaseModel):
    mappings: list[ColumnMapping]     # 成功映射的列
    unmapped_source: list[str]        # 未匹配的原始列名（忽略）
    unmapped_target: list[str]        # 未匹配的系统字段名（降级）
```

## 4. DegradationReport (降级报告 - 内存)

导入完成后生成，传给前端展示。

```python
class DegradationReport(BaseModel):
    missing_fields: list[str]         # 缺失的可选字段名
    impacts: list[DegradationImpact]  # 缺失影响说明

class DegradationImpact(BaseModel):
    field: str                        # 缺失字段名
    impact: str                       # 影响说明（中文）
    fallback: str                     # 降级策略说明
```

示例:
```json
{
  "missing_fields": ["schedule", "category"],
  "impacts": [
    {"field": "schedule", "impact": "无法检测时间冲突", "fallback": "课程将在课表中标记为'时间未指定'"},
    {"field": "category", "impact": "无法按分类筛选", "fallback": "将根据课程名称自动推断分类"}
  ]
}
```

## 5. SessionStore (会话存储 - 内存单例)

```python
class SessionStore:
    """内存中的会话课程存储，以 device_id 为 key"""

    _store: dict[str, list[SessionCourse]] = {}

    def set_courses(self, device_id: str, courses: list[SessionCourse]) -> None: ...
    def get_courses(self, device_id: str) -> list[SessionCourse] | None: ...
    def clear(self, device_id: str) -> None: ...
    def has_courses(self, device_id: str) -> bool: ...
```

## 6. SavedPlan (保存方案 - DB，已有)

复用现有 SavedPlan 模型，通过 cookie device_id 关联。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| device_id | str | cookie 关联 |
| name | str | 方案名称 |
| course_ids | JSONB | 课程 ID 列表 |
| total_credits | float | 总学分 |
| match_score | float | 匹配度 |
| notes | str | 备注 |
| created_at | datetime | 创建时间 |

**注意**: SavedPlan 中的 course_ids 在 session 模式下是课程名称而非 DB UUID，因为 session 课程没有持久化 ID。需在保存时转换为名称列表。

## 验证规则

### 核心字段校验
- name: 非空字符串，strip 后长度 > 0
- credit: 可转为 float，值 > 0

### 可选字段校验
- course_no: 非空时 strip
- instructor: 非空时 strip，去掉"教授"/"副教授"/"讲师"/"老师"等后缀
- schedule.day_of_week: 1-7
- schedule.start_period < schedule.end_period
- category: 非空时 strip

### 行级错误
- 核心字段缺失或格式错误 → 收集到 errors 列表，前端展示
- 可选字段格式错误 → 设为 None，不报错
