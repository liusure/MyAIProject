---

description: "任务清单：Cookie 设备认证 + 周课程表视图"

---

# 任务：Cookie 设备认证 + 周课程表视图

**输入**：设计文档 `/specs/002-cookie-auth-timetable/`
**前置条件**：spec.md（必需）
**前置项目**：001-llm-course-select（已有的全栈应用）

**格式**：`[ID] [P?] [Story?] 文件路径描述`

- **[P]**：可并行执行（不同文件，无依赖）
- **[Story]**：所属用户故事（US1, US2）

> 本功能是对现有系统的修改，非新建项目。Phase 1/2（项目初始化和基础架构）已在 001-llm-course-select 中完成，此处直接从用户故事开始。

---

## Phase 1：用户故事 1 - Cookie 设备认证替代登录（优先级：P1）🎯

**目标**：移除 Session 登录机制，改为浏览器 Cookie 自动识别设备，所有功能无需登录即可使用。

**独立测试**：打开浏览器访问系统，无需任何登录操作即可直接使用对话推荐、课程导入等所有功能。

### 实现（用户故事 1）

- [X] T001 [US1] 重写认证中间件：将 `get_current_user` 改为 `get_or_create_device`，从 Cookie `device_id` 获取设备标识，首次访问自动创建 `device_id` Cookie（UUID，有效期 1 年），不再查询 Student 表或 Redis `backend/src/core/security.py`
- [X] T002 [US1] 重写设备标识逻辑：新增 `get_device_id(request, response)` 函数，优先从 Cookie 读取 `device_id`，不存在则生成 UUID 并 Set-Cookie `backend/src/core/security.py`
- [X] T003 [US1] 修改对话 API：将 `Depends(get_current_user)` 替换为 `Depends(get_or_create_device)`，`user.id` 改为 `device_id` 字符串，对话记录关联 `device_id` 而非 `student_id` `backend/src/api/conversation.py`
- [X] T004 [US1] 修改方案 API：将认证依赖替换为 `get_or_create_device`，方案按 `device_id` 关联 `backend/src/api/plan.py`
- [X] T005 [US1] 修改管理 API：移除 `require_admin` 校验，课程导入和规则配置接口允许任意设备访问 `backend/src/api/admin.py`
- [X] T006 [US1] 修改对话服务层：`ConversationService` 的 `create` 方法接收 `device_id: str` 而非 `student_id: UUID`，数据库查询按 `device_id` 过滤 `backend/src/services/conversation.py`
- [X] T007 [US1] 修改方案服务层：`PlanService` 的 `save`、`list_by_student`、`get`、`delete` 方法改为按 `device_id` 操作 `backend/src/services/plan_service.py`
- [X] T008 [US1] 修改审计服务层：`AuditService.log` 的 `user_id` 参数改为 `device_id` 字符串 `backend/src/services/audit.py`
- [X] T009 [US1] 修改数据模型：Conversation 和 SavedPlan 表新增 `device_id` 字段（String），替代或补充 `student_id` 外键 `backend/src/models/conversation.py`、`backend/src/models/saved_plan.py`
- [X] T010 [US1] 生成 Alembic 迁移脚本：添加 `device_id` 字段到 `conversations` 和 `saved_plans` 表 `backend/alembic/versions/`
- [X] T011 [P] [US1] 移除前端登录相关代码：删除 `login`、`logout` 函数，移除未使用的 `Student` 类型导出 `frontend/src/services/api.ts`
- [X] T012 [P] [US1] 移除后端登录端点：删除 `POST /auth/login` 和 `POST /auth/logout`，或将其替换为空操作 `backend/src/api/auth.py`
- [X] T013 [US1] 修改 SSE 流式端点：将认证依赖替换为 `get_or_create_device` `backend/src/api/conversation.py`
- [X] T014 [US1] 修改 CORS 配置：确保 `supports_credentials` 保持为 True（Cookie 跨域传递）`backend/src/main.py`

**检查点**：用户无需登录即可使用全部功能，Cookie 自动识别设备

---

## Phase 2：用户故事 2 - 周课程表视图（优先级：P2）

**目标**：在推荐结果中展示周一到周日的可视化课程表，直观呈现课程时间分布和冲突。

**独立测试**：获取推荐结果后，验证课程表正确展示每门课程在对应星期和时间段的位置。

### 实现（用户故事 2）

- [X] T015 [P] [US2] 重写 ScheduleView 组件：使用 CSS Grid 实现周一至周日 + 8:00-18:00 时间轴的课程表，每门课程显示名称和背景色，冲突课程红色高亮，不同课程用不同颜色区分，修复现有冲突检测 bug `frontend/src/components/ScheduleView/ScheduleView.tsx`
- [X] T016 [P] [US2] 为 ScheduleView 添加样式：表头、格子、课程块、冲突标记、颜色方案、移动端横向滚动 `frontend/src/components/ScheduleView/ScheduleView.css`
- [X] T017 [US2] 在 CourseSelect 页面集成 ScheduleView：在每个推荐方案卡片内嵌入课程表，传入该方案的课程列表和冲突列表 `frontend/src/pages/CourseSelect.tsx`
- [X] T018 [US2] 更新 App.css：为 `.schedule-view` 添加表格和课程块样式 `frontend/src/App.css`

**检查点**：推荐结果中展示课程表，课程正确按时间/星期定位，冲突高亮

---

## 依赖关系

- **Phase 1（US1）**：无依赖，可立即开始
- **Phase 2（US2）**：无强依赖，可与 Phase 1 并行开发（但需在 US1 修复后才能完整测试，因为修复前所有功能被登录阻塞）

### 并行机会

- T001-T010 为后端串行修改（同一认证链路）
- T011 和 T012 可并行（前端 + 后端不同文件）
- T015 和 T016 可并行（组件 + 样式不同文件）
- Phase 1 和 Phase 2 可并行开发

---

## 实施策略

### 最小可行修复（仅 Phase 1）

1. 修改 `security.py`：移除 Redis session 查询，改为 Cookie device_id
2. 修改 API 层：替换所有 `get_current_user` 为设备标识
3. 修改数据模型：添加 device_id 字段
4. **验证**：无需登录即可访问所有接口

### 增量交付

1. 完成 US1 → 验证无需登录 → 部署
2. 添加 US2 课程表 → 验证可视化 → 部署
