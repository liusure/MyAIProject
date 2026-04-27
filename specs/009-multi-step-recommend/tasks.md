# Tasks: Multi-Step Course Recommendation

**Input**: Design documents from `/specs/009-multi-step-recommend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Tests included for critical paths only.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Verification)

**Purpose**: 确认现有环境和依赖可用

- [X] T001 确认 backend 可正常启动且现有测试全部通过（`cd backend && python -m pytest`）
- [X] T002 确认 MiMo API 可达且 `MIMO_API_KEY` 已配置（检查 `backend/.env`）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 确认核心依赖模块就绪，无阻塞项

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 确认 `SessionStore` 中 `category` 字段有值（检查 `backend/src/services/session_store.py` + `backend/src/services/import_parser.py` 中 category 映射逻辑）
- [X] T004 确认 `LLMProvider.generate_structured()` 支持自定义 schema（检查 `backend/src/services/llm/base.py` 接口签名）
- [X] T005 确认 `_filter_relevant()` 和 `_format_session_courses_for_llm()` 的现有行为可复用（阅读 `backend/src/services/recommend.py`）

**Checkpoint**: 基础确认完毕，可开始用户故事实现

---

## Phase 3: User Story 1 - Multi-Step Subject Filtering (Priority: P1) 🎯 MVP

**Goal**: 实现第一步学科过滤流程——从课程中提取唯一学科列表，发送给 LLM 做多选题，根据返回的学科在本地过滤课程子集。

**Independent Test**: 上传包含多学科课表的文件，输入"推荐计算机课程"，验证系统仅向 LLM 发送了学科列表并在本地筛选出计算机相关课程。

### Implementation for User Story 1

- [X] T006 [US1] 在 `backend/src/services/recommend.py` 中定义第一步 Schema 常量 `SUBJECT_FILTER_SCHEMA`
- [X] T007 [US1] 在 `backend/src/services/recommend.py` 中实现 `_extract_subjects()` 方法：从课程列表提取唯一 `category` 值，去重排序，过滤空值
- [X] T008 [US1] 在 `backend/src/services/recommend.py` 中实现 `_filter_by_subjects()` 方法：调用 LLM 做学科多选题，根据返回值在本地过滤课程；LLM 调用失败或返回空时回退到全部课程
- [X] T009 [US1] 在 `backend/src/services/recommend.py` 中重构 `recommend()` 方法：在现有逻辑前插入学科过滤步骤，过滤后的课程传给后续处理
- [X] T010 [US1] 在 `backend/src/services/recommend.py` 中添加日志记录：`[STEP1_SUBJECTS]` 记录提取的学科列表和 LLM 返回结果

**Checkpoint**: 第一步学科过滤独立工作——输入"推荐计算机课程"仅发送学科列表给 LLM，本地过滤出计算机课程

---

## Phase 4: User Story 2 - Non-Sensitive Detail Filtering (Priority: P2)

**Goal**: 实现第二步非敏感信息筛选——将过滤后的课程仅包含非敏感字段（名称、序号、时间、主讲人、地点、学分）发送给 LLM 做精细筛选。

**Independent Test**: 验证发送给 LLM 的消息中仅包含非敏感字段，且 LLM 返回的推荐方案中课程时间无冲突、方向符合用户描述。

### Implementation for User Story 2

- [X] T011 [US2] 在 `backend/src/services/recommend.py` 中实现 `_format_courses_for_step2()` 方法：格式化为 `- 序号 | 课程名 | N学分 | 教师 | 周X HH:MM-HH:MM | 地点`，不含 id/capacity/campus/semester/description
- [X] T012 [US2] 在 `backend/src/services/recommend.py` 中重构 `recommend()` 方法的第二步：使用 `_format_courses_for_step2()` 替代 `_format_session_courses_for_llm()` 作为发送给 LLM 的课程信息
- [X] T013 [US2] 在 `backend/src/services/recommend.py` 中处理第二步无匹配结果：返回"无匹配课程"友好提示，不做额外降级
- [X] T014 [US2] 在 `backend/src/services/recommend.py` 中添加日志记录：`[STEP2_FILTER]` 记录发送给 LLM 的课程数量和非敏感字段确认

**Checkpoint**: 第二步独立工作——过滤后的课程仅发送非敏感字段给 LLM，无匹配时返回友好提示

---

## Phase 5: User Story 3 - End-to-End Recommendation Flow (Priority: P3)

**Goal**: 端到端流程验证——确保两步推荐流程完整衔接，最终返回包含完整课程信息且无时间冲突的推荐方案。

**Independent Test**: 完整流程测试——上传课表 → 输入需求 → 验证返回的推荐方案包含完整课程信息且时间无冲突。

### Implementation for User Story 3

- [X] T015 [US3] 在 `backend/src/services/recommend.py` 中重构 `recommend()` 方法的整体流程：串联第一步学科过滤 → 第二步非敏感筛选 → 本地回查 → 冲突检测，确保返回结构与现有 API 兼容
- [X] T016 [US3] 在 `backend/src/services/recommend.py` 中完善两步之间的回退链：第一步失败 → 回退全部课程进入第二步；第二步失败 → 回退到 FallbackLLMProvider
- [X] T017 [US3] 在 `backend/src/api/conversation.py` 中确认错误处理逻辑兼容新的两步流程（ContentFilteredError、降级缓存逻辑无需变更，验证即可）
- [X] T018 [US3] 验证 LLMCache 缓存键兼容新的两步推荐结果格式

**Checkpoint**: 端到端流程完整——输入需求后返回完整推荐方案，含课程详情、匹配度、冲突报告

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 最终验证和清理

- [X] T019 在 `backend/src/services/recommend.py` 中移除或保留旧的 `_filter_relevant()` 方法（评估学科过滤是否已替代其功能）— 保留，作为学科过滤后的二级安全网
- [X] T020 运行全部测试确认无回归（205 passed）
- [X] T021 运行类型检查（mypy 未安装，通过 import 验证 + 测试通过确认）
- [X] T022 按 `quickstart.md` 中的 4 个测试场景手动验证端到端流程
- [X] T023 更新 `CLAUDE.md` 中的 plan 引用（已完成）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 — 立即开始
- **Foundational (Phase 2)**: 依赖 Phase 1 完成 — 阻塞所有用户故事
- **User Story 1 (Phase 3)**: 依赖 Phase 2 完成 — 🎯 MVP
- **User Story 2 (Phase 4)**: 依赖 Phase 3 完成（因为第二步使用第一步过滤后的结果）
- **User Story 3 (Phase 5)**: 依赖 Phase 4 完成（端到端集成）
- **Polish (Phase 6)**: 依赖 Phase 5 完成

### User Story Dependencies

- **US1 (P1)**: 可在 Foundational 后开始 — 无其他故事依赖
- **US2 (P2)**: 依赖 US1 完成 — 使用 US1 的学科过滤结果
- **US3 (P3)**: 依赖 US1 + US2 完成 — 集成两步流程

### Within Each User Story

- 所有修改集中在 `backend/src/services/recommend.py`，需按顺序执行（非 [P]）
- 每个方法实现后立即验证

### Parallel Opportunities

- Phase 1 的 T001 和 T002 可并行
- Phase 2 的 T003、T004、T005 可并行（只读检查）
- Phase 6 的 T020、T021 可并行

---

## Parallel Example: Phase 2 (Foundational Checks)

```bash
# 同时启动只读检查任务:
Task: "确认 SessionStore 中 category 字段有值"
Task: "确认 LLMProvider.generate_structured() 支持自定义 schema"
Task: "确认 _filter_relevant() 和 _format_session_courses_for_llm() 的现有行为"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: 环境确认
2. Complete Phase 2: 基础确认
3. Complete Phase 3: 第一步学科过滤
4. **STOP and VALIDATE**: 手动测试"推荐计算机课程"是否仅发送学科列表给 LLM
5. 可部署/演示

### Incremental Delivery

1. Phase 1 + Phase 2 → 基础就绪
2. Phase 3 (US1) → 学科过滤独立验证 → MVP!
3. Phase 4 (US2) → 非敏感字段筛选验证
4. Phase 5 (US3) → 端到端验证
5. Phase 6 → 清理和全面测试

### 单人开发策略

1. 个人完成 Phase 1 + Phase 2
2. 按优先级 P1 → P2 → P3 顺序实现
3. 每个 phase 完成后验证再继续
4. 最终 Polish 阶段全面回归测试

---

## Notes

- 所有实现集中在 `backend/src/services/recommend.py`（单文件修改）
- 无新 API 端点、无新数据模型、无新数据库迁移
- 现有的 `_build_recommendation_plan()` 和冲突检测逻辑完全复用
- LLMCache 缓存键基于消息内容，两步流程会产生不同的缓存键（第一步消息 ≠ 第二步消息），这是预期行为
- 向后兼容：`recommend()` 公共接口签名不变，API 层无需变更
