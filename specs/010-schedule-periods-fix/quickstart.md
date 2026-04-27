# Quickstart: Schedule Periods & Card Deduplication

## Manual Verification Steps

1. Start the frontend dev server:
   ```bash
   cd frontend && npx vite
   ```

2. Open the course selection page in the browser

3. Submit a recommendation query (e.g., "推荐计算机课程")

4. **Verify schedule grid**:
   - Left column shows numbers 1-13 (not "1", "2", etc.)
   - Corner header reads "节次" not "时间"
   - Courses appear in correct period rows

5. **Verify course cards**:
   - Each course appears exactly once in the course list
   - A course with multiple schedule slots (e.g., periods 3 and 4) shows as one card
   - ScheduleView still shows the course in all occupied period cells

## Automated Checks

```bash
cd frontend
npx tsc --noEmit    # TypeScript type check
npx vite build      # Production build
```

Both must pass with zero errors.
