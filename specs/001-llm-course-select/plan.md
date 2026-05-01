# 实施计划：LLM 自动选课系统

**功能分支**：`001-llm-course-select` | **日期**：2026-04-22 | **规格**：[spec.md](spec.md)
**输入**：功能规格 `/specs/001-llm-course-select/spec.md`

## 摘要

本系统是一个 AI 驱动的智能选课推荐平台，学生通过自然语言描述选课偏好，系统利用 LLM（MiMo API）理解意图，结合课程数据和选课规则自动推荐课程方案，检测冲突，并支持方案收藏和导出。**系统不执行真实选课操作**，实际选课由学生在学校系统中完成。技术栈：FastAPI + React + PostgreSQL + MiMo API。

## 技术上下文

**语言/版本**：Python 3.12（后端）、TypeScript 5.x（前端）
**主要依赖**：FastAPI、SQLAlchemy 2.x、Alembic、React 18、Vite、MiMo SDK、客户端 TXT 导出
**存储**：PostgreSQL 16
**测试**：pytest（后端）、Jest + React Testing Library（前端）
**目标平台**：Linux 服务器（后端部署）、现代浏览器（前端）
**项目类型**：全栈 Web 应用（web-service + web-frontend）
**性能目标**：100 并发用户，LLM P95 < 5s，首屏 < 1.5s，冲突检测 < 500ms
**约束**：选课高峰期 99.9% 可用性，HTTPS 传输加密，LLM 对话匿名化，单用户内存 < 200MB
**规模/范围**：预计 1000+ 学生用户，500+ 课程，选课高峰期 100 并发

## 宪法检查

*门禁：Phase 0 研究前必须通过。Phase 1 设计后重新检查。*

### 一、代码质量标准 ✅
- **类型安全**：Python 3.12 全量 Type Hints + mypy 检查；TypeScript strict 模式
- **文档**：FastAPI 自动生成 OpenAPI 文档 + Google 风格 Docstring
- **模块化**：后端四层架构（models → services → api → schemas）；前端组件分层

### 二、测试标准 ✅
- **单元测试**：pytest 覆盖 ≥ 85%，Jest 覆盖核心组件
- **集成测试**：MiMo API 使用 Mock/沙箱，PostgreSQL 使用测试容器 + 事务回滚
- **性能测试**：Locust 压测 100 并发

### 三、用户体验一致性 ✅
- **响应式**：React 加载 spinner + "加载中"提示、错误边界、推荐结果状态可视化
- **对话式**：SSE 流式输出 + JSON 结构化响应，对话历史持久化至 PostgreSQL
- **无障碍**：遵循 WCAG 2.1 AA，键盘导航支持
- **UI 美观性**：主色调蓝色系 (#1a73e8)、圆角卡片 (border-radius ≥ 8px)、悬停动画 (transition 200-300ms)

### 四、性能要求 ✅
- **响应时间**：React 代码分割 + 懒加载，FastAPI 异步处理
- **资源效率**：Redis 缓存 LLM 重复查询，PostgreSQL 索引全覆盖
- **可扩展性**：FastAPI 无状态设计，水平扩展；LLM 提供商策略模式可插拔

**结论**：无违反项，所有原则均可满足。

## 项目结构

### 文档（本功能）

```text
specs/001-llm-course-select/
├── plan.md              # 本文件
├── research.md          # Phase 0 产出
├── data-model.md        # Phase 1 产出
├── quickstart.md        # Phase 1 产出
├── contracts/           # Phase 1 产出
│   └── openapi.yaml     # API 接口契约
└── tasks.md             # Phase 2 产出（由 /speckit.tasks 生成）
```

### 源代码（仓库根目录）

```text
backend/
├── src/
│   ├── api/                  # FastAPI 路由层
│   │   ├── __init__.py
│   │   ├── courses.py        # 课程搜索端点
│   │   ├── plan.py           # 方案收藏/导出端点
│   │   ├── conversation.py   # 对话/LLM 相关端点
│   │   └── admin.py          # 教务管理端点
│   ├── services/             # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── llm/              # LLM 集成
│   │   │   ├── base.py       # 提供商抽象基类
│   │   │   ├── mimo.py       # MiMo API 集成
│   │   │   ├── factory.py    # 提供商工厂
│   │   │   └── fallback.py   # 降级策略
│   │   ├── recommend.py      # 选课推荐算法
│   │   ├── conflict/         # 冲突检测引擎
│   │   │   ├── time.py       # 时间冲突
│   │   │   ├── prerequisite.py  # 先修冲突
│   │   │   ├── commute.py    # 通勤冲突
│   │   │   └── engine.py     # 引擎入口
│   │   ├── plan_service.py   # 方案收藏/导出
│   │   ├── course_search.py  # 课程搜索（降级方案）
│   │   ├── import_parser.py  # CSV/Excel 解析
│   │   ├── course_import.py  # 课程导入业务逻辑
│   │   ├── rule_service.py   # 选课规则 CRUD
│   │   ├── rule_validator.py # 规则校验
│   │   ├── conversation.py   # 对话业务逻辑
│   │   ├── audit.py          # 操作日志
│   ├── models/               # 数据层（SQLAlchemy ORM）
│   │   ├── __init__.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── prerequisite.py
│   │   ├── saved_plan.py
│   │   ├── selection_rule.py
│   │   ├── conversation.py
│   │   └── audit_log.py
│   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── course.py
│   │   ├── plan.py
│   │   └── conversation.py
│   ├── core/                 # 核心配置
│   │   ├── config.py         # 应用配置
│   │   ├── database.py       # 数据库连接
│   │   └── security.py       # Session-based 认证
│   └── main.py               # FastAPI 入口
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── performance/

frontend/
├── src/
│   ├── components/           # UI 组件
│   │   ├── ChatPanel/        # 对话面板
│   │   ├── ScheduleView/     # 时间表视图
│   │   ├── CourseCard/       # 课程卡片
│   │   ├── ConflictBadge/    # 冲突标记
│   │   └── PlanExporter/     # 方案导出
│   ├── pages/                # 页面
│   │   ├── Home.tsx
│   │   ├── CourseSelect.tsx
│   │   ├── MyPlans.tsx       # 我的方案
│   │   └── Admin.tsx
│   ├── services/             # API 调用
│   │   └── api.ts
│   ├── hooks/                # 自定义 Hooks
│   └── types/                # TypeScript 类型定义
└── tests/

docs/
├── README.md
└── ARCHITECTURE.md
```

**结构决策**：采用全栈 Web 应用结构（后端 FastAPI + 前端 React），前后端分离部署。后端严格四层分离（models → services → api → schemas），前端组件化设计。

## 复杂性追踪

> **仅在宪法检查有违反项时填写**

无违反项，无需填写。
