# Tasks: 未识别列手动映射

**Input**: Design documents from `/specs/005-manual-column-mapping/`
**Prerequisites**: plan.md, spec.md, quickstart.md

**Tests**: Not explicitly requested in spec. No test tasks generated.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - 未识别列手动选择映射 (Priority: P1)

**Goal**: 用户在映射预览页面为未识别列通过下拉框手动选择系统字段，合并到映射结果后导入。

**Independent Test**: 上传含未识别列的 Excel，在预览页为未识别列选择下拉框映射，确认后验证数据正确导入。

### Implementation for User Story 1

- [X] T001 [US1] Add manual mapping state and logic in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` — add `manualMappings` state, `onMappingsChanged` callback prop, define SYSTEM_FIELDS constant with key-label pairs
- [X] T002 [US1] Replace unmapped column tags with dropdown selects in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` — render a `<select>` for each unmapped_source column, options = SYSTEM_FIELDS + "不映射" default, onChange updates manualMappings state
- [X] T003 [US1] Add dropdown styles in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.css` — style the select elements to match existing tag design
- [X] T004 [US1] Merge manual mappings on confirm in `frontend/src/components/FileUpload/FileUpload.tsx` — receive manual mappings from ColumnMappingPreview, merge with LLM mapping before calling confirmImport

**Checkpoint**: US1 complete — users can manually map unmapped columns via dropdowns and import with merged mappings.

---

## Phase 2: User Story 2 - 可用系统字段动态过滤 (Priority: P2)

**Goal**: 下拉框中只显示尚未被映射的系统字段，避免重复映射。

**Independent Test**: LLM 已识别"课程名称→name"，验证未识别列下拉框中不再包含 name 选项。

### Implementation for User Story 2

- [X] T005 [US2] Implement dynamic field filtering in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` — compute `availableTargets` by excluding LLM-mapped targets + already-selected manual targets, pass filtered list to each dropdown

**Checkpoint**: US2 complete — dropdowns dynamically exclude already-mapped fields.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [ ] T006 Verify end-to-end flow per `quickstart.md` — upload → analyze → preview with dropdowns → select mappings → confirm → data imported correctly
- [ ] T007 Verify "不选择直接导入" works — upload → analyze → skip all dropdowns → confirm → import succeeds with only LLM mappings

---

## Dependencies & Execution Order

```
Phase 1 (US1 - Manual Mapping)  ← MVP
    └── Phase 2 (US2 - Dynamic Filtering)  ← Depends on US1
        └── Phase 3 (Polish)  ← Depends on all
```

- T001-T004 are sequential within US1 (same component file)
- T005 modifies the same file as T001-T004, runs after US1 complete
- T006-T007 are verification only

## Implementation Strategy

### MVP (US1 Only)
1. Complete Phase 1: Manual mapping dropdowns in ColumnMappingPreview
2. Merge logic in FileUpload on confirm
3. **STOP and VALIDATE**: Upload Excel, manually map a column, verify import

### Incremental Delivery
1. Phase 1 (US1) → Manual mapping works → **MVP!**
2. Phase 2 (US2) → Dynamic filtering works
3. Phase 3 → Verification
