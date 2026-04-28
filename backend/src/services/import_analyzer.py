"""Import analyzer: LLM column mapping. Always sends headers to LLM for matching."""
import io
import json
import logging

import pandas as pd

from src.schemas.import_result import (
    ColumnMapping,
    DegradationImpact,
    DegradationReport,
    MappingResult,
)
from src.services.field_normalizer import FIELD_DEFINITIONS

logger = logging.getLogger(__name__)

COLUMN_MAPPING_SCHEMA = {
    "type": "object",
    "properties": {
        "mappings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "文件中的原始列名"},
                    "target": {"type": "string", "description": "系统字段key"},
                },
                "required": ["source", "target"],
            },
        }
    },
    "required": ["mappings"],
}

DEGRADATION_IMPACTS: dict[str, DegradationImpact] = {
    "course_no": DegradationImpact(field="course_no", impact="无法通过编号精确匹配课程", fallback="将使用课程名称去重"),
    "instructor": DegradationImpact(field="instructor", impact="无法按教师筛选推荐", fallback="跳过教师筛选"),
    "capacity": DegradationImpact(field="capacity", impact="无法显示课程容量", fallback="容量信息不可用"),
    "location": DegradationImpact(field="location", impact="无法显示上课地点", fallback="地点信息不可用"),
    "campus": DegradationImpact(field="campus", impact="无法检测跨校区通勤冲突", fallback="跳过通勤检测"),
    "category": DegradationImpact(field="category", impact="无法按分类筛选", fallback="将根据课程名称自动推断分类"),
    "semester": DegradationImpact(field="semester", impact="无法按学期筛选", fallback="跳过学期筛选"),
    "schedule": DegradationImpact(field="schedule", impact="无法检测时间冲突", fallback="课程将标记为'时间未指定'"),
}

# System fields description for LLM — no hardcoded aliases
SYSTEM_FIELDS_DESC = {
    "name": "课程名称（如：课程名称、课程名、course name）",
    "credit": "学分/课时（如：学分、课时/学分、credit）",
    "course_no": "课程编号/序号/编码（如：课程编码、课号、序号）",
    "instructor": "授课教师/主讲人（如：主讲教师、首席教授、任课老师）",
    "capacity": "选课人数上限/容量（如：限选人数、最大人数）",
    "location": "上课地点/教室（如：教室、教学楼）",
    "campus": "校区（如：校区、院区）",
    "category": "课程分类/属性/类型（如：课程属性、课程类型）",
    "semester": "开课学期/学年（如：开课学期、学年学期）",
    "schedule": "上课时间/星期节次（如：上课时间、开课时间）",
    "weeks": "开课周/周次（如：开课周、第1-12周）",
}


class ImportAnalyzer:
    """Analyzes Excel file columns and produces mapping via LLM."""

    @classmethod
    async def analyze(cls, file_bytes: bytes, filename: str) -> tuple[MappingResult, list[dict]]:
        """Analyze file and return (mapping_result, raw_data_as_dicts).

        Always uses LLM for column matching. Falls back to empty mapping if LLM unavailable.
        """
        raw_data, columns = cls._read_raw(file_bytes, filename)

        if not columns:
            raise ValueError("文件不含任何列")

        # Split compound headers (e.g., "课时/学分" → "课时" + "学分")
        raw_data, columns = cls._split_compound_headers(raw_data, columns)

        try:
            mapping = await cls._llm_analyze(columns, raw_data)
            mapping = cls._deduplicate_mapping(mapping)
            return mapping, raw_data
        except Exception as e:
            logger.error(
                f"LLM column mapping failed: {e}. "
                f"请检查 MIMO_API_KEY 和 MIMO_API_BASE_URL 是否已在 .env 中正确配置。"
            )
            raise ValueError(f"列映射失败：LLM 服务不可用。请确认 API 密钥已配置。原始错误: {e}")

    @classmethod
    def _read_raw(cls, file_bytes: bytes, filename: str) -> tuple[list[dict], list[str]]:
        """Read file into list of dicts with original column names."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

        columns = [str(c).strip() for c in df.columns]
        df.columns = columns
        records = df.where(pd.notna(df), None).to_dict(orient="records")
        return records, columns

    @classmethod
    def _split_compound_headers(
        cls, raw_data: list[dict], columns: list[str]
    ) -> tuple[list[dict], list[str]]:
        """Split compound headers containing '/' into separate columns.

        e.g., "课时/学分" → two columns "课时" and "学分"
        Values like "48/3" are split correspondingly.
        Single values (no '/') are assigned to the first sub-column.
        """
        # Build split plan: for each original column, what new columns it produces
        split_plan: list[tuple[list[str], bool]] = []  # (new_col_names, is_compound)
        has_compound = False

        for col in columns:
            if "/" in col and not col.startswith("http"):
                parts = [p.strip() for p in col.split("/", 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    split_plan.append(([parts[0], parts[1]], True))
                    has_compound = True
                    logger.info(f"Compound header split: '{col}' → '{parts[0]}' + '{parts[1]}'")
                    continue
            split_plan.append(([col], False))

        if not has_compound:
            return raw_data, columns

        # Build new column list
        new_columns = [name for names, _ in split_plan for name in names]

        # Rebuild raw_data
        new_raw_data: list[dict] = []
        for row in raw_data:
            new_row: dict = {}
            for i, (orig_col, (new_names, is_compound)) in enumerate(zip(columns, split_plan)):
                if is_compound:
                    raw_val = row.get(orig_col)
                    raw_str = str(raw_val).strip() if raw_val is not None else ""
                    if "/" in raw_str:
                        val_parts = raw_str.split("/", 1)
                        new_row[new_names[0]] = val_parts[0].strip() or None
                        new_row[new_names[1]] = val_parts[1].strip() or None
                    else:
                        # No slash in value — assign to first sub-column
                        new_row[new_names[0]] = raw_str or None
                        new_row[new_names[1]] = None
                else:
                    new_row[new_names[0]] = row.get(orig_col)
            new_raw_data.append(new_row)

        return new_raw_data, new_columns

    @classmethod
    def _deduplicate_mapping(cls, mapping: MappingResult) -> MappingResult:
        """When multiple source columns map to the same target, keep the best match.

        For compound header splits (e.g., "课时" and "学分" both → credit),
        prefer the column whose name most closely matches the target field's aliases.
        """
        from src.services.field_normalizer import FIELD_DEFINITIONS

        # Group mappings by target
        target_groups: dict[str, list[ColumnMapping]] = {}
        for m in mapping.mappings:
            target_groups.setdefault(m.target, []).append(m)

        deduped: list[ColumnMapping] = []
        for target, group in target_groups.items():
            if len(group) == 1:
                deduped.append(group[0])
            else:
                # Pick best: column name matches target field aliases
                aliases = FIELD_DEFINITIONS.get(target)
                if aliases:
                    alias_set = set(aliases.aliases)
                    best = max(group, key=lambda m: max(
                        (len(a) for a in alias_set if a in m.source.lower()),
                        default=0,
                    ))
                    deduped.append(best)
                    demoted = [m.source for m in group if m != best]
                    if demoted:
                        logger.info(f"Mapping dedup: '{best.source}'→{target}, demoted: {demoted}")
                else:
                    # No aliases to compare, keep first
                    deduped.append(group[0])

        mapped_targets = {m.target for m in deduped}
        return MappingResult(
            mappings=deduped,
            unmapped_source=mapping.unmapped_source,
            unmapped_target=[k for k in SYSTEM_FIELDS_DESC if k not in mapped_targets],
        )

    @classmethod
    async def _llm_analyze(cls, columns: list[str], raw_data: list[dict]) -> MappingResult:
        """Send system fields + file headers + sample data to LLM for matching."""
        from src.services.llm.factory import LLMFactory

        # Build field list for LLM — just labels, no hardcoded aliases
        field_lines = "\n".join(
            f"  {key} — {desc}"
            for key, desc in SYSTEM_FIELDS_DESC.items()
        )

        # Sample rows within token budget
        sample_rows = raw_data[:3]
        sample_text = json.dumps(sample_rows, ensure_ascii=False, default=str)

        prompt = (
            f"我需要你帮我把上传的 Excel 文件的列名对应到系统字段。这是一个「连线」任务。\n\n"
            f"系统需要的字段（target）：\n{field_lines}\n\n"
            f"上传文件的列名（source）：\n  {columns}\n\n"
            f"文件前几行样本数据：\n{sample_text}\n\n"
            f"请根据列名含义和样本数据内容，将文件列名对应到合适的系统字段。\n"
            f"每个系统字段最多对应一个文件列名。不确定的不要映射。\n\n"
            f"返回 JSON:\n"
            f'{{"mappings": [{{"source": "文件列名", "target": "系统字段key"}}]}}'
        )

        logger.info(f"LLM column mapping: {len(columns)} columns, {len(sample_rows)} sample rows")

        llm = LLMFactory.get_available()
        result = await llm.generate_structured(
            [{"role": "user", "content": prompt}],
            schema=COLUMN_MAPPING_SCHEMA,
        )

        # Validate targets exist in SYSTEM_FIELDS_DESC
        valid_targets = set(SYSTEM_FIELDS_DESC.keys())
        mappings = [
            ColumnMapping(source=m["source"], target=m["target"], confidence=0.9)
            for m in result.get("mappings", [])
            if m.get("target") in valid_targets
        ]

        mapped_targets = {m.target for m in mappings}
        return MappingResult(
            mappings=mappings,
            unmapped_source=[c for c in columns if c not in {m.source for m in mappings}],
            unmapped_target=[k for k in valid_targets if k not in mapped_targets],
        )

    @classmethod
    def _empty_mapping(cls, columns: list[str]) -> MappingResult:
        """Return empty mapping when LLM is unavailable. All fields marked as missing."""
        return MappingResult(
            mappings=[],
            unmapped_source=list(columns),
            unmapped_target=list(SYSTEM_FIELDS_DESC.keys()),
        )

    @classmethod
    def build_degradation_report(cls, mapping: MappingResult) -> DegradationReport:
        """Generate degradation report from unmapped optional fields."""
        impacts = []
        for field in mapping.unmapped_target:
            if field in DEGRADATION_IMPACTS and field not in {"name", "credit"}:
                impacts.append(DEGRADATION_IMPACTS[field])

        return DegradationReport(
            missing_fields=[imp.field for imp in impacts],
            impacts=impacts,
        )