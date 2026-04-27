# Quickstart: Period-Based Scheduling

## Verify the standardization

1. **Run backend tests** (after fixing):
   ```bash
   cd backend && python -m pytest tests/ -v
   ```
   All tests should pass with integer period values.

2. **Start the frontend dev server**:
   ```bash
   cd frontend && npx vite
   ```

3. **Upload a course file** and verify:
   - Course cards display schedule as "周一（3-4节）" (period numbers)
   - The weekly schedule grid shows rows labeled 1-13
   - No clock time references appear anywhere in the UI

4. **Test conflict detection**:
   - Select two courses at the same period on the same day
   - Verify the system detects a time conflict
