# Data Model: 映射流程优化

## 实体定义

### SystemFieldInfo (前端显示用)

描述系统字段的展示信息，不持久化，仅在前端组件内使用。

| 属性 | 类型 | 说明 |
|------|------|------|
| key | string | 系统字段 key（如 "schedule"） |
| label | string | 中文名称（如 "上课时间"） |
| description | string | 用途说明（如 "用于检测课程时间冲突"） |
| degradation | DegradationImpact \| null | 不映射时的降级影响，name/credit 为 null |
| isRequired | boolean | 是否必填字段（name、credit 为 true） |
| mappedSource | string \| null | LLM 已映射的文件列名，未映射为 null |

数据来源：
- `key`, `label`, `isRequired` — 前端常量 `SYSTEM_FIELDS`
- `description` — 从前端常量 `FIELD_DESCRIPTIONS` 获取
- `degradation` — 从 `ImportAnalyzeResponse.degradation.impacts` 查找
- `mappedSource` — 从 `ImportAnalyzeResponse.mapping.mappings` 中查找 target 匹配项

### ManualSelection (前端状态)

用户手动选择的映射关系，存储在 `ColumnMappingPreview` 组件的 `useState` 中。

| 属性 | 类型 | 说明 |
|------|------|------|
| [systemFieldKey] | string | key 为系统字段 key，value 为用户选择的文件列名，空字符串表示"不映射" |

传递给父组件时转换为 `ColumnMapping[]` 格式。

## 状态机：FileUpload 步骤流转

```
idle → analyzing → preview → importing → done
  ↑        ↓          ↑  ↘      ↑           ↑
  ←────────┘          ←───┘     ←───────────┘
  (重新选择文件)       (返回上传)  (返回修改映射)
```

- `idle` → `analyzing`: 用户选择文件
- `analyzing` → `preview`: 分析完成，展示映射预览
- `preview` → `importing`: 用户确认导入
- `importing` → `done`: 导入完成
- `done` → `preview`: 点击"返回修改映射"（保留映射选择和 raw_data）
- `done` → `idle`: 点击"重新上传"（完全重置）
- `preview` → `idle`: 点击"重新选择文件"（完全重置）

## 关系

本功能不涉及后端数据持久化，所有状态在前端组件内管理。
- `SystemFieldInfo` 聚合自 `MappingResult.unmapped_target` + `DegradationReport`
- `ManualSelection` 合并到 `MappingResult.mappings` 后发送给后端 confirm 接口
