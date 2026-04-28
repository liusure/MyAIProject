import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.plan import RecommendationPlan
from src.schemas.course import CourseResponse, ScheduleItem, SessionCourse
from src.services.llm.base import LLMProvider
from src.services.conflict.time import detect_time_conflicts
from src.services.conflict.commute import detect_commute_conflicts

logger = logging.getLogger(__name__)

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string", "description": "给学生的自然语言回复"},
        "recommendations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "plan_name": {"type": "string"},
                    "course_ids": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                    "match_score": {"type": "number"},
                },
            },
        },
    },
    "required": ["reply", "recommendations"],
}

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
        "reason": {
            "type": "string",
            "description": "推荐这些课程的理由，简要说明为什么它们匹配用户的需求",
        },
    },
    "required": ["matching_indices"],
}

MAX_COURSES_FOR_LLM = 200


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

    async def _filter_courses(self, user_message: str, courses: list[SessionCourse]) -> tuple[list[SessionCourse], str]:
        # Step 1: Select relevant fields
        selected_fields = await self._select_fields(user_message)

        # Step 1.5: If subject is selected, pre-filter locally to reduce dataset
        if "subject" in selected_fields:
            subjects = self._extract_subjects(courses)
            if len(subjects) > 1:
                matched_subjects = await self._match_subjects(user_message, subjects)
                if matched_subjects:
                    courses = [c for c in courses if c.subject and c.subject.strip() in matched_subjects]
                    logger.info(
                        f"[PRE_FILTER] subject filter: {len(courses)} courses after filtering by {matched_subjects}")

        # Build reduced dataset
        reduced_data = self._build_reduced_dataset(courses, selected_fields)

        prompt = (
            f"学生的需求是：{user_message}\n\n"
            "请从下方课程列表中筛选满足要求的课程。\n"
            "每行课程以 [序号] 开头。只返回满足要求的课程序号。\n"
            "如果需求模糊，结合课程名称和常识自行判断。\n\n"
            "如果没有课程满足要求，返回空列表。\n\n"
            "严格要求：最多返回20个课程序号，按相关度从高到低排序。不要返回超过20个。\n\n"
            "同时请在 reason 字段中简要说明推荐这些课程的理由，"
            "说明为什么它们匹配学生的需求（2-3句话）。\n\n"
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
            logger.info(
                f"[STEP2_FILTER] matching_indices={matching_indices}, total_courses={len(courses)}, "
                f"payload_chars={payload_size}, has_reason={bool(reason)}")

            if not matching_indices:
                logger.info("[STEP2_FILTER] empty result, returning empty list")
                return [], reason

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
            return matched, reason

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
            "我将会分两步发送给你需要的数据，第一步由你判断所需字段，第二步按你的回复返回对应字段，最终由你返回推荐课程序号\n\n"
            "注意这是一张周课程表，因此不要返回过多内容，不要返回有时间冲突的课程\n\n"
            f"学生的需求是：{user_message}\n\n"
            "请判断：要满足这个需求，需要查看课程的哪些字段？\n"
            "只选择真正相关的字段，不要选择无关字段。\n"
            "如果需求模糊，则可不返回。\n\n"
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

    async def recommend(self, user_message: str, context: list[dict] | None = None) -> dict:
        """推荐入口 — 两步决策树过滤。"""
        if not self.session_courses:
            return {
                "reply": "请先上传课表文件，然后再进行选课推荐。",
                "recommendations": [],
            }

        matched_courses, reason = await self._filter_courses(user_message, self.session_courses)

        if not matched_courses:
            return {
                "reply": "抱歉，根据您的需求未找到匹配的课程。请尝试调整描述或放宽条件。",
                "recommendations": [],
            }

        plan = await self._build_plan_from_courses(matched_courses)
        reply = reason if reason else f"根据您的需求，筛选出 {len(matched_courses)} 门相关课程。"
        return {
            "reply": reply,
            "recommendations": [plan],
        }

    async def _build_plan_from_courses(
            self, courses: list[SessionCourse]
    ) -> RecommendationPlan | None:
        """从筛选后的课程列表构建推荐方案（两步过滤结果）。"""
        if not courses:
            return None
        return self._courses_to_plan(courses, plan_name="筛选结果")

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

    @staticmethod
    def _match_courses_by_ids(
            course_ids: list[str], courses: list[SessionCourse]
    ) -> list[SessionCourse]:
        """根据 LLM 返回的 course_ids 从课程列表中匹配课程。"""
        matched = []
        for c in courses:
            for cid in course_ids:
                if c.id and str(c.id) == cid:
                    matched.append(c)
                    break
                if c.name == cid:
                    matched.append(c)
                    break
                if c.course_no and c.course_no == cid:
                    matched.append(c)
                    break
                if cid in c.name or c.name in cid:
                    matched.append(c)
                    break
        return matched

    async def _build_recommendation_plan(
            self, rec: dict, courses: list[SessionCourse]
    ) -> RecommendationPlan | None:
        course_ids = rec.get("course_ids", [])
        if not course_ids:
            return None

        matched = self._match_courses_by_ids(course_ids, courses)
        if not matched:
            return None

        return self._courses_to_plan(
            matched,
            plan_name=rec.get("plan_name", "推荐方案"),
            match_score=rec.get("match_score", 0),
        )
