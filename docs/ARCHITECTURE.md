# 架构文档：LLM 自动选课系统

## 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI    │────▶│ PostgreSQL  │
│   前端      │     │   后端       │     │  数据库     │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │    Redis     │
                    │ Session+缓存 │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │  MiMo API    │
                    │  LLM 服务    │
                    └──────────────┘
```

## 后端分层架构

```
src/
├── api/          # 路由层：HTTP 请求处理
├── services/     # 业务逻辑层：核心业务规则
│   ├── llm/      #   LLM 集成（策略模式）
│   └── conflict/ #   冲突检测引擎
├── models/       # 数据层：SQLAlchemy ORM 模型
├── schemas/      # 序列化层：Pydantic 请求/响应
└── core/         # 核心配置：数据库、Redis、安全
```

## 关键设计决策

### LLM 提供商策略模式
- 抽象基类 `LLMProvider`，实现 `MiMoProvider`
- 工厂模式 `LLMFactory` 支持多提供商切换
- `FallbackLLMProvider` 提供降级方案（关键词搜索）

### 冲突检测引擎
- 模块化设计：`time.py`、`prerequisite.py`、`commute.py`
- 统一入口 `ConflictEngine` 聚合所有检测器
- 支持扩展新的冲突类型

### Session-based 认证
- Redis 存储 Session，HTTP-only Cookie 传递
- 支持学生和管理员双角色

## 数据库实体

- **Student**：学生/管理员（含 role 和 password_hash）
- **Course**：课程（JSONB schedule 支持多时段）
- **Prerequisite**：先修关系（有向图）
- **SavedPlan**：收藏方案（JSONB course_ids）
- **SelectionRule**：选课规则
- **Conversation**：对话记录（JSONB messages）
- **AuditLog**：操作日志
