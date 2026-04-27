# Quickstart: Fix Credit Calculation & Add Category Credit Breakdown

## Verify the features

1. **Start the project**:
   ```bash
   cd backend && uvicorn src.main:app --port 8000
   cd frontend && npx vite
   ```

2. **Test credit fix (US1)**:
   - Upload courses, request recommendations, note the total credits
   - Favorite a plan
   - Navigate to "我的方案"
   - Verify the saved plan card shows the correct total credits (not 0)
   - Export the plan as TXT and verify credits are correct

3. **Test category breakdown (US2)**:
   - View a recommendation plan with courses from multiple categories
   - Verify the plan header shows category credit breakdown (e.g., "必修课 8 学分 · 公选课 4 学分")
   - Navigate to "我的方案" and verify saved plans also show the breakdown
   - Export a plan and verify the TXT includes the breakdown
   - View a plan where all courses are the same category — verify no redundant breakdown is shown
