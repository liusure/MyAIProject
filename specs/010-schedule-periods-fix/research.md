# Research: Schedule Periods & Card Deduplication

## Decision 1: Time-to-Period Mapping

- **Decision**: Use a static `Record<string, number>` lookup table mapping time strings ("1") to period numbers (1)
- **Rationale**: Chinese universities use standardized period numbering. A static map is O(1), zero-dependency, and self-documenting. The `start_period`/`end_period` fields in the backend are strings like "1", "3" — direct lookup is cleaner than arithmetic parsing.
- **Alternatives considered**:
  - Arithmetic: `(parseInt(start_period) - 8) + 1` — works but fragile if non-hour-aligned times appear
  - Backend change: return period numbers from API — unnecessary scope expansion; frontend mapping is sufficient

## Decision 2: Deduplication Strategy

- **Decision**: Filter by `course.id` using `findIndex` to keep first occurrence
- **Rationale**: Simple, no new dependencies, preserves insertion order. The `id` field is a reliable unique identifier for courses.
- **Alternatives considered**:
  - `Map`-based dedup — more code for same result on small arrays
  - Backend fix: return unique courses — would lose per-slot schedule data needed by ScheduleView; frontend dedup for card display is the right layer
  - Set-based — can't use objects in Sets without serialization
