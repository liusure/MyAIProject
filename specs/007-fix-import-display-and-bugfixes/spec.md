# Feature Specification: 导入显示优化及推荐和课程表bug修复

**Feature Branch**: `[007-fix-import-display-and-bugfixes]`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "导入成功后展示成功条数即可，因为有任何一条失败都算失败，不需要展示所有导入的课程列表，没有意义。修复bug：现在使用推荐功能，返回"未找到匹配的课程方案，请尝试调整你的需求描述"。修复bug：未显示周课程表"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 导入结果简化展示 (Priority: P1)

用户上传 Excel 文件完成导入后，在结果页面只看到导入成功的条数。如果有任何一行数据导入失败，整个导入操作视为失败，展示失败信息而非成功条数。

**Why this priority**: 导入结果展示是用户每次导入都会看到的界面，当前展示完整课程列表没有实际意义，用户只需要知道"导入了多少条"或"哪里出错了"。

**Independent Test**: 上传一个包含 10 行数据的 Excel 文件，确认导入成功后只显示"成功导入 X 条"文字，不显示课程卡片列表。上传一个包含错误数据的文件，确认显示失败信息而非部分成功的数量。

**Acceptance Scenarios**:

1. **Given** 用户上传了一个有效的 Excel 文件，**When** 所有行均成功导入，**Then** 页面展示"成功导入 X 条"，不展示课程列表
2. **Given** 用户上传了一个包含无效数据的 Excel 文件，**When** 任何一行导入失败，**Then** 页面展示失败信息（包含行号和错误原因），不展示成功条数

---

### User Story 2 - 修复推荐功能返回空结果 (Priority: P1)

用户上传课程文件后，在智能选课页面输入选课偏好描述，系统应返回匹配的推荐方案，而非始终显示"未找到匹配的课程方案"。

**Why this priority**: 推荐功能是本应用的核心价值，当前完全不可用，属于阻断性 bug。

**Independent Test**: 上传包含课程数据的 Excel 文件，在对话框输入"推荐一些计算机相关课程"，确认返回至少一个包含课程列表的推荐方案。

**Acceptance Scenarios**:

1. **Given** 用户已上传课程文件且系统中有可用课程，**When** 用户输入选课偏好描述，**Then** 系统返回一个或多个推荐方案，每个方案包含课程列表和匹配度
2. **Given** 用户未上传任何课程文件，**When** 用户输入选课偏好描述，**Then** 系统提示"请先上传课表文件"

---

### User Story 3 - 修复周课程表不显示 (Priority: P1)

当推荐方案返回后，每个方案下方应显示该方案的周课程表视图，展示课程在一周中的时间分布。

**Why this priority**: 课程表视图是用户评估推荐方案的重要工具，没有课程表用户无法判断时间冲突。

**Independent Test**: 获取推荐方案后，确认每个方案下方出现课程表网格，且已安排时间的课程显示在正确的格子中。

**Acceptance Scenarios**:

1. **Given** 推荐方案中的课程包含 schedule 数据，**When** 推荐方案渲染完成，**Then** 方案下方显示周课程表，课程块出现在对应的时间格子中
2. **Given** 推荐方案中的课程不包含 schedule 数据，**When** 推荐方案渲染完成，**Then** 课程表区域显示"时间未指定"提示

---

### Edge Cases

- 导入的 Excel 文件有 0 行数据时如何处理？
- 推荐功能的 LLM 服务不可用时，如何优雅降级？
- 课程表有时间冲突时，冲突课程如何标记？

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 导入完成后，若所有行均成功，页面 MUST 只展示"成功导入 X 条"文字，不展示课程列表
- **FR-002**: 导入过程中，若任何一行失败，整体视为导入失败。页面 MUST 展示失败信息（行号+错误原因），不展示成功条数。已成功的行仍保留入库，不回滚。
- **FR-003**: 推荐功能 MUST 基于用户已上传的课程数据生成推荐方案，不得返回与实际可用课程不匹配的方案
- **FR-004**: 推荐方案返回后，每个方案下方 MUST 显示周课程表视图
- **FR-005**: 推荐方案数据 MUST 完整传递到前端，包含 plan_name、courses（含课程名称/学分/schedule）、total_credits、match_score、conflicts 字段

### Key Entities *(include if feature involves data)*

- **ImportConfirmResponse**: 导入结果，包含 total（总条数）、errors（失败列表）、courses（课程列表）
- **RecommendationPlan**: 推荐方案，包含 plan_name、courses、total_credits、match_score、conflicts
- **ScheduleSlot**: 课程时间槽，包含 day_of_week、start_period、end_period、weeks

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 导入成功后页面只显示一行成功条数文字，不再显示课程卡片列表
- **SC-002**: 上传课程文件后，推荐功能返回至少一个有效推荐方案的成功率 > 95%
- **SC-003**: 推荐方案返回后，课程表视图在 1 秒内完成渲染
- **SC-004**: 课程表中已安排时间的课程 100% 显示在正确的格子中

## Assumptions

- 用户的 Excel 文件包含系统可识别的课程名称和学分字段
- LLM 服务（MiMo API）在正常运行时可用
- 用户浏览器支持 SSE（Server-Sent Events）
- 课程表的展示范围为周一至周日、8:00-18:00
