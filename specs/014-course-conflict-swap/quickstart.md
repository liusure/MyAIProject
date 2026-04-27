# Quickstart: Course Conflict Swap Selection

## Verify the feature

1. **Start the project**:
   ```bash
   cd backend && uvicorn src.main:app --port 8000
   cd frontend && npx vite
   ```

2. **Test conflict-aware display**:
   - Upload courses that have time conflicts
   - Request recommendations that produce a plan with conflicting courses
   - Verify that all course cards are displayed in the course list
   - Verify that the schedule only shows the conflict-free subset by default
   - Verify that unselected conflicting courses have a dimmed/alternative visual style

3. **Test swap behavior**:
   - Click on an unselected conflicting course card
   - Verify that its conflict partner is removed from the schedule
   - Verify that the clicked course now appears in the schedule
   - Verify that the clicked course card shows a "selected" visual indicator
   - Click the original course card to swap back

4. **Test hover conflict highlighting**:
   - Hover over a course card that has conflicts
   - Verify that its conflicting alternative course cards display a red border
   - Move the mouse away and verify the red borders disappear

5. **Test copy/favorite with selection**:
   - After making a swap, click the copy button
   - Verify that only the currently selected courses are copied
   - After making a swap, click the favorite button
   - Verify that the favorited plan contains only the selected courses

6. **Test no-op on selected course**:
   - Click on a course card that is already selected (displayed in schedule)
   - Verify that nothing changes (no-op behavior)
