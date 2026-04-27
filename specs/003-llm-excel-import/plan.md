# Implementation Plan: 学生课表智能导入与推荐

**Branch**: `003-llm-excel-import` | **Date**: 2026-04-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-llm-excel-import/spec.md`

## Summary

学生在选课页面上传任意格式的 Excel 课表文件，系统通过 LLM 智能识别列名映射（仅发送表头+样本行节省 token），通过算法处理确定性字段（日期、人名），对缺失字段优雅降级。课程数据保存在会话内存中不持久化，推荐结果附带可视化课表和冲突检测。项目本质是对现有 LLM 选课系统的 UX 增强。

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.x
**Primary Dependencies**: FastAPI, SQLAlchemy async, pandas/openpyxl (Excel), React 18, Vite
**Storage**: PostgreSQL（对话、方案等持久化数据）。课程数据为会话内存，不存 DB。
**Testing**: pytest（后端），手动浏览器测试（前端）
**Target Platform**: Web（localhost 开发 / Linux 部署）
**Project Type**: Web Application（前后端分离）
**Performance Goals**: Excel 解析 < 30s，LLM 列映射 token < 500，推荐响应 < 5s
**Constraints**: LLM 调用需有降级方案，不发送完整文件给 LLM，会话结束清除课程数据
**Scale/Scope**: 单用户场景，Excel ≤ 5MB / 2000 行，课程 ≤ 200 门/次

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| 类型安全优先 | ✅ | 所有新函数使用 Type Hints，Pydantic 模型 |
| 模块化设计 | ✅ | 新增独立服务层（ImportAnalyzer, SessionStore），不破坏现有分层 |
| 测试覆盖率 | ⚠️ | 后端核心逻辑需 ≥ 85% 覆盖率，LLM 调用需 Mock |
| LLM 集成规范 | ✅ | 列映射有固定格式回退方案，分类推断失败标记"未知" |
| 响应式交互 | ✅ | 上传过程有加载状态，解析结果有预览确认 |
| 性能要求 | ✅ | 首屏 < 1.5s，LLM 首字符 < 1s，冲突检测 < 500ms |
| 数据隐私 | ✅ | 课程数据不持久化，会话结束自动清除 |

## Project Structure

### Documentation (this feature)

```text
specs/003-llm-excel-import/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── import-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/src/
├── models/              # 现有（Course 模型保留用于 SavedPlan 引用）
├── schemas/
│   ├── course.py        # 修改：新增 SessionCourse schema
│   └── import_result.py # 新增：导入结果 schema
├── services/
│   ├── import_parser.py       # 重写：LLM 列映射 + 算法预处理
│   ├── import_analyzer.py     # 新增：LLM 列映射分析
│   ├── field_normalizer.py    # 新增：日期/人名算法标准化
│   ├── session_store.py       # 新增：会话课程内存存储
│   ├── recommend.py           # 修改：支持从会话内存获取课程
│   └── conflict/              # 现有：需接入推荐流程
├── api/
│   ├── admin.py         # 修改：导入端点改为学生可见
│   └── conversation.py  # 修改：推荐时使用会话课程数据

frontend/src/
├── pages/
│   ├── CourseSelect.tsx       # 修改：增加上传入口 + 课表展示
│   └── Home.tsx               # 修改：引导学生上传课表
├── components/
│   ├── FileUpload/            # 新增：文件上传组件
│   │   ├── FileUpload.tsx
│   │   └── FileUpload.css
│   ├── ColumnMappingPreview/  # 新增：列映射预览组件
│   │   ├── ColumnMappingPreview.tsx
│   │   └── ColumnMappingPreview.css
│   ├── ScheduleView/          # 现有：增强降级提示
│   └── CourseCard/            # 现有
├── services/
│   └── api.ts                 # 修改：新增上传和解析 API
├── types/
│   └── index.ts               # 修改：新增导入相关类型
```

**Structure Decision**: 使用现有的 Web Application 结构（backend/ + frontend/），新增文件遵循现有目录约定。

## Architecture Changes

### 当前架构（DB 中心）
```
Admin上传Excel → ImportParser(固定列名) → Course表(DB) → RecommendService(DB查询) → 显示
```

### 新架构（会话内存）
```
学生上传Excel → ImportAnalyzer(LLM列映射) → FieldNormalizer(算法标准化)
    → SessionStore(内存) → RecommendService(内存数据) → 冲突检测 → 课表可视化 → 显示
```

### 核心变更点

1. **ImportParser 重写**：不再要求固定列名。先检查列名是否完全匹配（快速路径），不匹配时走 LLM 列映射。
2. **新增 SessionStore**：以 device_id 为 key，在内存 dict 中存储当次上传的课程列表。会话结束或新上传时清除。
3. **RecommendService 修改**：优先从 SessionStore 获取课程，无数据时提示"请先上传课表"。
4. **冲突检测接入**：将 conflict/ 引擎接入推荐流程，不再返回空 conflicts。
5. **前端上传入口**：在 CourseSelect 页面顶部增加上传区域，不再局限于 Admin 页面。

## Complexity Tracking

| 复杂点 | 原因 | 更简单方案被拒原因 |
|--------|------|-------------------|
| 会话内存存储替代 DB | 用户澄清课程数据不持久化 | 直接用 DB 会导致不同用户数据混合 |
| LLM + 算法混合处理 | 节省 token，确定性字段不需要 LLM | 全走 LLM 成本高且慢 |
| 降级机制 | 不同学校导出格式差异大 | 强制所有字段会导致用户无法使用 |
