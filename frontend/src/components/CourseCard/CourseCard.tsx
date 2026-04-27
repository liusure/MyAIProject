import type { Course } from '../../types';

interface CourseCardProps {
  course: Course;
  isSelected?: boolean;
  isConflictHighlighted?: boolean;
  onClick?: () => void;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

const DAY_NAMES = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];

export default function CourseCard({
  course,
  isSelected = true,
  isConflictHighlighted = false,
  onClick,
  onMouseEnter,
  onMouseLeave,
}: CourseCardProps) {
  const borderColor = isConflictHighlighted
    ? '#e53935'
    : 'var(--color-border)';

  return (
    <div
      className={`course-card${!isSelected ? ' course-card--unselected' : ''}`}
      style={{
        border: `2px solid ${borderColor}`,
        borderRadius: 'var(--radius-sm)',
        padding: '6px 10px',
        backgroundColor: isSelected ? 'var(--color-surface)' : 'var(--color-bg)',
        boxShadow: 'var(--shadow-sm)',
        transition: 'transform var(--transition-normal), box-shadow var(--transition-normal), border-color var(--transition-fast), opacity var(--transition-fast)',
        cursor: onClick ? 'pointer' : 'default',
        fontSize: '0.82em',
        lineHeight: 1.4,
        opacity: isSelected ? 1 : 0.7,
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-1px)';
        e.currentTarget.style.boxShadow = 'var(--shadow-hover)';
        onMouseEnter?.();
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
        onMouseLeave?.();
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '3px' }}>
        <span style={{ fontWeight: 600, color: 'var(--color-text)', fontSize: '1.05em' }}>{course.name}</span>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9em' }}>{course.course_no}</span>
      </div>
      <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.92em' }}>
        {course.credit}学分
        {course.instructor && <> · {course.instructor}</>}
        {course.location && <> · {course.location}{course.campus && `（${course.campus}）`}</>}
        {course.category && <> · {course.category}</>}
      </div>
      {course.schedule.length > 0 && (
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
          {course.schedule.map((slot, i) => (
            <span
              key={i}
              style={{
                padding: '1px 6px',
                borderRadius: '4px',
                backgroundColor: isSelected ? 'var(--color-primary-bg)' : 'var(--color-bg)',
                color: isSelected ? 'var(--color-primary)' : 'var(--color-text-light)',
                fontSize: '0.88em',
              }}
            >
              {DAY_NAMES[slot.day_of_week]}（{slot.start_period}-{slot.end_period}节）
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
