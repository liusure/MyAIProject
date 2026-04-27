# Contract: RecommendService (Multi-Step)

## 内部服务接口

本 feature 不新增外部 API 端点，仅重构 `RecommendService.recommend()` 内部逻辑。

### 公共接口（不变）

```python
class RecommendService:
    async def recommend(self, user_message: str, context: list[dict] | None = None) -> dict:
        """
        执行多步课程推荐。

        Returns:
            {
                "reply": str,                    # 自然语言回复
                "recommendations": list[RecommendationPlan],  # 推荐方案列表
            }
        Raises:
            ContentFilteredError: MiMo API 内容安全过滤触发
            Exception: LLM 调用失败（由上层降级到 FallbackLLMProvider）
        """
```

### 内部方法签名（新增/修改）

```python
def _extract_subjects(self, courses: list[SessionCourse]) -> list[str]:
    """从课程列表中提取所有唯一的学科（category）值，去重排序。"""

async def _filter_by_subjects(
    self, courses: list[SessionCourse], user_message: str
) -> list[SessionCourse]:
    """
    第一步：发送学科多选题给 LLM，返回匹配的课程子集。
    若 LLM 返回空或调用失败，回退到全部课程。
    """

def _format_courses_for_step2(self, courses: list[SessionCourse]) -> str:
    """
    第二步专用格式化：仅包含非敏感字段。
    格式: - 序号 | 课程名 | N学分 | 教师 | 周X HH:MM-HH:MM | 地点
    不含: id, capacity, campus, semester, description
    """
```

### LLM Schema

**第一步 Schema**（学科多选题）:
```json
{
  "type": "object",
  "properties": {
    "matched_subjects": {
      "type": "array",
      "items": {"type": "string"},
      "description": "匹配用户需求的学科名称列表，必须从给定列表中选择"
    }
  },
  "required": ["matched_subjects"]
}
```

**第二步 Schema**（复用现有 RECOMMENDATION_SCHEMA，不变）:
```json
{
  "type": "object",
  "properties": {
    "reply": {"type": "string"},
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "plan_name": {"type": "string"},
          "course_ids": {"type": "array", "items": {"type": "string"}},
          "reason": {"type": "string"},
          "match_score": {"type": "number"}
        }
      }
    }
  },
  "required": ["reply", "recommendations"]
}
```

### API 端点（不变）

- `POST /api/v1/conversation/chat` — 无需变更
- `POST /api/v1/conversation/chat/stream` — 无需变更（内部调用 `recommend()`）

错误处理沿用现有模式：ContentFilteredError → 友好提示，其他异常 → FallbackLLMProvider。
