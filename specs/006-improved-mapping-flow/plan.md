# Implementation Plan: 映射流程优化

**Branch**: `005-manual-column-mapping` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)

## Summary

优化 Excel 导入的列映射交互流程。核心变更：
1. 映射 UI 方向翻转：从未识别列→选择系统字段，改为系统字段→选择未识别列，并在中间展示字段用途和降级说明
2. 导入结果页增加"返回修改映射"按钮，支持回退到预览页重新选择
3. 整体流程每一步都有回退路径
4. 当 LLM 完美映射所有字段时隐藏手动映射区域

**范围**：纯前端变更，后端 API 无需修改。

## Technical Context

**Language/Version**: TypeScript 5.x, React 19
**Primary Dependencies**: React, Vite
**Storage**: N/A (session in-memory, frontend state only)
**Testing**: Manual verification per quickstart.md
**Target Platform**: 现代浏览器 (Chrome/Firefox/Safari)
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: 首屏映射预览加载 < 1秒
**Constraints**: 不修改后端 API 契约，复用现有 ImportAnalyzeResponse 和 ImportConfirmResponse
**Scale/Scope**: 修改 2 个组件文件，新增 1 个 CSS 文件无需修改

## Constitution Check

| 原则 | 状态 | 说明 |
|------|------|------|
| 类型安全优先 | PASS | TypeScript 严格模式，所有 props 已类型化 |
| 模块化设计 | PASS | 仅修改表现层组件，不触及业务逻辑层 |
| 响应式交互 | PASS | 加载状态和错误处理已有，回退按钮新增 |
| 首屏加载 < 1.5秒 | PASS | 无新增依赖，仅 UI 重组 |

## Project Structure

### Documentation (this feature)

```text
specs/006-improved-mapping-flow/
├── plan.md              # This file
├── research.md          # Phase 0 — research (not needed, no unknowns)
├── data-model.md        # Phase 1 — data model
├── quickstart.md        # Phase 1 — verification steps
├── contracts/           # Phase 1 — API contracts (N/A, no backend changes)
└── tasks.md             # Phase 2 — task breakdown
```

### Source Code (repository root)

```text
frontend/src/components/
├── ColumnMappingPreview/
│   ├── ColumnMappingPreview.tsx    # [MODIFY] 重写映射UI方向
│   └── ColumnMappingPreview.css    # [MODIFY] 更新样式
└── FileUpload/
    ├── FileUpload.tsx              # [MODIFY] 添加回退逻辑
    └── FileUpload.css              # [MODIFY] 添加回退按钮样式

backend/src/services/
└── import_analyzer.py              # [READ ONLY] 提供 DEGRADATION_IMPACTS 数据参考
```

**Structure Decision**: Option 2 — Web application，本次仅修改 frontend 侧 2 个组件文件。后端无需变更。

## Complexity Tracking

无违反项。本功能为前端 UI 交互重组，不引入新依赖或新层级。
