# Implementation Plan: 未识别列手动映射

**Branch**: `005-manual-column-mapping` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-manual-column-mapping/spec.md`

## Summary

LLM 自动列映射后，部分列可能未被识别。本功能在映射预览页面的"未识别的列"区域为每个未识别列添加下拉选择框，用户可手动选择系统字段映射，未选择的列静默忽略。前端交互增强，后端无需修改。

## Technical Context

**Language/Version**: TypeScript (React 19), Python 3.12
**Primary Dependencies**: React, FastAPI, Pydantic
**Storage**: In-memory (SessionStore, 非持久化)
**Testing**: 手动测试（上传含未识别列的 Excel）
**Target Platform**: Web (现代浏览器)
**Project Type**: Web application (React + FastAPI)
**Performance Goals**: 下拉框选择后映射合并 < 100ms
**Constraints**: 不修改后端接口，仅前端增强
**Scale/Scope**: 单个组件修改，影响 ColumnMappingPreview + FileUpload

## Constitution Check

无宪法违规。本功能为前端交互增强，复用已有后端接口，不引入新依赖。

## Project Structure

### Documentation (this feature)

```text
specs/005-manual-column-mapping/
├── plan.md              # 本文件
├── spec.md              # 需求规格
├── research.md          # 无需研究
├── data-model.md        # 无新实体
├── quickstart.md        # 测试步骤
└── tasks.md             # 由 /speckit.tasks 生成
```

### Source Code (repository root)

```text
frontend/src/
├── components/
│   ├── ColumnMappingPreview/
│   │   ├── ColumnMappingPreview.tsx    # 主要修改
│   │   └── ColumnMappingPreview.css    # 样式修改
│   └── FileUpload/
│       └── FileUpload.tsx              # 传递 unmapped_target 给子组件
└── types/
    └── index.ts                        # 无需修改（已有类型足够）
```

**Structure Decision**: Option 2 — Web application。仅修改前端组件，后端不变。

## Phase 0: Research

无未知项，无需研究。

## Phase 1: Design

### Data Model

无新实体。复用现有类型：
- `ColumnMapping { source, target, confidence }` — 已有
- `MappingResult { mappings, unmapped_source, unmapped_target }` — 已有

前端新增内部状态：
- `manualMappings: Record<string, string>` — 用户手动选择的映射 `{ 未识别列名: 系统字段key }`

### Interface Contract

无新 API 接口。用户确认导入时：
1. 合并 `mapping.mappings`（LLM 结果）+ 手动映射
2. 调用现有 `POST /import/confirm` 接口，`mapping.mappings` 包含合并后的完整映射

### Quickstart

1. 上传包含 LLM 未识别列的 Excel 文件
2. 在映射预览页面，查看"未识别的列"区域
3. 为未识别列通过下拉框选择系统字段
4. 验证下拉框中已映射字段不再出现
5. 点击确认导入，验证手动映射的列数据正确导入
6. 不选择任何映射直接确认，验证导入正常完成
