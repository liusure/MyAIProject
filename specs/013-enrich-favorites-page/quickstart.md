# Quickstart: Enrich Favorites Page & Page State Preservation

## Verify the features

1. **Start the project**:
   ```bash
   cd backend && uvicorn src.main:app --port 8000
   cd frontend && npx vite
   ```

2. **Test enriched plan cards**:
   - Upload courses, request recommendations, favorite a plan
   - Navigate to "我的方案"
   - Verify each card shows course count ("X 门课程") and weekly periods ("每周 X 节")

3. **Test TXT export**:
   - Click the export button on a saved plan
   - Verify a `.txt` file is downloaded
   - Open the file and verify it contains plan name, credits, and course list

4. **Test page state preservation**:
   - On the course selection page, request recommendations
   - Navigate to "我的方案"
   - Navigate back to "智能选课"
   - Verify recommendations and chat history are still displayed
