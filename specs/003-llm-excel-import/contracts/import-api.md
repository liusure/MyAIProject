# API Contract: 课表导入接口

所有端点在 `/api/v1/import` 下。

## POST /analyze — 分析 Excel 文件并返回列映射

**请求**: `multipart/form-data`
- `file`: Excel 文件（.xlsx/.xls/.csv）

**响应 200**:
```json
{
  "mapping": {
    "mappings": [
      {"source": "课程名称", "target": "name", "confidence": 0.98},
      {"source": "学分", "target": "credit", "confidence": 0.95},
      {"source": "任课教师", "target": "instructor", "confidence": 0.92}
    ],
    "unmapped_source": ["备注"],
    "unmapped_target": ["capacity", "campus"]
  },
  "sample_data": [
    {"name": "数据结构", "credit": 3.0, "instructor": "张三"},
    {"name": "操作系统", "credit": 4.0, "instructor": "李四"}
  ],
  "degradation": {
    "missing_fields": ["schedule", "category", "capacity", "campus"],
    "impacts": [
      {"field": "schedule", "impact": "无法检测时间冲突", "fallback": "课程将标记为'时间未指定'"},
      {"field": "category", "impact": "无法按分类筛选", "fallback": "将根据课程名称自动推断分类"}
    ]
  }
}
```

**错误响应**:
- 400: 文件格式不支持
- 400: 文件不含任何可识别的课程列
- 413: 文件超过 5MB 限制
- 500: LLM 分析失败（自动回退到固定格式，不应返回此错误）

## POST /confirm — 确认映射并导入课程到会话

**请求** `application/json`:
```json
{
  "mapping": {
    "mappings": [
      {"source": "课程名称", "target": "name", "confidence": 0.98}
    ],
    "unmapped_source": ["备注"],
    "unmapped_target": ["capacity"]
  },
  "raw_data": [
    {"课程名称": "数据结构", "学分": 3, "备注": "必修"}
  ]
}
```

**响应 200**:
```json
{
  "courses": [
    {
      "id": "uuid-1",
      "name": "数据结构",
      "credit": 3.0,
      "course_no": null,
      "instructor": null,
      "category": null,
      "schedule": [],
      "semester": null
    }
  ],
  "total": 42,
  "errors": [
    {"row": 5, "message": "学分必须为数字"}
  ],
  "degradation": {
    "missing_fields": ["course_no", "schedule"],
    "impacts": [...]
  }
}
```

**错误响应**:
- 400: mapping 格式无效
- 400: 所有行均未通过核心字段校验

## GET /session/courses — 获取当前会话课程

**响应 200**:
```json
{
  "courses": [
    {
      "id": "uuid-1",
      "name": "数据结构",
      "credit": 3.0,
      "instructor": "张三",
      "category": "专业必修",
      "schedule": [
        {"day_of_week": 1, "start_period": "1", "end_period": "2", "weeks": [1,2,3]}
      ]
    }
  ],
  "degradation": {
    "missing_fields": ["campus"],
    "impacts": [...]
  }
}
```

**无数据响应 204**: 会话中无课程数据。

## DELETE /session/courses — 清除会话课程

**响应 204**: 无内容。

## 与现有端点的集成

### POST /conversation/chat (修改)

推荐时优先从 SessionStore 获取课程:
- 若 SessionStore 有数据 → 使用会话课程做推荐
- 若 SessionStore 无数据 → 提示"请先上传课表"
- 推荐结果接入 ConflictEngine 做冲突检测

### POST /plans (修改)

保存方案时:
- course_ids 改为支持 session course 的 name 引用
- 或要求 session 课程有稳定的 id（UUID 生成）

## 认证

所有端点通过 cookie `device_id` 识别用户（复用现有 get_or_create_device 机制）。
