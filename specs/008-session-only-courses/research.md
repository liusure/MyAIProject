# Research: 课程数据仅存会话，推荐历史持久化

## Decision 1: 移除数据库课程回退

**Decision**: `RecommendService.recommend()` 不再查询 `courses` 表作为回退。当 `session_courses` 为空时，直接返回"请先上传课表文件"。

**Rationale**: spec FR-004/FR-005 明确要求不再从数据库获取课程。当前 `_get_active_courses()` 查询 `courses` 表的行为需要移除。

**Alternatives considered**:
- 保留数据库查询但标记为"旧数据"（增加复杂度，违反"每次都上传"的使用模式）
- 将 courses 表改为只读参考数据（需求不明确，过度设计）

## Decision 2: 推荐历史快照存储

**Decision**: 推荐方案中的课程信息通过现有 `Conversation.messages` JSONB 字段以快照形式持久化。`RecommendService._build_recommendation_plan()` 返回的 `RecommendationPlan` 已包含完整的 `CourseResponse` 列表（名称、学分、教师、schedule 等），这些数据随对话消息一起存入数据库。

**Rationale**: 现有架构已经将推荐结果存入 `Conversation.messages`（conversation.py line 77, 153）。只需确保 `RecommendationPlan` 中的 `courses` 字段包含完整快照（当前已包含），无需新建表或修改存储层。

**Alternatives considered**:
- 新建 `recommendation_history` 表（增加存储复杂度，与现有 conversation 存储重复）
- 使用 Redis 缓存历史（不持久化，不符合需求）

## Decision 3: courses 表保留但不再作为推荐来源

**Decision**: 保留 `courses` 表和 `Course` 模型不动，但移除 `RecommendService` 对它的读取。`CourseSearchService` 和 `PDFExportService` 如果仍需要可以保留，但本 feature 不涉及这些功能。

**Rationale**: 最小改动。删除 courses 表需要数据库迁移，且可能影响其他尚未迁移的功能。仅移除推荐服务的依赖即可。

**Alternatives considered**:
- 删除 courses 表及相关代码（破坏性变更，影响范围大）
- 将 courses 表用途改为"课程模板库"（需求不明确）

## Decision 4: SessionStore 的 device_id 问题

**Decision**: 当前调试发现 `session_courses=None`，根本原因是 uvicorn `--reload` 模式下 worker 进程重启导致内存 SessionStore 丢失。这不是架构问题，是开发环境问题。生产环境（无 --reload）不存在此问题。

**Rationale**: SessionStore 的设计是正确的（内存存储），需要确保生产环境和开发环境的行为一致。

**Alternatives considered**:
- 将 SessionStore 改为 Redis（增加依赖，session 数据量小不需要）
- 使用文件持久化（不必要，增加 I/O 开销）
