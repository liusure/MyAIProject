import uuid
import logging
from collections.abc import AsyncIterator, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.plan import RecommendationPlan
from src.schemas.course import CourseResponse, ScheduleItem, SessionCourse
from src.services.llm.base import LLMProvider
from src.services.conflict.time import detect_time_conflicts
from src.services.conflict.commute import detect_commute_conflicts

logger = logging.getLogger(__name__)

SUBJECT_FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "matched_subjects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "匹配用户需求的学科名称列表，必须从给定列表中选择",
        },
    },
    "required": ["matched_subjects"],
}

# T001: Chinese → English field name mapping for two-step filtering
FIELD_NAME_MAP: dict[str, str] = {
    "课程名称": "name",
    "课程编号": "course_no",
    "学分": "credit",
    "教师": "instructor",
    "容量": "capacity",
    "上课时间": "schedule",
    "地点": "location",
    "校区": "campus",
    "学科": "subject",
    "课程属性": "category",
    "学期": "semester",
    "课程描述": "description",
}

# T002: Schema for step 1 — LLM selects relevant fields from enum
FIELD_SELECTION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "selected_fields": {
            "type": "array",
            "items": {"type": "string", "enum": list(FIELD_NAME_MAP.keys())},
            "description": "与用户需求相关的课程字段名称列表，必须从给定列表中选择",
            "minItems": 1,
        }
    },
    "required": ["selected_fields"],
}

# T003: Schema for step 2 — LLM returns matching course indices
FILTER_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "matching_indices": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "满足用户要求的课程序号列表（0-based 索引），最多20个，按相关度排序",
            "maxItems": 20,
        },
        "plan_name": {
            "type": "string",
            "description": "推荐课程方案的名称",
        },
        "reason": {
            "type": "string",
            "description": "推荐这些课程的理由，简要说明为什么它们匹配用户的需求",
        },
        "match_score": {
            "type": "number",
            "description": "推荐结果与用户需求的匹配程度，0-100之间的整数",
            "minimum": 0,
            "maximum": 100,
        },
    },
    "required": ["matching_indices"],
}

MAX_COURSES_FOR_LLM = 200

# T004: Merged schema for combined field selection + subject matching
FIELD_SUBJECT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "selected_fields": {
            "type": "array",
            "items": {"type": "string", "enum": list(FIELD_NAME_MAP.keys())},
            "description": "与用户需求相关的课程字段名称列表，必须从给定列表中选择",
            "minItems": 1,
        },
        "matched_subjects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "匹配用户需求的学科名称列表，必须从给定列表中选择。如果需求不涉及特定学科或未选择学科字段，返回空列表",
        },
    },
    "required": ["selected_fields"],
}


class RecommendService:
    """选课推荐服务 — 两步决策树过滤"""

    def __init__(
            self,
            db: AsyncSession,
            llm: LLMProvider,
            session_courses: list[SessionCourse] | None = None,
    ) -> None:
        self.db = db
        self.llm = llm
        self.session_courses = session_courses

    def _build_reduced_dataset(self, courses: list[SessionCourse], fields: list[str]) -> str:
        """第二步数据准备：固定包含序号+课程名称+上课时间，再加上LLM选出的字段。"""
        day_names = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}

        # 固定字段：课程名称、上课时间。从 LLM 选出的字段中去掉重复的
        extra_fields = [f for f in fields if f not in ("name", "schedule")]

        lines: list[str] = []
        for idx, c in enumerate(courses):
            parts = [f"[{idx}]"]

            # 固定：课程名称
            parts.append(c.name)

            # 固定：上课时间
            if c.schedule:
                schedule_str = ", ".join(
                    f"周{day_names.get(s.day_of_week, '?')}({s.start_period}-{s.end_period}节)"
                    for s in c.schedule
                )
                parts.append(schedule_str)

            # LLM 选出的额外字段
            for field in extra_fields:
                if field == "course_no" and c.course_no:
                    parts.append(f"编号:{c.course_no}")
                elif field == "credit":
                    parts.append(f"{c.credit}学分")
                elif field == "instructor" and c.instructor:
                    parts.append(c.instructor)
                elif field == "capacity" and c.capacity:
                    parts.append(f"容量:{c.capacity}")
                elif field == "location" and c.location:
                    parts.append(c.location)
                elif field == "campus" and c.campus:
                    parts.append(c.campus)
                elif field == "subject" and c.subject:
                    parts.append(c.subject)
                elif field == "category" and c.category:
                    parts.append(c.category)
                elif field == "semester" and c.semester:
                    parts.append(c.semester)
                elif field == "description" and c.description:
                    parts.append(c.description[:100])
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    @staticmethod
    def _extract_subjects(courses: list[SessionCourse]) -> list[str]:
        """从课程列表中提取所有唯一的学科（category）值，去重排序，过滤空值。"""
        subjects: set[str] = set()
        for c in courses:
            if c.subject and c.subject.strip():
                subjects.add(c.subject.strip())
        return sorted(subjects)

    async def _filter_courses(self, user_message: str, courses: list[SessionCourse]) -> tuple[list[SessionCourse], str, int]:
        # Step 1 (merged): Select relevant fields AND match subjects in one LLM call
        subjects = self._extract_subjects(courses)
        selected_fields, matched_subjects = await self._select_fields_and_subjects(user_message, subjects)

        # Pre-filter by matched subjects if applicable
        if "subject" in selected_fields and matched_subjects:
            filtered = [c for c in courses if c.subject and c.subject.strip() in matched_subjects]
            if filtered:
                courses = filtered
                logger.info(f"[PRE_FILTER] subject filter: {len(courses)} courses after filtering by {matched_subjects}")

        # Build reduced dataset
        reduced_data = self._build_reduced_dataset(courses, selected_fields)

        prompt = (
            f"学生的需求是：{user_message}\n\n"
            "请从下方课程列表中筛选满足要求的课程。\n"
            "每行课程以 [序号] 开头。返回满足要求的课程序号。\n"
            "如果没有课程满足要求，返回空列表。\n\n"
            "严格要求：最多返回20个课程序号，按相关度从高到低排序。不要返回超过20个。\n\n"
            "同时请在 plan_name 字段中为方案起一个名字 reason 字段中简要说明推荐这些课程的理由，并在 match_score 字段给出你对推荐结果与学生需求匹配程度的评分（0-100）。\n\n"
            f"课程列表:\n{reduced_data}"
        )
        messages = [
            {"role": "user", "content": prompt},
        ]

        try:
            payload_size = sum(len(m["content"]) for m in messages)
            result = await self.llm.generate_structured(messages, schema=FILTER_SCHEMA)
            matching_indices = result.get("matching_indices", [])
            reason = result.get("reason", "")
            match_score = int(result.get("match_score", 0))
            logger.info(
                f"[STEP2_FILTER] matching_indices={matching_indices}, total_courses={len(courses)}, "
                f"payload_chars={payload_size}, has_reason={bool(reason)}, match_score={match_score}")

            if not matching_indices:
                logger.info("[STEP2_FILTER] empty result, returning empty list")
                return [], reason, match_score

            # Deduplicate indices (LLM may return duplicates)
            unique_indices = list(dict.fromkeys(matching_indices))

            # Hard limit: cap at 20 courses
            if len(unique_indices) > 20:
                logger.warning(f"[STEP2_FILTER] LLM returned {len(unique_indices)} indices, capping to 20")
                unique_indices = unique_indices[:20]

            # Resolve indices to full SessionCourse objects
            matched: list[SessionCourse] = []
            for idx in unique_indices:
                if isinstance(idx, int) and 0 <= idx < len(courses):
                    matched.append(courses[idx])
                else:
                    logger.warning(f"[STEP2_FILTER] invalid index: {idx}")

            logger.info(f"[STEP2_FILTER] resolved {len(matched)} courses from {len(matching_indices)} indices")
            return matched, reason, match_score

        except Exception as e:
            logger.warning(f"[STEP2_FILTER] LLM call failed: {type(e).__name__}: {e}")
            raise  # Let caller handle fallback

    async def _match_subjects(self, user_message: str, subjects: list[str]) -> set[str]:
        """让 LLM 从学科列表中选择匹配的学科，用于预过滤。"""
        subjects_text = "\n".join(f"- {s}" for s in subjects)
        prompt = (
            f"学生的需求是：{user_message}\n\n"
            f"请从以下学科列表中选择与需求相关的学科。只返回匹配的学科名称。\n"
            f"如果需求不涉及特定学科，返回空列表。\n\n"
            f"可选学科:\n{subjects_text}"
        )
        messages = [{"role": "user", "content": prompt}]

        try:
            result = await self.llm.generate_structured(messages, schema=SUBJECT_FILTER_SCHEMA)
            matched = result.get("matched_subjects", [])
            logger.info(f"[MATCH_SUBJECTS] matched={matched}")
            return set(matched) if matched else set()
        except Exception as e:
            logger.warning(f"[MATCH_SUBJECTS] LLM call failed: {e}")
            return set()

    async def _select_fields(self, user_message: str) -> list[str]:
        """第一步：让 LLM 根据用户需求判断需要哪些字段来过滤课程。"""
        field_names_text = "\n".join(f"- {name}" for name in FIELD_NAME_MAP.keys())
        prompt = (
            "你是一个课程选择助手，你需要帮助学生选择满足需求，时间无冲突，课程规划合理的课程表。\n\n"
            "不要返回有时间冲突的课程\n\n"
            f"学生的需求是：{user_message}\n\n"
            "请判断：要满足这个需求，需要查看课程的哪些字段？\n"
            "只选择真正相关的字段，不要选择无关字段。\n"
            f"可选字段:\n{field_names_text}"
        )
        messages = [
            {"role": "user", "content": prompt},
        ]
        logger.info(f"{prompt}")
        try:
            payload_size = sum(len(m["content"]) for m in messages)
            result = await self.llm.generate_structured(messages, schema=FIELD_SELECTION_SCHEMA)
            selected_cn = result.get("selected_fields", [])
            logger.info(f"[STEP1_FIELDS] selected_cn={selected_cn}, payload_chars={payload_size}")

            # Map Chinese names to English attribute names
            selected_en = []
            for cn_name in selected_cn:
                en_name = FIELD_NAME_MAP.get(cn_name)
                if en_name:
                    selected_en.append(en_name)
                else:
                    logger.warning(f"[STEP1_FIELDS] unknown field name: {cn_name}")

            logger.info(f"[STEP1_FIELDS] selected_en={selected_en}")
            return selected_en

        except Exception as e:
            logger.warning(f"[STEP1_FIELDS] LLM call failed: {type(e).__name__}: {e}, falling back to all fields")
            return []

    async def _select_fields_and_subjects(
        self, user_message: str, subjects: list[str]
    ) -> tuple[list[str], set[str]]:
        """合并步骤：让 LLM 同时选择相关字段和匹配学科，减少一次 LLM 调用。"""
        field_names_text = "\n".join(f"- {name}" for name in FIELD_NAME_MAP.keys())
        subjects_text = "\n".join(f"- {s}" for s in subjects)
        prompt = (
            "你是一个课程选择助手，你需要帮助学生选择满足需求，时间无冲突，课程规划合理的课程表。\n\n"
            "不要返回有时间冲突的课程\n\n"
            f"学生的需求是：{user_message}\n\n"
            "请判断：\n"
            "1. 要满足这个需求，需要查看课程的哪些字段？只选择真正相关的字段。\n"
            "2. 从下方学科列表中选择与需求相关的学科。如果需求不涉及特定学科，返回空列表。\n\n"
            f"可选字段:\n{field_names_text}\n\n"
            f"可选学科:\n{subjects_text}"
        )
        messages = [{"role": "user", "content": prompt}]
        logger.info(f"[MERGED_STEP] prompt_chars={len(prompt)}")

        try:
            result = await self.llm.generate_structured(messages, schema=FIELD_SUBJECT_SCHEMA)
            selected_cn = result.get("selected_fields", [])
            matched = result.get("matched_subjects", [])
            logger.info(f"[MERGED_STEP] selected_cn={selected_cn}, matched_subjects={matched}")

            # Map Chinese names to English attribute names
            selected_en = []
            for cn_name in selected_cn:
                en_name = FIELD_NAME_MAP.get(cn_name)
                if en_name:
                    selected_en.append(en_name)
                else:
                    logger.warning(f"[MERGED_STEP] unknown field name: {cn_name}")

            logger.info(f"[MERGED_STEP] selected_en={selected_en}")
            return selected_en, set(matched) if matched else set()

        except Exception as e:
            logger.warning(f"[MERGED_STEP] LLM call failed: {type(e).__name__}: {e}, falling back")
            return [], set()

    async def recommend(self, user_message: str, context: list[dict] | None = None) -> dict:
        """推荐入口 — 两步决策树过滤。"""
        if not self.session_courses:
            return {
                "reply": "请先上传课表文件，然后再进行选课推荐。",
                "recommendations": [],
            }

        matched_courses, reason, match_score = await self._filter_courses(user_message, self.session_courses)

        if not matched_courses:
            return {
                "reply": "抱歉，根据您的需求未找到匹配的课程。请尝试调整描述或放宽条件。",
                "recommendations": [],
            }

        plan = await self._build_plan_from_courses(matched_courses, match_score=match_score)
        reply = reason if reason else f"根据您的需求，筛选出 {len(matched_courses)} 门相关课程。"
        return {
            "reply": reply,
            "recommendations": [plan],
        }

    async def recommend_stream(
        self,
        user_message: str,
        context: list[dict] | None = None,
        on_progress: "Callable[[str, str], Awaitable[None]] | None" = None,
    ) -> tuple[dict, AsyncIterator[str]]:
        """推荐入口（流式版）— 返回 (结构化结果, 流式回复文字迭代器)。

        结构化结果包含 recommendations、conflicts 等数据。
        流式迭代器逐块产出回复文字。
        """
        if not self.session_courses:
            result = {
                "reply": "请先上传课表文件，然后再进行选课推荐。",
                "recommendations": [],
            }
            async def _empty():
                if False:
                    yield ""
            return result, _empty()

        # Progress: analyzing
        if on_progress:
            await on_progress("analyzing", "正在分析你的选课偏好...")

        subjects = self._extract_subjects(self.session_courses)
        selected_fields, matched_subjects = await self._select_fields_and_subjects(user_message, subjects)

        # Progress: filtering with identified conditions
        if on_progress:
            field_names = ", ".join(selected_fields) if selected_fields else "全部"
            subject_info = ", ".join(sorted(matched_subjects)) if matched_subjects else "不限"
            await on_progress("filtering", f"已识别筛选条件：字段={field_names}，学科={subject_info}")

        # Pre-filter by subjects
        courses = self.session_courses
        if "subject" in selected_fields and matched_subjects:
            filtered = [c for c in courses if c.subject and c.subject.strip() in matched_subjects]
            if filtered:
                courses = filtered

        # Progress: building
        if on_progress:
            await on_progress("building", f"在 {len(courses)} 门课中筛选匹配方案...")

        # Step 2: Filter courses
        reduced_data = self._build_reduced_dataset(courses, selected_fields)
        prompt = (
            f"学生的需求是：{user_message}\n\n"
            "请从下方课程列表中筛选满足要求的课程。\n"
            "每行课程以 [序号] 开头。返回满足要求的课程序号。\n"
            "如果没有课程满足要求，返回空列表。\n\n"
            "严格要求：最多返回20个课程序号，按相关度从高到低排序。不要返回超过20个。\n\n"
            "同时请在 plan_name 字段中为方案起一个名字 reason 字段中简要说明推荐这些课程的理由，并在 match_score 字段给出你对推荐结果与学生需求匹配程度的评分（0-100）。\n\n"
            f"课程列表:\n{reduced_data}"
        )
        messages = [{"role": "user", "content": prompt}]

        try:
            result_data = await self.llm.generate_structured(messages, schema=FILTER_SCHEMA)
            matching_indices = result_data.get("matching_indices", [])
            reason = result_data.get("reason", "")
            match_score = int(result_data.get("match_score", 0))
        except Exception as e:
            logger.warning(f"[STREAM_FILTER] LLM call failed: {type(e).__name__}: {e}")
            raise

        if not matching_indices:
            result = {
                "reply": "抱歉，根据您的需求未找到匹配的课程。请尝试调整描述或放宽条件。",
                "recommendations": [],
            }
            async def _empty2():
                if False:
                    yield ""
            return result, _empty2()

        # Resolve indices
        unique_indices = list(dict.fromkeys(matching_indices))
        if len(unique_indices) > 20:
            unique_indices = unique_indices[:20]
        matched: list[SessionCourse] = []
        for idx in unique_indices:
            if isinstance(idx, int) and 0 <= idx < len(courses):
                matched.append(courses[idx])

        plan = await self._build_plan_from_courses(matched, match_score=match_score)
        reply_text = reason if reason else f"根据您的需求，筛选出 {len(matched)} 门相关课程。"

        result = {
            "reply": reply_text,
            "recommendations": [plan],
        }

        # Create streaming iterator for the reply text
        async def _stream_reply():
            yield reply_text

        return result, _stream_reply()

    async def _build_plan_from_courses(
            self, courses: list[SessionCourse], match_score: int = 0
    ) -> RecommendationPlan | None:
        """从筛选后的课程列表构建推荐方案（两步过滤结果）。"""
        if not courses:
            return None
        return self._courses_to_plan(courses, plan_name="筛选结果", match_score=match_score)

    @staticmethod
    def _courses_to_plan(
            courses: list[SessionCourse],
            plan_name: str = "推荐方案",
            match_score: int = 0,
    ) -> RecommendationPlan:
        """将 SessionCourse 列表转为 RecommendationPlan（含冲突检测）。"""
        course_responses = [
            CourseResponse(
                id=uuid.UUID(c.id) if c.id else uuid.uuid4(),
                course_no=c.course_no or "",
                name=c.name,
                credit=c.credit,
                instructor=c.instructor or "",
                capacity=c.capacity or 0,
                schedule=[
                    ScheduleItem(
                        day_of_week=s.day_of_week,
                        start_period=s.start_period,
                        end_period=s.end_period,
                        weeks=s.weeks,
                    )
                    for s in (c.schedule or [])
                ],
                location=c.location or "",
                campus=c.campus or "",
                subject=c.subject or "",
                category=c.category or "",
                semester=c.semester or "",
                is_active=True,
            )
            for c in courses
        ]
        total_credits = sum(c.credit for c in courses)

        # Run conflict detection
        conflict_dicts = [cr.model_dump() for cr in course_responses]
        conflicts = []
        try:
            conflicts.extend(detect_time_conflicts(conflict_dicts))
            conflicts.extend(detect_commute_conflicts(conflict_dicts))
        except Exception as e:
            logger.warning(f"Conflict detection failed: {e}")

        return RecommendationPlan(
            plan_name=plan_name,
            courses=course_responses,
            total_credits=total_credits,
            match_score=match_score,
            conflicts=conflicts,
        )

