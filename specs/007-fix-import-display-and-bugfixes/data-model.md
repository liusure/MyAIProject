# Data Model: 导入显示优化及推荐和课程表bug修复

## Entities

### ImportConfirmResponse (现有，修改展示逻辑)

- `courses: list[dict]` — 后端仍然返回，前端不再展示
- `total: int` — 前端主要展示此字段
- `errors: list[ImportError]` — 有错误时前端展示此字段
- `degradation: DegradationReport` — 降级信息

**变更**: 无结构变更，仅前端展示逻辑变化。任何 errors 非空即视为整体失败。

### RecommendationPlan (现有，修复序列化)

- `plan_name: str`
- `courses: list[CourseResponse]`
- `total_credits: float`
- `match_score: float`
- `conflicts: list[ConflictItem]`

**变更**: SSE 流中序列化时需调用 `model_dump(mode='json')` 转换为 dict。

### SessionStore (扩展，新增 raw_data 存储)

现有字段:
- `_store: dict[str, list[SessionCourse]]` — 课程数据

新增字段:
- `_raw_data: dict[str, list[dict]]` — analyze 步骤存储的完整原始数据

新增方法:
- `set_raw_data(device_id, raw_data)` — 存储原始数据
- `get_raw_data(device_id)` — 获取原始数据

**变更**: analyze 时存储全部行，confirm 时从 session 读取（而非依赖前端传回的 3 行样本）。

## Relationships

```
analyze (upload) → SessionStore.set_raw_data(device_id, full_raw_data)
confirm → SessionStore.get_raw_data(device_id) → ImportParser.apply_mapping()
```
