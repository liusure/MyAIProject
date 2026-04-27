# Research: Multi-Step Course Recommendation

## Decision 1: 学科提取策略

**Decision**: 从 SessionCourse 列表中提取所有唯一的 `category`（所属学科）值，去重后排序，作为第一步发送给 LLM 的多选题选项。

**Rationale**:
- `category` 字段已在现有的 `_format_session_courses_for_llm` 中被使用，数据可直接从 `SessionCourse.category` 获取
- 去重后的学科列表通常不超过 50 个，token 量极小（<1% 原始数据），满足 SC-001
- LLM 做多选题（从给定列表中选）比自由生成学科名称更可靠，确保返回值精确匹配

**Alternatives considered**:
- 让 LLM 自由生成学科名称后模糊匹配：不可靠，可能返回不存在的学科
- 使用学科代码而非名称：当前数据模型无学科代码字段

## Decision 2: 两步 LLM 调用的 Schema 设计

**Decision**: 第一步使用独立的简化 schema（仅返回学科列表），第二步使用现有的 `RECOMMENDATION_SCHEMA`（返回推荐方案）。

**Rationale**:
- 第一步不需要推荐方案，只需要学科过滤结果，简化 schema 减少 token 消耗和出错概率
- 第二步复用现有 schema 保持兼容性，`_build_recommendation_plan` 等后处理逻辑不变
- 两步 schema 分离使每步的 prompt 更专注，降低 LLM 混淆风险

**Alternatives considered**:
- 用一个 schema 同时返回学科和推荐方案：增加了单步复杂度，违背分步减负的初衷
- 两步都用同一个 schema：第一步不需要推荐方案字段，浪费 token

## Decision 3: 非敏感字段格式化

**Decision**: 第二步发送给 LLM 的课程信息格式化为：`- 序号 | 课程名 | N学分 | 教师 | 周X HH:MM-HH:MM | 地点`，不含 `id`、`capacity`、`campus`、`semester` 等敏感/冗余字段。

**Rationale**:
- `id` 是内部 UUID，对 LLM 无意义，序号（course_no）足以做本地回查
- `capacity`、`campus`、`semester` 属于内部管理数据，符合 FR-004 非敏感要求
- `credit`（学分）经 clarification 确认为非敏感字段，保留
- 格式与现有 `_format_session_courses_for_llm` 一致，减少变更量

**Alternatives considered**:
- 完全不发送任何 ID：LLM 无法引用具体课程，需要序号做标识
- 发送完整字段：违反 FR-004 非敏感信息限制

## Decision 4: 学科过滤回退策略

**Decision**: 以下情况回退到不过滤学科（使用全部课程）：
1. 所有课程的 `category` 为空或全部相同（无过滤价值）
2. LLM 返回的学科列表为空（用户需求不匹配任何学科）
3. LLM 调用失败（ContentFilteredError 或其他异常）

**Rationale**:
- 符合 FR-006 "学科过滤无结果时回退到使用全部课程数据"
- 符合 FR-008 "LLM 调用失败时提供降级方案"
- 保证系统鲁棒性：任何第一步异常都不阻断推荐流程

**Alternatives considered**:
- 学科过滤失败直接返回错误：用户体验差，不满足 FR-006
- 仅在 LLM 调用失败时回退：忽略了"无匹配学科"的正常场景

## Decision 5: 第二步无匹配结果处理

**Decision**: 第二步 LLM 返回空推荐列表时，直接返回"无匹配课程"提示给用户，不做额外降级。

**Rationale**:
- 经 clarification 确认（Question 2 Answer A）
- 第二步在已缩减的数据集上运行，无匹配说明需求确实无法满足
- 强行降级到关键词搜索反而可能返回不相关结果

**Alternatives considered**:
- 回退到学科过滤后的全部课程用关键词搜索：可能返回不相关内容
- 回退到原始全部课程：违背数据缩减目标
