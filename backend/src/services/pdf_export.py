import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.saved_plan import SavedPlan
from src.models.course import Course
from sqlalchemy import select


class PDFExportService:
    """PDF 导出服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def export_plan(self, plan: SavedPlan) -> bytes:
        from weasyprint import HTML

        html = await self._build_html(plan)
        return HTML(string=html).write_pdf()

    async def _build_html(self, plan: SavedPlan) -> str:
        # 获取课程详情
        course_ids = [uuid.UUID(cid) for cid in plan.course_ids]
        result = await self.db.execute(select(Course).where(Course.id.in_(course_ids)))
        courses = result.scalars().all()

        rows = ""
        for c in courses:
            schedule_str = ", ".join(
                f"周{slot.get('day_of_week', '')} 第{slot.get('start_period', '')}-{slot.get('end_period', '')}节"
                for slot in (c.schedule if isinstance(c.schedule, list) else [])
            )
            rows += f"""
            <tr>
                <td>{c.course_no}</td>
                <td>{c.name}</td>
                <td>{c.credit}</td>
                <td>{c.instructor}</td>
                <td>{schedule_str}</td>
                <td>{c.location}</td>
                <td>{c.campus}</td>
            </tr>"""

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif; padding: 20px; }}
                h1 {{ color: #1a73e8; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f5f5f5; }}
                .info {{ margin: 10px 0; color: #666; }}
            </style>
        </head>
        <body>
            <h1>{plan.name}</h1>
            <p class="info">总学分：{plan.total_credits} | 匹配度：{plan.match_score or 'N/A'}% | 导出时间：{plan.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            {f'<p class="info">备注：{plan.notes}</p>' if plan.notes else ''}
            <table>
                <thead>
                    <tr>
                        <th>课程编号</th>
                        <th>课程名称</th>
                        <th>学分</th>
                        <th>教师</th>
                        <th>上课时间</th>
                        <th>地点</th>
                        <th>校区</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """
