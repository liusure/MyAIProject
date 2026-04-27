# Tasks: 映射流程优化

**Input**: Design documents from `/specs/006-improved-mapping-flow/`
**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec. No test tasks generated.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - 系统需求驱动的映射选择 (Priority: P1)

**Goal**: 映射预览页面以系统需求为视角展示：左侧系统字段名、中间用途+降级说明、右侧下拉选择未识别列。必填字段红色高亮。LLM完美映射时隐藏手动区域。

**Independent Test**: 上传含未识别列的 Excel，确认每个未映射系统字段显示字段名、用途、降级说明和下拉框。上传可完全识别的文件，确认手动区域隐藏。

### Implementation for User Story 1

- [X] T001 [US1] Add SYSTEM_FIELDS constant with descriptions and degradation info in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` — extend existing SYSTEM_FIELDS to include `description` (string) and `isRequired` (boolean) properties, add FIELD_DESCRIPTIONS constant mapping each system field key to a human-readable purpose string
- [X] T002 [US1] Reverse mapping UI direction in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` — change the unmapped section from showing "file column → system field dropdown" to showing "system field → file column dropdown", iterate over `unmappedTargets` instead of `unmapped_source`, render each system field row with: left=label, middle=description+degradation, right=dropdown of available file columns
- [X] T003 [US1] Style required fields with red highlight in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.css` — add `.system-field-required` class with red border/text for name/credit fields
- [X] T004 [US1] Add field description and degradation info display in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.css` — add `.field-info` styles for the middle section showing description and degradation impact text
- [X] T005 [US1] Handle all-mapped edge case in `frontend/src/components/ColumnMappingPreview/ColumnMappingPreview.tsx` — when `unmappedTargets` is empty, hide the manual mapping section and show a success message "所有字段已成功识别"

**Checkpoint**: US1 complete — mapping UI reversed with degradation info, required fields highlighted, all-mapped case handled.

---

## Phase 2: User Story 2 - 导入后可回退重新选择 (Priority: P1)

**Goal**: 导入结果页面提供"返回修改映射"按钮，点击后回到映射预览状态，保留之前的映射选择。重新导入时用新数据覆盖旧数据。

**Independent Test**: 完成一次导入后，在结果页点击"返回修改映射"，验证回到预览页且选择被保留。修改映射后重新导入，验证数据被替换。

### Implementation for User Story 2

- [X] T006 [US2] Add "返回修改映射" button to done step in `frontend/src/components/FileUpload/FileUpload.tsx` — add a button that sets step back to 'preview' while preserving analyzeResult, rawData, and manualMappings state
- [X] T007 [US2] Ensure re-import overwrites previous data in `frontend/src/components/FileUpload/FileUpload.tsx` — verify that handleConfirm always calls confirmImport with current merged mapping (already works by design since onCoursesImported replaces session data)

**Checkpoint**: US2 complete — users can return to mapping preview from import result and re-import with new mappings.

---

## Phase 3: User Story 3 - 整体流程可回退 (Priority: P2)

**Goal**: 整个导入流程每一步都有返回路径。映射预览页有"重新选择文件"按钮，导入结果页有"重新上传"按钮。

**Independent Test**: 在每个步骤（上传→预览→结果）都尝试返回，确认每一步都能回到上一步。

### Implementation for User Story 3

- [X] T008 [US3] Add "重新选择文件" button to preview step in `frontend/src/components/FileUpload/FileUpload.tsx` — add a secondary button in the preview actions that calls reset() to return to idle state
- [X] T009 [US3] Ensure "重新上传" button in done step resets all state in `frontend/src/components/FileUpload/FileUpload.tsx` — verify the existing reset() call in done step properly clears manualMappings, confirmResult, and all other state

**Checkpoint**: US3 complete — every step in the import flow has a back path.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T010 Verify end-to-end flow per `quickstart.md` — test all 5 scenarios: system-driven mapping, all-mapped case, back from result, full flow back, skip-and-import
- [X] T011 Verify button labels are clear and distinguishable — "返回修改映射" vs "重新上传" should have distinct visual treatment (primary vs secondary)

---

## Dependencies & Execution Order

```
Phase 1 (US1 - 系统需求驱动)  ← MVP
    └── Phase 2 (US2 - 导入回退)  ← Depends on US1 UI structure
        └── Phase 3 (US3 - 流程回退)  ← Depends on US1+US2
            └── Phase 4 (Polish)  ← Depends on all
```

- T001-T005 are sequential within US1 (same component file)
- T006-T007 modify FileUpload.tsx, sequential within US2
- T008-T009 modify FileUpload.tsx, sequential within US3
- T010-T011 are verification only

## Implementation Strategy

### MVP (US1 Only)
1. Complete Phase 1: Reverse mapping UI with degradation info
2. **STOP and VALIDATE**: Upload Excel, verify new mapping UI works
3. Deploy/demo if ready

### Incremental Delivery
1. Phase 1 (US1) → Mapping UI reversed → **MVP!**
2. Phase 2 (US2) → Back from import result
3. Phase 3 (US3) → Full flow back navigation
4. Phase 4 → Verification
