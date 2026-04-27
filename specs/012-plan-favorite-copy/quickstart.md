# Quickstart: Plan Favorite & Copy to Clipboard

## Verify the features

1. **Start the frontend dev server**:
   ```bash
   cd frontend && npx vite
   ```

2. **Test Favorite button**:
   - Upload a course file and request recommendations
   - Click the favorite button on a recommendation plan
   - Verify the button changes to "favorited" state
   - Verify the plan appears in the favorites list
   - Click again to unfavorite — verify removal

3. **Test Copy to Clipboard button**:
   - View a recommendation plan with courses
   - Click the copy to clipboard button
   - Verify visual confirmation appears ("已复制")
   - Paste into any text field and verify all course names + numbers are present

4. **Test edge cases**:
   - Run a new recommendation query — favorites should persist
   - Test with a course that has no course number — should show only name in copied text
