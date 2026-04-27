import type { SavedPlan, SessionCourse } from '../../types';

interface PlanExporterProps {
  plan: SavedPlan;
  courseMap: Map<string, SessionCourse>;
}

export default function PlanExporter({ plan, courseMap }: PlanExporterProps) {
  const handleExport = () => {
    const lines: string[] = [];
    lines.push(`方案名称：${plan.name}`);
    lines.push(`总学分：${plan.total_credits}`);

    // Category breakdown
    const catMap = new Map<string, number>();
    for (const id of plan.course_ids) {
      const course = courseMap.get(id);
      if (course) {
        const key = course.category || '其他';
        catMap.set(key, (catMap.get(key) || 0) + course.credit);
      }
    }
    if (catMap.size > 1) {
      const breakdown = Array.from(catMap.entries())
        .map(([cat, credits]) => `${cat} ${credits} 学分`)
        .join(' · ');
      lines.push(`学分构成：${breakdown}`);
    }

    if (plan.match_score !== null) {
      lines.push(`匹配度：${plan.match_score}%`);
    }
    lines.push(`课程列表：`);
    plan.course_ids.forEach((id, i) => {
      const course = courseMap.get(id);
      if (course) {
        const label = course.course_no ? `${course.name}（${course.course_no}）` : course.name;
        lines.push(`${i + 1}. ${label}`);
      } else {
        lines.push(`${i + 1}. [未知课程] (${id})`);
      }
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${plan.name}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      className="plan-export-btn"
      onClick={handleExport}
      style={{
        padding: '6px 16px',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--color-primary)',
        backgroundColor: 'var(--color-surface)',
        color: 'var(--color-primary)',
        cursor: 'pointer',
        transition: 'background-color var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--color-primary)';
        e.currentTarget.style.color = '#fff';
        e.currentTarget.style.boxShadow = 'var(--shadow-hover)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--color-surface)';
        e.currentTarget.style.color = 'var(--color-primary)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      导出
    </button>
  );
}
