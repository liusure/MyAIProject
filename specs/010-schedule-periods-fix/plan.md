# Implementation Plan: Schedule Periods & Card Deduplication

**Branch**: `010-schedule-periods-fix` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-schedule-periods-fix/spec.md`

## Summary

Two frontend-only UI fixes to the course recommendation display: (1) replace clock-time row labels in the schedule grid with period numbers 1-13, and (2) deduplicate course cards so each course renders once regardless of how many schedule slots it has.

## Technical Context

**Language/Version**: TypeScript 5.x, React 19
**Primary Dependencies**: Vite 8, React Router
**Storage**: N/A (frontend display only)
**Testing**: TypeScript type checker (`tsc --noEmit`), Vite production build
**Target Platform**: Modern browsers (ES2020+)
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: No measurable impact — constant-time mapping lookup, linear dedup filter
**Constraints**: Must not change backend API or data types
**Scale/Scope**: 2 files modified, ~30 lines changed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Type Safety | PASS | All changes maintain existing TypeScript types; no `any` introduced |
| Modular Design | PASS | Changes isolated to ScheduleView component and CourseSelect page |
| Test Coverage | PASS | TypeScript compiler validates type correctness; production build validates rendering |
| Performance | PASS | O(n) dedup filter, O(1) time-to-period lookup via Record |
| UX Consistency | PASS | Visual style unchanged; only labels and dedup logic affected |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/010-schedule-periods-fix/
├── plan.md              # This file
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
frontend/src/
├── components/
│   └── ScheduleView/
│       └── ScheduleView.tsx    # Modified: period numbers + time-to-period mapping
├── pages/
│   └── CourseSelect.tsx        # Modified: course deduplication before card render
└── types/
    └── index.ts               # Unchanged (ScheduleSlot, Course types)
```

**Structure Decision**: Option 2 — Web application. Only frontend files modified; backend untouched.

## Phase 0: Research

No unknowns. All technical decisions are straightforward:

- **Time-to-period mapping**: Use a `Record<string, number>` lookup table. Chinese universities standardize on 13 periods starting at 08:00.
- **Deduplication strategy**: Filter by course `id` field using `findIndex` — preserves first occurrence, removes duplicates.

## Phase 1: Design & Contracts

### Data Model

No new entities. Existing types reused:
- `ScheduleSlot` (`start_period: string`, `end_period: string`, `day_of_week: number`)
- `Course` (`id: string`, `schedule: ScheduleSlot[]`)

### Interface Changes

**ScheduleView.tsx**:
- `HOURS` constant (8-18) → `PERIODS` constant (1-13)
- Add `TIME_TO_PERIOD` mapping: `'08:00' → 1, '09:00' → 2, ... '20:00' → 13`
- `slotMap` loop: `parseInt(slot.start_period)` → `TIME_TO_PERIOD[slot.start_period]`
- Row labels: `${hour}:00` → `{period}` (plain number)
- Corner header: "时间" → "节次"

**CourseSelect.tsx**:
- Before rendering `CourseCard` list, deduplicate `plan.courses` by `id`:
  ```tsx
  const uniqueCourses = plan.courses.filter(
    (c, idx, arr) => arr.findIndex(x => x.id === c.id) === idx
  );
  ```
- `ScheduleView` still receives full `plan.courses` (with all slots) for accurate grid placement

### Contracts

No API changes. Frontend-only modification.

### Quickstart

1. Start frontend dev server: `cd frontend && npx vite`
2. Navigate to course selection page
3. Submit a course recommendation query
4. Verify: schedule grid shows 1-13 rows, each course card appears once

## Complexity Tracking

No violations. No entries needed.
