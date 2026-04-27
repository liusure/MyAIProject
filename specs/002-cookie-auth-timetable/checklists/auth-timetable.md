# Requirements Quality Checklist: Cookie 认证 + 课程表视图

**Purpose**: 验证需求文档中认证迁移和课程表视图相关需求的完整性、清晰度和一致性
**Created**: 2026-04-22
**Feature**: [spec.md](../spec.md)

## Cookie 认证需求质量

- [ ] CHK001 - FR-001 中"移除所有登录/登出流程和界面"是否包含了对前端路由和导航栏的具体要求？[Completeness, Spec §FR-001]
- [ ] CHK002 - FR-002 中"有效期不少于 1 年"是否明确指定了 Cookie 的 SameSite、HttpOnly、Secure 属性要求？[Clarity, Spec §FR-002]
- [ ] CHK003 - FR-003 中"所有 API 端点"是否明确包含 SSE 流式端点 `/conversation/chat/stream` 和文件上传端点 `/admin/courses/import`？[Completeness, Spec §FR-003]
- [ ] CHK004 - 用户通过 Cookie device_id 识别后，原有的"管理员"角色权限校验如何处理？需求中未定义新角色模型。[Gap, Spec §FR-003]
- [ ] CHK005 - FR-004 中"移除登录页面和登录表单"与现有系统中无登录页面的事实是否一致？[Consistency, Spec §FR-004]
- [ ] CHK006 - 设备标识方案中，同一浏览器多个标签页是否被视为同一设备？Cookie 共享行为是否已定义？[Gap, Spec §FR-002]
- [ ] CHK007 - 用户清除 Cookie 后，旧 device_id 关联的数据（对话、方案）是否永久不可访问？需求中未定义数据恢复策略。[Gap, Edge Case]
- [ ] CHK008 - 隐身模式下 Cookie 丢失的处理策略是否与正常模式一致？[Coverage, Edge Case]
- [ ] CHK009 - 认证方式从 Session 迁移到 Cookie 后，原有数据库中的 `student_id` 外键数据如何处理？是否需要数据迁移？[Gap, Spec §FR-001]

## 课程表视图需求质量

- [ ] CHK010 - FR-006 中"8:00-18:00，按小时分段"是否定义了当课程跨多个时段（如 14:00-16:40）的显示方式？[Clarity, Spec §FR-006]
- [ ] CHK011 - FR-007 中"不同课程使用不同背景颜色区分"是否指定了颜色数量上限和颜色选择策略？[Clarity, Spec §FR-007]
- [ ] CHK012 - FR-008 中"时间冲突的课程"的冲突判定标准是什么？是重叠即冲突还是需完全相同时间段？[Ambiguity, Spec §FR-008]
- [ ] CHK013 - FR-009 中"每个推荐方案有独立的课程表"——当推荐方案数量超过 3 个时，多个课程表的页面布局如何处理？[Gap, Spec §FR-009]
- [ ] CHK014 - FR-010 中"可横向滚动"是否定义了最小可读宽度和滚动提示机制？[Clarity, Spec §FR-010]
- [ ] CHK015 - 课程表中是否需要显示课程地点（教室/校区）信息？当前需求仅提到显示课程名称。[Gap, Spec §FR-007]
- [ ] CHK016 - 课程表是否需要支持点击课程卡片查看详细信息的交互？[Gap]
- [ ] CHK017 - 周六和周日是否应该包含在课程表中？大学课程通常不在周末开课，展示空列是否有价值？[Assumption, Spec §FR-005]

## 成功标准质量

- [ ] CHK018 - SC-001 中"0 秒"是否过于绝对？Cookie 创建本身是否有可感知延迟？[Measurability, Spec §SC-001]
- [ ] CHK019 - SC-003 中"不超过 5 秒"的理解时间如何测量？是否有具体的用户测试方法？[Measurability, Spec §SC-003]
- [ ] CHK020 - SC-004 中"检测准确率和可视化标记准确率均为 100%"——是否定义了冲突检测的测试用例集？[Completeness, Spec §SC-004]

## 需求一致性

- [ ] CHK021 - 边缘场景中提到"用户清除 Cookie 后数据关联丢失"，但需求中未定义这是否为可接受的用户体验损失。[Consistency, Edge Case vs Requirements]
- [ ] CHK022 - 假设中提到"课程表展示仅针对推荐方案中的课程"，但需求中未排除学生已选课程，二者是否一致？[Consistency, Assumptions vs FR-005]
- [ ] CHK023 - FR-003 要求所有端点接受 Cookie，但 `/health` 端点是否也应包含在内？[Coverage, Spec §FR-003]

## 缺失需求

- [ ] CHK024 - 认证迁移过程中数据库 Schema 变更的回滚策略是否定义？[Gap, Recovery]
- [ ] CHK025 - 课程表在不同浏览器和设备上的兼容性要求是否明确？[Gap, Non-Functional]
- [ ] CHK026 - 设备标识 Cookie 的跨域共享策略（前端 5173 端口 vs 后端 8000 端口）是否在需求中体现？[Gap, Spec §FR-002]
