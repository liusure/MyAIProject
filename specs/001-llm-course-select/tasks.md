---

description: "任务清单：LLM 自动选课推荐系统功能实现（后澄清版本）"

---

# 任务：LLM 自动选课推荐系统

**输入**：设计文档 `/specs/001-llm-course-select/`
**前置条件**：plan.md（必需）、spec.md（必需）、data-model.md、contracts/openapi.yaml

**测试**：本任务包含测试任务，遵循宪法「测试标准」原则。

**格式**：`[ID] [P?] [Story?] 文件路径描述`

- **[P]**：可并行执行（不同文件，无依赖）
- **[Story]**：所属用户故事（US1, US2, US3, US4）

> **注意**：系统不执行真实选课操作。实际选课由学生在学校系统中自行完成。系统仅提供推荐、冲突检测、方案收藏与导出功能。

---

## Phase 1：项目初始化（Setup）

**目的**：项目基础结构和工具链配置

- [X] T001 创建项目目录结构（backend/ + frontend/ + docs/）per plan.md
- [X] T002 [P] 初始化 Python 项目：创建 pyproject.toml，配置 FastAPI、SQLAlchemy、Alembic、pytest、redis、weasyprint、pandas、openpyxl 依赖
- [X] T003 [P] 初始化 React 项目：使用 Vite + TypeScript 创建 frontend/，安装 React 18、TypeScript 依赖
- [X] T004 [P] 配置后端开发工具：ruff（lint + format）、mypy（类型检查）
- [X] T005 [P] 配置前端开发工具：ESLint、Prettier、TypeScript strict 模式
- [X] T006 [P] 配置 Docker Compose：PostgreSQL 16 + Redis 7 服务
- [X] T007 创建 .env.example 文件，定义环境变量模板（DATABASE_URL、REDIS_URL、MIMO_API_KEY 等）

---

## Phase 2：基础架构（Foundational）

**目的**：所有用户故事的阻塞前置条件

**⚠️ 关键**：在任何用户故事开始前，本阶段必须全部完成

- [X] T008 创建 SQLAlchemy 数据库连接配置 `backend/src/core/database.py`
- [X] T009 创建 FastAPI 应用配置 `backend/src/core/config.py`（Pydantic Settings）
- [X] T010 创建 Redis 连接配置 `backend/src/core/redis.py`（Session 存储 + LLM 缓存）
- [X] T011 创建 Student 数据模型 `backend/src/models/student.py`（含 role 字段和 password_hash）
- [X] T012 创建 Course 数据模型 `backend/src/models/course.py`（含 JSONB schedule 字段）
- [X] T013 创建 Prerequisite 数据模型 `backend/src/models/prerequisite.py`
- [X] T014 创建 SavedPlan 数据模型 `backend/src/models/saved_plan.py`（含 JSONB course_ids）
- [X] T015 创建 SelectionRule 数据模型 `backend/src/models/selection_rule.py`
- [X] T016 创建 Conversation 数据模型 `backend/src/models/conversation.py`
- [X] T017 创建 AuditLog 数据模型 `backend/src/models/audit_log.py`
- [X] T018 配置 Alembic 迁移，生成初始数据库迁移脚本
- [X] T019 [P] 创建 Pydantic Schema：Course 相关 `backend/src/schemas/course.py`
- [X] T020 [P] 创建 Pydantic Schema：Plan 相关 `backend/src/schemas/plan.py`
- [X] T021 [P] 创建 Pydantic Schema：Conversation 相关 `backend/src/schemas/conversation.py`
- [X] T022 实现 Session-based 认证中间件 `backend/src/core/security.py`（依赖 Redis）
- [X] T023 创建认证 API 端点（登录/登出）`backend/src/api/auth.py`
- [X] T024 创建 FastAPI 入口 `backend/src/main.py`，注册路由和 Session 中间件
- [X] T025 [P] 创建前端 API 服务层 `frontend/src/services/api.ts`
- [X] T026 [P] 创建前端 TypeScript 类型定义 `frontend/src/types/`（Course、SavedPlan、Conversation 等）
- [X] T027 创建前端路由和页面骨架（Home、CourseSelect、MyPlans、Admin）

**检查点**：基础架构就绪，用户故事可并行开发

---

## Phase 3：用户故事 1 - 自然语言选课推荐（优先级：P1）🎯 MVP

**目标**：学生通过自然语言描述选课偏好，系统返回推荐课程方案

**独立测试**：输入"我想选周三下午的计算机课程"，验证系统返回至少 3 个匹配方案

### 测试（用户故事 1）

- [X] T028 [P] [US1] LLM 服务 Mock 测试 `backend/tests/unit/test_llm_service.py`
- [X] T029 [P] [US1] 推荐算法单元测试 `backend/tests/unit/test_recommend.py`
- [X] T030 [P] [US1] 对话 API 契约测试 `backend/tests/contract/test_conversation_api.py`

### 实现（用户故事 1）

- [X] T031 [US1] 实现 LLM 提供商抽象基类 `backend/src/services/llm/base.py`
- [X] T032 [US1] 实现 MiMo API 集成 `backend/src/services/llm/mimo.py`（JSON 结构化输出）
- [X] T033 [US1] 实现 LLM 提供商工厂（支持 MiMo/OpenAI/Claude 切换）`backend/src/services/llm/factory.py`
- [X] T034 [US1] 实现 LLM 降级策略：LLM 不可用时切换关键词搜索 `backend/src/services/llm/fallback.py`
- [X] T035 [US1] 实现推荐引擎：解析 LLM JSON 输出 + 匹配课程 `backend/src/services/recommend.py`
- [X] T036 [US1] 实现对话业务逻辑：对话创建、消息追加、上下文管理 `backend/src/services/conversation.py`
- [X] T037 [US1] 实现课程搜索服务（降级方案）`backend/src/services/course_search.py`
- [X] T038 [US1] 实现对话 API 端点 POST /conversation/chat `backend/src/api/conversation.py`
- [X] T039 [US1] 实现课程搜索 API 端点 GET /courses/search `backend/src/api/courses.py`
- [X] T040 [US1] 实现操作日志记录服务 `backend/src/services/audit.py`
- [X] T041 [US1] 实现 LLM 响应缓存（Redis，相似需求复用结果）`backend/src/services/llm/cache.py`
- [X] T042 [US1] 创建前端对话面板组件 `frontend/src/components/ChatPanel/`
- [X] T043 [US1] 创建前端课程卡片组件 `frontend/src/components/CourseCard/`
- [X] T044 [US1] 实现选课推荐页面（对话 + 推荐结果展示）`frontend/src/pages/CourseSelect.tsx`
- [X] T045 [US1] 实现 SSE 流式输出对接（前端接收 LLM 流式响应）

**检查点**：用户故事 1 应完全可独立运行和测试

---

## Phase 4：用户故事 2 - 课程时间冲突检测（优先级：P1）

**目标**：系统自动检测推荐课程的时间、地点和先修课程冲突

**独立测试**：选择一组包含已知冲突的课程，验证系统正确标出所有冲突

### 测试（用户故事 2）

- [X] T046 [P] [US2] 冲突检测引擎单元测试 `backend/tests/unit/test_conflict.py`（时间重叠、先修不满足、通勤不足）
- [X] T047 [P] [US2] 冲突检测集成测试 `backend/tests/integration/test_conflict_detection.py`

### 实现（用户故事 2）

- [X] T048 [US2] 实现时间冲突检测（时间区间重叠算法）`backend/src/services/conflict/time.py`
- [X] T049 [US2] 实现先修课程冲突检测（有向图检测）`backend/src/services/conflict/prerequisite.py`
- [X] T050 [US2] 实现通勤冲突检测（校区距离 + 时间间隔）`backend/src/services/conflict/commute.py`
- [X] T051 [US2] 实现冲突检测引擎入口 `backend/src/services/conflict/engine.py`
- [X] T052 [US2] 将冲突检测集成到推荐引擎 `backend/src/services/recommend.py`（修改已有文件）
- [X] T053 [US2] 创建前端冲突标记组件 `frontend/src/components/ConflictBadge/`
- [X] T054 [US2] 创建前端时间表可视化组件 `frontend/src/components/ScheduleView/`
- [X] T055 [US2] 在选课页面集成冲突展示（修改 CourseSelect.tsx）

**检查点**：用户故事 1 + 2 联合可独立运行和测试

---

## Phase 5：用户故事 3 - 方案收藏与导出（优先级：P2）

**目标**：学生收藏推荐方案并导出为 PDF，以便在学校选课系统开放时快速对照

**独立测试**：收藏一个方案验证持久化，导出 PDF 验证内容完整性

### 测试（用户故事 3）

- [X] T056 [P] [US3] 方案服务单元测试 `backend/tests/unit/test_plan_service.py`
- [X] T057 [P] [US3] PDF 导出单元测试 `backend/tests/unit/test_pdf_export.py`

### 实现（用户故事 3）

- [X] T058 [US3] 实现方案收藏业务逻辑：保存、查询、删除 `backend/src/services/plan_service.py`
- [X] T059 [US3] 实现 PDF 导出服务 `backend/src/services/pdf_export.py`（WeasyPrint HTML→PDF）
- [X] T060 [US3] 创建 PDF 导出 HTML 模板 `backend/src/templates/plan_export.html`
- [X] T061 [US3] 实现方案 API 端点 POST /plans（收藏）`backend/src/api/plan.py`
- [X] T062 [US3] 实现方案 API 端点 GET /plans（列表）`backend/src/api/plan.py`（修改已有文件）
- [X] T063 [US3] 实现方案 API 端点 DELETE /plans/{plan_id} `backend/src/api/plan.py`（修改已有文件）
- [X] T064 [US3] 实现方案 API 端点 GET /plans/{plan_id}/export（PDF 下载）`backend/src/api/plan.py`（修改已有文件）
- [X] T065 [US3] 创建前端方案导出组件 `frontend/src/components/PlanExporter/`
- [X] T066 [US3] 创建前端"我的方案"页面 `frontend/src/pages/MyPlans.tsx`（列表 + 导出 + 删除）
- [X] T067 [US3] 在推荐结果中添加"收藏方案"按钮（修改 CourseSelect.tsx）

**检查点**：用户故事 1 + 2 + 3 联合可独立运行和测试

---

## Phase 6：用户故事 4 - 教务数据导入与规则配置（优先级：P3）

**目标**：教务管理员批量导入课程数据（CSV/Excel）并配置选课规则

**独立测试**：上传 CSV/Excel 课程文件，验证系统自动识别格式并正确解析

### 测试（用户故事 4）

- [X] T068 [P] [US4] 课程导入服务单元测试 `backend/tests/unit/test_import_service.py`
- [X] T069 [P] [US4] 选课规则服务单元测试 `backend/tests/unit/test_rule_service.py`

### 实现（用户故事 4）

- [X] T070 [US4] 实现 CSV/Excel 课程数据解析器（自动识别格式）`backend/src/services/import_parser.py`
- [X] T071 [US4] 实现课程导入业务逻辑（批量插入、错误收集）`backend/src/services/course_import.py`
- [X] T072 [US4] 实现选课规则 CRUD 服务 `backend/src/services/rule_service.py`
- [X] T073 [US4] 实现选课规则校验服务（学分上限、选课时段）`backend/src/services/rule_validator.py`
- [X] T074 [US4] 实现管理端点 POST /admin/courses/import `backend/src/api/admin.py`
- [X] T075 [US4] 实现管理端点 POST /admin/rules `backend/src/api/admin.py`（修改已有文件）
- [X] T076 [US4] 创建前端管理页面 `frontend/src/pages/Admin.tsx`（课程导入 + 规则配置）

**检查点**：所有用户故事应完全可独立运行和测试

---

## Phase 7：收尾与横切关注点

**目的**：影响多个用户故事的改进

- [X] T077 [P] 编写项目文档 docs/README.md
- [X] T078 [P] 编写架构文档 docs/ARCHITECTURE.md
- [X] T079 [P] 实现 Alembic 数据库迁移脚本（含所有实体和索引）
- [X] T080 后端性能测试：使用 Locust 压测 100 并发 `backend/tests/performance/`
- [X] T081 前端无障碍审计：验证 WCAG 2.1 AA 合规
- [X] T082 安全审查：Session 安全、API Key 环境变量化、数据加密、SQL 注入防护
- [X] T083 运行 quickstart.md 验证全流程

---

## Phase 8：UI 美观性增强（NFR-04/05/06, FR-08a, FR-05a）

**目的**：落实澄清阶段新增的前端 UI 要求

- [X] T084 [P] 创建全局 CSS 主题变量 `frontend/src/styles/theme.css`（主色调 #1a73e8、圆角 8px、动画时长 250ms）
- [X] T085 [P] [US1] 为 ChatPanel 组件添加加载 spinner 和"加载中"提示，空结果展示"无结果" `frontend/src/components/ChatPanel/ChatPanel.tsx`
- [X] T086 [P] [US1] 为 CourseCard 组件应用圆角卡片样式和悬停动画 `frontend/src/components/CourseCard/CourseCard.tsx`
- [X] T087 [P] [US2] 为 ConflictBadge 组件应用主题色和圆角样式 `frontend/src/components/ConflictBadge/ConflictBadge.tsx`
- [X] T088 [P] [US3] 为 MyPlans 页面添加分页展示（按时间倒序）`frontend/src/pages/MyPlans.tsx`
- [X] T089 [P] [US3] 为 PlanExporter 和方案卡片应用圆角和悬停动画 `frontend/src/components/PlanExporter/PlanExporter.tsx`
- [X] T090 [US1] 更新推荐引擎：不足 3 个方案时仅展示实际匹配结果，不强制补齐 `backend/src/services/recommend.py`

---

## 依赖关系与执行顺序

### 阶段依赖

- **Phase 1（Setup）**：无依赖，可立即开始
- **Phase 2（Foundational）**：依赖 Phase 1 完成 — 阻塞所有用户故事
- **Phase 3-6（用户故事）**：全部依赖 Phase 2 完成
  - 用户故事可按优先级顺序开发（P1 → P2 → P3）
  - 或按团队并行开发
- **Phase 7（收尾）**：依赖所有期望的用户故事完成

### 用户故事依赖

- **US1（自然语言推荐）**：Phase 2 完成后即可开始 — 无其他故事依赖
- **US2（冲突检测）**：Phase 2 完成后即可开始 — 与 US1 集成但可独立测试
- **US3（方案收藏导出）**：依赖 US1 的推荐方案数据流 — 需要 US1 的 RecommendationPlan 结构
- **US4（教务导入）**：Phase 2 完成后即可开始 — 无其他故事依赖（但其数据供 US1/US2 使用）

### 阶段内依赖

- 测试必须先写且失败后才开始实现
- Models → Services → API → 前端组件
- 核心实现 → 集成
- 故事完成后再进入下一个优先级

### 并行机会

- Phase 1 中所有标记 [P] 的任务可并行执行
- Phase 2 中所有标记 [P] 的 Schema/类型定义任务可并行执行
- Phase 3 中所有标记 [P] 的测试任务可并行执行
- US1 和 US2 可由不同开发者并行开发
- US4 可与 US1/US2 并行开发
- Phase 7 中所有标记 [P] 的文档任务可并行执行

---

## 并行示例：用户故事 1

```bash
# 并行启动所有 US1 测试：
Task: "LLM 服务 Mock 测试 backend/tests/unit/test_llm_service.py"
Task: "推荐算法单元测试 backend/tests/unit/test_recommend.py"
Task: "对话 API 契约测试 backend/tests/contract/test_conversation_api.py"

# 并行启动前端组件：
Task: "创建对话面板组件 frontend/src/components/ChatPanel/"
Task: "创建课程卡片组件 frontend/src/components/CourseCard/"
```

---

## 实施策略

### MVP 优先（仅用户故事 1）

1. 完成 Phase 1：项目初始化
2. 完成 Phase 2：基础架构（关键 — 阻塞所有故事）
3. 完成 Phase 3：用户故事 1
4. **停止并验证**：独立测试用户故事 1
5. 部署/演示

### 增量交付

1. 完成 Setup + Foundational → 基础就绪
2. 添加 US1 → 独立测试 → 部署/演示（MVP!）
3. 添加 US2 → 独立测试 → 部署/演示
4. 添加 US3 → 独立测试 → 部署/演示
5. 添加 US4 → 独立测试 → 部署/演示
6. 每个故事增加价值而不破坏已有故事

### 并行团队策略

多名开发者：
1. 团队共同完成 Setup + Foundational
2. Foundational 完成后：
   - 开发者 A：US1（自然语言推荐）
   - 开发者 B：US2（冲突检测）
   - 开发者 C：US4（教务导入）
3. US1 + US2 完成后：
   - 任意开发者：US3（方案收藏导出）
4. 故事独立完成并集成

---

## 注意事项

- [P] 任务 = 不同文件，无依赖
- [Story] 标签将任务映射到特定用户故事以实现可追溯性
- 每个用户故事应可独立完成和测试
- 验证测试失败后才开始实现
- 每个任务或逻辑组完成后提交
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同文件冲突、破坏独立性的跨故事依赖
