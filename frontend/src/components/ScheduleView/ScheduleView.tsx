import { useMemo } from 'react';
import type { Conflict, ScheduleSlot } from '../../types';
import './ScheduleView.css';

interface ScheduleCourse {
  id: string;
  name: string;
  instructor?: string | null;
  location?: string | null;
  schedule: ScheduleSlot[];
}

interface ScheduleViewProps {
  courses: ScheduleCourse[];
  conflicts?: Conflict[];
}

const PERIODS = Array.from({ length: 13 }, (_, i) => i + 1); // 1-13节
const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

const COURSE_COLORS = [
  '#e3f2fd', '#f3e5f5', '#e8f5e9', '#fff3e0',
  '#fce4ec', '#e0f2f1', '#fff8e1', '#f1f8e9',
];

const COURSE_TEXT_COLORS = [
  '#1565c0', '#7b1fa2', '#2e7d32', '#e65100',
  '#c62828', '#00695c', '#f57f17', '#33691e',
];

export default function ScheduleView({ courses, conflicts = [] }: ScheduleViewProps) {
  const conflictSet = useMemo(() => {
    const set = new Set<string>();
    for (const c of conflicts) {
      if (c.type === 'time') {
        set.add([c.course_a, c.course_b].sort().join('-'));
      }
    }
    return set;
  }, [conflicts]);

  const coursesWithSchedule = useMemo(
    () => courses.filter((c) => c.schedule && c.schedule.length > 0),
    [courses],
  );

  const coursesWithoutSchedule = useMemo(
    () => courses.filter((c) => !c.schedule || c.schedule.length === 0),
    [courses],
  );

  const courseColorMap = useMemo(() => {
    const map = new Map<string, { bg: string; text: string }>();
    coursesWithSchedule.forEach((c, i) => {
      map.set(c.id, {
        bg: COURSE_COLORS[i % COURSE_COLORS.length],
        text: COURSE_TEXT_COLORS[i % COURSE_TEXT_COLORS.length],
      });
    });
    return map;
  }, [coursesWithSchedule]);

  const slotMap = useMemo(() => {
    const map = new Map<string, ScheduleCourse[]>();
    console.log(coursesWithSchedule)
    for (const course of coursesWithSchedule) {
      for (const slot of course.schedule) {
        for (let p = slot.start_period; p < slot.end_period; p++) {
          const key = `${slot.day_of_week}-${p}`;
          if (!map.has(key)) map.set(key, []);
          map.get(key)!.push(course);
        }
      }
    }
    return map;
  }, [coursesWithSchedule]);

  return (
    <div className="schedule-view">
      <div className="schedule-grid">
        <div className="schedule-header schedule-corner">节次</div>
        {DAYS.map((d) => (
          <div key={d} className="schedule-header">{d}</div>
        ))}
        {PERIODS.map((period) => (
          <div key={`row-${period}`} style={{ display: 'contents' }}>
            <div className="schedule-time">
              {period}
            </div>
            {DAYS.map((_, dayIdx) => {
              const day = dayIdx + 1;
              const key = `${day}-${period}`;
              const slotCourses = slotMap.get(key) || [];
              const hasConflict = slotCourses.length > 1;
              return (
                <div
                  key={key}
                  className={`schedule-cell${hasConflict ? ' has-conflict' : ''}`}
                >
                  {slotCourses.map((c) => {
                    const colors = courseColorMap.get(c.id);
                    const isConflict = slotCourses.some(
                      (other) => other.id !== c.id && conflictSet.has([c.id, other.id].sort().join('-'))
                    );
                    return (
                      <div
                        key={c.id}
                        className={`schedule-course${isConflict ? ' conflict' : ''}`}
                        style={{
                          backgroundColor: isConflict ? '#ffebee' : colors?.bg,
                          color: isConflict ? '#c62828' : colors?.text,
                        }}
                        title={`${c.name}${c.instructor ? ' - ' + c.instructor : ''}${c.location ? ' - ' + c.location : ''}`}
                      >
                        {c.name}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {coursesWithoutSchedule.length > 0 && (
        <div className="schedule-unspecified">
          <h4>时间未指定</h4>
          <div className="schedule-unspecified-list">
            {coursesWithoutSchedule.map((c) => (
              <div key={c.id} className="schedule-unspecified-item">
                <span className="course-name">{c.name}</span>
                {c.instructor && <span className="course-instructor">{c.instructor}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {conflicts.length > 0 && (
        <div className="schedule-conflicts-summary">
          <h4>检测到 {conflicts.length} 个冲突</h4>
          <ul>
            {conflicts.map((c, i) => (
              <li key={i} className={`conflict-item conflict-item--${c.severity}`}>
                {c.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
