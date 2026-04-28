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
    "课程类别": "category",
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
            "description": "满足用户要求的课程序号列表（0-based 索引）",
        }
    },
    "required": ["matching_indices"],
}


SYSTEM_PROMPT = "你是大学选课推荐助手。根据学生的需求推荐合适的课程。"
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

    def _extract_subjects(self, courses: list[SessionCourse]) -> list[str]:
        """从课程列表中提取所有唯一的学科（category）值，去重排序，过滤空值。"""
        subjects: set[str] = set()
        for c in courses:
            if c.category and c.category.strip():
                subjects.add(c.category.strip())
        return sorted(subjects)

    async def _filter_by_subjects(
        self, courses: list[SessionCourse], user_message: str
    ) -> list[SessionCourse]:
        """第一步：发送学科多选题给 LLM，返回匹配的课程子集。失败时回退到全部课程。"""
        subjects = self._extract_subjects(courses)

        # 无学科可过滤时跳过
        if len(subjects) <= 1:
            logger.info(f"[STEP1_SUBJECTS] subjects_count={len(subjects)}, skipping filter")
            return courses

        subjects_text = "\n".join(f"- {s}" for s in subjects)
        system_prompt = (
            "你是大学选课推荐助手。根据学生的需求，从下方学科列表中选择匹配的学科。\n"
            "重要规则：\n"
            "1. 只能从给定的学科列表中选择，不要返回列表中没有的学科。\n"
            "2. 如果需求不匹配任何学科，返回空列表。\n"
            f"可选学科:\n{subjects_text}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            result = await self.llm.generate_structured(messages, schema=SUBJECT_FILTER_SCHEMA)
            matched = result.get("matched_subjects", [])
            logger.info(f"[STEP1_SUBJECTS] input_subjects={len(subjects)}, matched={matched}")

            if not matched:
                return courses

            # 本地过滤
            matched_set = set(matched)
            filtered = [c for c in courses if c.category and c.category.strip() in matched_set]
            if not filtered:
                logger.warning("[STEP1_SUBJECTS] no courses matched, falling back to all")
                return courses
            return filtered

        except Exception as e:
            logger.warning(f"[STEP1_SUBJECTS] LLM call failed: {type(e).__name__}: {e}, falling back to all courses")
            return courses

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
                elif field == "category" and c.category:
                    parts.append(c.category)
                elif field == "semester" and c.semester:
                    parts.append(c.semester)
                elif field == "description" and c.description:
                    parts.append(c.description[:100])
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    async def _filter_courses(self, user_message: str, courses: list[SessionCourse]) -> list[SessionCourse]:
        """第二步：让 LLM 从精简数据中筛选满足要求的课程，返回匹配的课程列表。"""
        # Step 1: Select relevant fields
        selected_fields = await self._select_fields(user_message)

        # Build reduced dataset
        reduced_data = self._build_reduced_dataset(courses, selected_fields)

        prompt = (
            f"学生的需求是：{user_message}\n\n"
            "请从下方课程列表中筛选满足要求的课程。\n"
            "每行课程以 [序号] 开头。只返回满足要求的课程序号。\n"
            "如果没有课程满足要求，返回空列表。\n\n"
            f"课程列表:\n{reduced_data}"
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            payload_size = sum(len(m["content"]) for m in messages)
            result = await self.llm.generate_structured(messages, schema=FILTER_SCHEMA)
            matching_indices = result.get("matching_indices", [])
            logger.info(f"[STEP2_FILTER] matching_indices={matching_indices}, total_courses={len(courses)}, payload_chars={payload_size}")

            if not matching_indices:
                logger.info("[STEP2_FILTER] empty result, returning empty list")
                return []

            # Resolve indices to full SessionCourse objects
            matched: list[SessionCourse] = []
            for idx in matching_indices:
                if isinstance(idx, int) and 0 <= idx < len(courses):
                    matched.append(courses[idx])
                else:
                    logger.warning(f"[STEP2_FILTER] invalid index: {idx}")

            logger.info(f"[STEP2_FILTER] resolved {len(matched)} courses from {len(matching_indices)} indices")
            return matched

        except Exception as e:
            logger.warning(f"[STEP2_FILTER] LLM call failed: {type(e).__name__}: {e}")
            raise  # Let caller handle fallback

    async def _select_fields(self, user_message: str) -> list[str]:
        """第一步：让 LLM 根据用户需求判断需要哪些字段来过滤课程。"""
        field_names_text = "\n".join(f"- {name}" for name in FIELD_NAME_MAP.keys())
        prompt = (
            f"学生的需求是：{user_message}\n\n"
            "请判断：要满足这个需求，需要查看课程的哪些字段？\n"
            "只选择真正相关的字段，不要选择无关字段。\n"
            "如果需求模糊，则可不返回。\n\n"
            f"可选字段:\n{field_names_text}"
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            payload_size = sum(len(m["content"]) for m in messages)
            result = await self.llm.generate_structured(messages, schema=FIELD_SELECTION_SCHEMA)
            selected_cn = result.get("selected_fields", [])
            logger.info(f"[STEP1_FIELDS] selected_cn={selected_cn}, payload_chars={payload_size}")

            if not selected_cn:
                logger.warning("[STEP1_FIELDS] empty selection, falling back to all fields")
                return list(FIELD_NAME_MAP.values())

            # Map Chinese names to English attribute names
            selected_en = []
            for cn_name in selected_cn:
                en_name = FIELD_NAME_MAP.get(cn_name)
                if en_name:
                    selected_en.append(en_name)
                else:
                    logger.warning(f"[STEP1_FIELDS] unknown field name: {cn_name}")

            if not selected_en:
                logger.warning("[STEP1_FIELDS] no valid fields after mapping, falling back to all")
                return list(FIELD_NAME_MAP.values())

            logger.info(f"[STEP1_FIELDS] selected_en={selected_en}")
            return selected_en

        except Exception as e:
            logger.warning(f"[STEP1_FIELDS] LLM call failed: {type(e).__name__}: {e}, falling back to all fields")
            return list(FIELD_NAME_MAP.values())

    async def recommend(self, user_message: str, context: list[dict] | None = None) -> dict:
        """推荐入口 — 两步决策树过滤，失败时回退到 recommend_legacy。"""
        if not self.session_courses:
            return {
                "reply": "请先上传课表文件，然后再进行选课推荐。",
                "recommendations": [],
            }

        all_courses = self.session_courses

        # Two-step filtering with fallback
        try:
            matched_courses = await self._filter_courses(user_message, all_courses)
        except Exception as e:
            logger.error(f"[RECOMMEND] two-step flow failed: {type(e).__name__}: {e}, falling back to legacy")
            return await self.recommend_legacy(user_message, context)

        # Empty result — no retry
        if not matched_courses:
            return {
                "reply": "抱歉，根据您的需求未找到匹配的课程。请尝试调整描述或放宽条件。",
                "recommendations": [],
            }

        # Build recommendation plan from filtered courses
        plan = await self._build_plan_from_courses(matched_courses)
        if not plan:
            logger.warning("[RECOMMEND] failed to build plan from matched courses, falling back to legacy")
            return await self.recommend_legacy(user_message, context)

        return {
            "reply": f"根据您的需求，筛选出 {len(matched_courses)} 门相关课程。",
            "recommendations": [plan],
        }

    async def _build_plan_from_courses(
        self, courses: list[SessionCourse]
    ) -> RecommendationPlan | None:
        """从筛选后的课程列表构建推荐方案。"""
        if not courses:
            return None

        course_responses = []
        for c in courses:
            course_responses.append(CourseResponse(
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
                category=c.category or "",
                semester=c.semester or "",
                is_active=True,
            ))
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
            plan_name="筛选结果",
            courses=course_responses,
            total_credits=total_credits,
            match_score=0,
            conflicts=conflicts,
        )

    async def recommend_legacy(self, user_message: str, context: list[dict] | None = None) -> dict:
        messages = (context or []) + [{"role": "user", "content": user_message}]

        # Session courses only — no DB fallback
        if not self.session_courses:
            return {
                "reply": "请先上传课表文件，然后再进行选课推荐。",
                "recommendations": [],
            }

        all_courses = self.session_courses

        # Step 1: 学科过滤 — 发送学科列表给 LLM 做多选题
        courses = await self._filter_by_subjects(all_courses, user_message)

        # Step 2 筛选后仍过多时，按关键词相关性排序取 Top N
        if len(courses) > MAX_COURSES_FOR_LLM:
            courses = self._filter_relevant(courses, user_message)

        # Step 2: 使用非敏感字段格式化课程信息
        course_info = self._format_courses_for_step2(courses)

        # Build prompt
        system_prompt = (
            "你是大学选课推荐助手。根据学生的需求，从可用课程中直接推荐选课方案。\n"
            "重要规则：\n"
            "1. 不要追问用户任何信息，直接根据已有条件推荐。\n"
            "2. 推荐的课程之间不能有时间冲突。\n"
            "3. 如果能匹配多个方案则提供多个，如果只能匹配 1-2 个方案则仅提供实际匹配的方案，不要凑数。\n"
            "4. course_ids 必须使用下方课程列表中每行开头的序号值。\n"
            f"可用课程:\n{course_info}\n\n"
            "请为每个方案命名（如'平衡方案'、'兴趣优先'），并说明推荐理由和匹配度评分（0-100）。"
        )
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # Step 2 logging
        logger.info(f"[STEP2_FILTER] sending {len(courses)} courses to LLM (from {len(all_courses)} total)")

        # Call LLM
        try:
            result = await self.llm.generate_structured(full_messages, schema=RECOMMENDATION_SCHEMA)
        except Exception as e:
            logger.error(f"[RECOMMEND_FAIL] generate_structured failed: {type(e).__name__}: {e}", exc_info=True)
            raise

        # Parse recommendations
        recommendations = []
        for rec in result.get("recommendations", []):
            plan = await self._build_recommendation_plan(rec, courses)
            if plan:
                recommendations.append(plan)

        # 第二步无匹配结果时返回友好提示，不做额外降级
        if not recommendations:
            logger.info("[STEP2_FILTER] no recommendations matched, returning empty")
            return {
                "reply": result.get("reply") or "抱歉，根据您的需求未找到匹配的课程。请尝试调整描述或放宽条件。",
                "recommendations": [],
            }

        return {
            "reply": result.get("reply", "抱歉，无法生成推荐"),
            "recommendations": recommendations,
        }

    # Stop words that appear in almost all course names
    _STOP_WORDS = {"课程", "推荐", "选课", "课", "学", "的", "了", "是", "在", "有", "和"}

    def _filter_relevant(
        self, courses: list[SessionCourse], user_message: str
    ) -> list[SessionCourse]:
        """Filter courses by keyword relevance when total exceeds MAX_COURSES_FOR_LLM."""
        import re

        # Extract keywords: English words + Chinese bigrams/trigrams
        keywords = set()
        # English words
        for token in re.findall(r"[a-zA-Z]{2,}", user_message):
            keywords.add(token.lower())
        # Chinese: extract all chars, then generate bigrams + trigrams
        cn_chars = re.findall(r"[一-鿿]", user_message)
        cn_text = "".join(cn_chars)
        # Also check full Chinese tokens (e.g., "计算机" from "推荐计算机课程")
        for token in re.findall(r"[一-鿿]{2,}", user_message):
            if token not in self._STOP_WORDS:
                keywords.add(token)
        # Generate sub-segments: try sliding windows of 2-4 chars on full Chinese text
        for length in (2, 3, 4):
            for i in range(len(cn_text) - length + 1):
                seg = cn_text[i : i + length]
                if seg not in self._STOP_WORDS:
                    keywords.add(seg)

        if not keywords:
            return courses[: MAX_COURSES_FOR_LLM]

        # Score courses by keyword match
        scored: list[tuple[int, SessionCourse]] = []
        for c in courses:
            score = 0
            searchable = f"{c.name} {c.course_no or ''} {c.category or ''} {c.instructor or ''} {c.description or ''}".lower()
            for kw in keywords:
                if kw in searchable:
                    score += 1
            scored.append((score, c))

        # Sort by score descending, take top MAX
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [c for _, c in scored[: MAX_COURSES_FOR_LLM]]

        # If no keyword matched at all, return first MAX (don't return empty)
        if scored and scored[0][0] == 0:
            return courses[: MAX_COURSES_FOR_LLM]

        return result

    def _format_session_courses_for_llm(self, courses: list[SessionCourse]) -> str:
        day_names = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
        lines = []
        for c in courses:
            schedule_str = ""
            if c.schedule:
                schedule_str = ", ".join(
                    f"周{day_names.get(s.day_of_week, '?')}({s.start_period}-{s.end_period}节)"
                    for s in c.schedule
                )
            parts = [f"- id:{c.id} {c.name}"]
            if c.course_no:
                parts[0] += f"（{c.course_no}）"
            parts.append(f"{c.credit}学分")
            if c.instructor:
                parts.append(c.instructor)
            if schedule_str:
                parts.append(schedule_str)
            if c.location:
                parts.append(c.location)
            if c.category:
                parts.append(c.category)
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    def _format_courses_for_step2(self, courses: list[SessionCourse]) -> str:
        """第二步专用格式化：仅包含非敏感字段。不含 id/capacity/campus/semester/description。"""
        day_names = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
        lines = []
        for c in courses:
            schedule_str = ""
            if c.schedule:
                schedule_str = ", ".join(
                    f"周{day_names.get(s.day_of_week, '?')}({s.start_period}-{s.end_period}节)"
                    for s in c.schedule
                )
            # 使用序号(course_no)作为标识，不含内部 id
            identifier = c.course_no or c.id or c.name
            parts = [f"- {identifier} {c.name}"]
            parts.append(f"{c.credit}学分")
            if c.instructor:
                parts.append(c.instructor)
            if schedule_str:
                parts.append(schedule_str)
            if c.location:
                parts.append(c.location)
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    async def _build_recommendation_plan(
        self, rec: dict, courses: list[SessionCourse]
    ) -> RecommendationPlan | None:
        course_ids = rec.get("course_ids", [])
        if not course_ids:
            return None

        matched = []
        for c in courses:
            for cid in course_ids:
                # Exact ID match
                if c.id and str(c.id) == cid:
                    matched.append(c)
                    break
                # Exact name match
                if c.name == cid:
                    matched.append(c)
                    break
                # Course number match
                if c.course_no and c.course_no == cid:
                    matched.append(c)
                    break
                # Partial name match: LLM returns "篮球" for "体育（篮球）"
                if cid in c.name or c.name in cid:
                    matched.append(c)
                    break
        if not matched:
            return None

        # Convert session courses to CourseResponse with full snapshot
        course_responses = []
        for c in matched:
            course_responses.append(CourseResponse(
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
                category=c.category or "",
                semester=c.semester or "",
                is_active=True,
            ))
        total_credits = sum(c.credit for c in matched)

        # Run conflict detection on matched courses
        conflict_dicts = [cr.model_dump() for cr in course_responses]
        conflicts = []
        try:
            conflicts.extend(detect_time_conflicts(conflict_dicts))
            conflicts.extend(detect_commute_conflicts(conflict_dicts))
        except Exception as e:
            logger.warning(f"Conflict detection failed: {e}")

        return RecommendationPlan(
            plan_name=rec.get("plan_name", "推荐方案"),
            courses=course_responses,
            total_credits=total_credits,
            match_score=rec.get("match_score", 0),
            conflicts=conflicts,
        )
