# 快速开始：LLM 自动选课系统

## 前置要求

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+（Session 存储 + 缓存）
- MiMo API Key（或 OpenAI/Claude API Key）

## 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填写数据库连接、Redis 连接和 LLM API Key

# 5. 初始化数据库
alembic upgrade head

# 6. 导入示例课程数据
python -m scripts.seed_courses

# 7. 启动开发服务器
uvicorn src.main:app --reload --port 8000
```

## 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

## 验证功能

### 1. 登录系统（FR-09）

打开浏览器访问 `http://localhost:5173`，使用学号和密码登录。

预期结果：登录成功，Session 建立，进入系统首页。

### 2. 自然语言选课推荐（US1）

在对话框中输入：

> "我想选周三下午的计算机课程，3 学分的"

预期结果：系统返回至少 3 个符合条件的课程推荐方案，每个方案包含匹配度评分。LLM 输出为 JSON 结构化格式，前端解析后展示自然语言回复和结构化方案。

### 3. 课程冲突检测（US2）

在推荐结果中，如果方案包含时间冲突的课程：

预期结果：冲突课程被高亮标记，显示冲突类型（时间/地点/先修/通勤），并提供替代建议。

### 4. 方案收藏与导出（US3）

选择一个满意的推荐方案，点击「收藏方案」：

预期结果：方案保存到"我的方案"页面。

在"我的方案"页面点击「导出 PDF」：

预期结果：系统生成包含课程名称、时间、地点、教师的 PDF 文件并下载。

### 5. 教务数据导入（US4）

以管理员身份登录，进入管理页面，上传 CSV 或 Excel 课程数据文件：

预期结果：系统自动识别文件格式，解析并导入课程数据，显示导入成功/失败统计。

### 6. LLM 降级测试（FR-08）

模拟 LLM 服务不可用（断开网络或配置错误 API Key），在对话框中输入关键词搜索：

预期结果：系统自动降级至关键词搜索模式，返回匹配的课程列表。

## API 文档

启动后端后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 运行测试

```bash
# 后端测试
cd backend
pytest --cov=src --cov-report=term-missing

# 前端测试
cd frontend
npm test
```

## 常见问题

### LLM 服务不可用

系统自动降级至关键词搜索模式。在对话框中直接输入课程关键词即可搜索。

### 数据库连接失败

检查 `.env` 中的 `DATABASE_URL` 配置，确保 PostgreSQL 正在运行且数据库已创建。

### Redis 连接失败

检查 `.env` 中的 `REDIS_URL` 配置，确保 Redis 正在运行。Session 和 LLM 缓存依赖 Redis。

### 课程导入格式错误

参考 `docs/course_import_template.csv` 获取标准导入格式。系统同时支持 CSV 和 Excel（.xlsx），自动识别格式。
