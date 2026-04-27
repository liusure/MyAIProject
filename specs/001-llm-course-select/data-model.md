# 数据模型：LLM 自动选课系统

## 实体关系图

```text
Student 1──* SavedPlan *──* Course
Student 1──* Conversation
Course *──* Course (先修关系，自引用)
SelectionRule（全局规则，不直接关联实体）
```

## 实体定义

### Student（学生）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 学生唯一标识 |
| student_no | VARCHAR(20) | UNIQUE, NOT NULL | 学号 |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| major | VARCHAR(100) | NOT NULL | 专业 |
| grade | SMALLINT | NOT NULL | 年级 |
| email | VARCHAR(100) | UNIQUE | 邮箱 |
| role | ENUM | NOT NULL, DEFAULT 'student' | 角色：student/admin |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希（Session-based 认证） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**验证规则**：
- student_no 必须符合学校学号格式
- grade 范围 1-6

### Course（课程）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 课程唯一标识 |
| course_no | VARCHAR(20) | UNIQUE, NOT NULL | 课程编号 |
| name | VARCHAR(100) | NOT NULL | 课程名称 |
| credit | DECIMAL(3,1) | NOT NULL | 学分 |
| instructor | VARCHAR(50) | NOT NULL | 授课教师 |
| capacity | INTEGER | NOT NULL | 课程容量 |
| schedule | JSONB | NOT NULL | 上课时间（多时段） |
| location | VARCHAR(100) | NOT NULL | 上课地点 |
| campus | VARCHAR(50) | NOT NULL | 所在校区 |
| category | VARCHAR(50) | NOT NULL | 课程类别（必修/选修/通识） |
| description | TEXT | | 课程描述 |
| semester | VARCHAR(20) | NOT NULL | 学期（如 2026-Spring） |
| is_active | BOOLEAN | DEFAULT true | 是否可选 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**schedule JSONB 结构**：
```json
[
  {
    "day_of_week": 1,
    "start_period": "1",
    "end_period": "2",
    "weeks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
  }
]
```

**验证规则**：
- credit > 0 且 ≤ 10
- capacity > 0
- schedule 中 start_period < end_period
- day_of_week 范围 1-7

### Prerequisite（先修关系）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| course_id | UUID | FK(Course), NOT NULL | 目标课程 |
| prerequisite_course_id | UUID | FK(Course), NOT NULL | 先修课程 |
| min_grade | DECIMAL(3,1) | DEFAULT 60 | 最低成绩要求 |

**验证规则**：
- course_id ≠ prerequisite_course_id（不能自引用）
- 无循环依赖（通过图检测）

### SavedPlan（收藏方案）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 方案唯一标识 |
| student_id | UUID | FK(Student), NOT NULL | 学生 |
| name | VARCHAR(100) | NOT NULL | 方案名称 |
| course_ids | JSONB | NOT NULL | 课程 ID 列表 |
| total_credits | DECIMAL(4,1) | NOT NULL | 总学分 |
| match_score | DECIMAL(5,2) | | 匹配度评分 |
| notes | TEXT | | 学生备注 |
| created_at | TIMESTAMP | NOT NULL | 收藏时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**course_ids JSONB 结构**：
```json
["uuid-1", "uuid-2", "uuid-3"]
```

**验证规则**：
- course_ids 非空
- course_ids 中的每个 ID 必须引用有效的 Course

### SelectionRule（选课规则）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 规则唯一标识 |
| name | VARCHAR(100) | NOT NULL | 规则名称 |
| max_credits | INTEGER | NOT NULL | 最大学分上限 |
| min_credits | INTEGER | DEFAULT 0 | 最小学分要求 |
| enrollment_start | TIMESTAMP | NOT NULL | 选课开始时间 |
| enrollment_end | TIMESTAMP | NOT NULL | 选课结束时间 |
| semester | VARCHAR(20) | NOT NULL | 适用学期 |
| priority_strategy | ENUM | NOT NULL | 优先级策略：credit/interest/major |
| is_active | BOOLEAN | DEFAULT true | 是否生效 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**验证规则**：
- max_credits > min_credits
- enrollment_start < enrollment_end

### Conversation（对话记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 对话唯一标识 |
| student_id | UUID | FK(Student), NOT NULL | 学生 |
| messages | JSONB | NOT NULL | 对话消息列表 |
| context | JSONB | | 对话上下文（推荐结果等） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**messages JSONB 结构**：
```json
[
  {
    "role": "user",
    "content": "我想选周三下午的机器学习课程",
    "timestamp": "2026-04-22T14:00:00Z"
  },
  {
    "role": "assistant",
    "content": "为您推荐以下课程...",
    "structured_data": {
      "recommendations": [...],
      "conflicts": [...]
    },
    "timestamp": "2026-04-22T14:00:05Z"
  }
]
```

### AuditLog（操作日志）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 日志唯一标识 |
| student_id | UUID | FK(Student) | 操作学生（可空，管理员操作） |
| action | VARCHAR(50) | NOT NULL | 操作类型 |
| entity_type | VARCHAR(50) | NOT NULL | 操作对象类型 |
| entity_id | UUID | NOT NULL | 操作对象 ID |
| details | JSONB | NOT NULL | 操作详情 |
| ip_address | INET | | IP 地址 |
| created_at | TIMESTAMP | NOT NULL | 操作时间 |

## 索引策略

- Student: student_no (B-tree), role (B-tree)
- Course: course_no (B-tree), semester + category (复合), schedule (GIN for JSONB)
- SavedPlan: student_id + created_at (复合)
- Conversation: student_id + created_at (复合)
- AuditLog: student_id + created_at (复合), action + created_at (复合)
