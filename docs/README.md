# LLM 自动选课推荐系统

AI 驱动的智能选课推荐平台，学生通过自然语言描述选课偏好，系统利用 LLM 理解意图并推荐最优课程方案。

## 系统特点

- **自然语言选课**：学生用中文描述选课偏好，AI 智能推荐
- **冲突检测**：自动检测时间、地点、先修课程和通勤冲突
- **方案收藏与导出**：收藏推荐方案，导出 TXT 用于对照选课
- **教务数据导入**：管理员批量导入 CSV/Excel 课程数据

> **注意**：系统不执行真实选课操作。实际选课由学生在学校系统中自行完成。

## 技术栈

- **后端**：Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **前端**：React 18 + TypeScript + Vite
- **数据库**：PostgreSQL 16 + Redis 7
- **LLM**：MiMo API（支持 OpenAI/Claude 切换）

## 快速开始

详见 [quickstart.md](../specs/001-llm-course-select/quickstart.md)

```bash
# 启动数据库服务
docker compose up -d

# 后端
cd backend
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn src.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## API 文档

启动后端后访问：http://localhost:8000/docs
