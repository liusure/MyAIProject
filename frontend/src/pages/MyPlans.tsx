import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { listPlans, deletePlan, getSessionCourses } from '../services/api';
import PlanExporter from '../components/PlanExporter/PlanExporter';
import ScheduleModal from '../components/ScheduleModal/ScheduleModal';
import { mergeCourses } from '../utils/courseMerge';
import type { SavedPlan, SessionCourse, Course, ScheduleSlot } from '../types';

interface ScheduleViewCourse {
  id: string;
  name: string;
  instructor?: string | null;
  location?: string | null;
  schedule: ScheduleSlot[];
}

const PAGE_SIZE = 10;

function categoryCreditsSummary(plan: SavedPlan, courseMap: Map<string, SessionCourse>): string {
  const map = new Map<string, number>();
  for (const id of plan.course_ids) {
    const course = courseMap.get(id);
    if (course) {
      const key = course.category || '其他';
      map.set(key, (map.get(key) || 0) + course.credit);
    }
  }
  if (map.size <= 1) return '';
  return Array.from(map.entries())
    .map(([cat, credits]) => `${cat} ${credits} 学分`)
    .join(' · ');
}

function calcWeeklyPeriods(plan: SavedPlan, courseMap: Map<string, SessionCourse>): number {
  let total = 0;
  for (const id of plan.course_ids) {
    const course = courseMap.get(id);
    if (course) {
      for (const slot of course.schedule) {
        total += slot.end_period - slot.start_period;
      }
    }
  }
  return total;
}

export default function MyPlans() {
  const location = useLocation();
  const [plans, setPlans] = useState<SavedPlan[]>([]);
  const [sessionCourses, setSessionCourses] = useState<SessionCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalPlanName, setModalPlanName] = useState('');
  const [modalCourses, setModalCourses] = useState<ScheduleViewCourse[]>([]);

  // 每次进入 /plans 页面时重新加载数据
  useEffect(() => {
    if (location.pathname === '/plans') {
      loadPlans();
    }
  }, [location.pathname]);

  const loadPlans = async () => {
    try {
      const [res, courses] = await Promise.all([listPlans(), getSessionCourses()]);
      const sorted = res.plans.sort(
        (a: SavedPlan, b: SavedPlan) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setPlans(sorted);
      if (courses) setSessionCourses(courses);
    } finally {
      setLoading(false);
    }
  };

  const courseMap = useMemo(() => {
    const map = new Map<string, SessionCourse>();
    for (const c of sessionCourses) {
      if (c.id) map.set(c.id, c);
    }
    return map;
  }, [sessionCourses]);

  const handleOpenSchedule = (plan: SavedPlan) => {
    // 用保存的原始 ID 查找课程，再应用合并逻辑（与推荐页面一致）
    const found: Course[] = [];
    for (const id of plan.course_ids) {
      const c = courseMap.get(id);
      if (c && c.id) {
        found.push({
          id: c.id,
          course_no: c.course_no || '',
          name: c.name,
          credit: c.credit,
          instructor: c.instructor || '',
          capacity: c.capacity || 0,
          schedule: c.schedule,
          location: c.location || '',
          campus: c.campus || '',
          category: c.category || '',
          semester: c.semester || '',
          is_active: true,
        });
      }
    }
    const merged = mergeCourses(found);
    const viewCourses: ScheduleViewCourse[] = merged.map(c => ({
      id: c.id,
      name: c.name,
      instructor: c.instructor,
      location: c.location,
      schedule: c.schedule,
    }));
    setModalCourses(viewCourses);
    setModalPlanName(plan.name);
    setModalOpen(true);
  };

  const handleDelete = async (planId: string) => {
    if (!confirm('确定删除该方案？')) return;
    await deletePlan(planId);
    setPlans((prev) => prev.filter((p) => p.id !== planId));
  };

  const totalPages = Math.ceil(plans.length / PAGE_SIZE);
  const pagedPlans = plans.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) return <p>加载中...</p>;

  return (
    <>
    <div className="my-plans-page" style={{ padding: 'var(--spacing-lg)' }}>
      <h2>我的方案</h2>
      {plans.length === 0 ? (
        <p>暂无收藏方案。在选课推荐页面收藏推荐方案后将显示在这里。</p>
      ) : (
        <>
          <div className="plans-list">
            {pagedPlans.map((plan) => (
              <div
                key={plan.id}
                className="plan-card"
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-hover)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                }}
              >
                <h3 style={{ margin: '0 0 var(--spacing-sm) 0' }}>{plan.name}</h3>
                <p style={{ margin: '4px 0', color: 'var(--color-text-secondary)' }}>
                  总学分：{plan.total_credits}{categoryCreditsSummary(plan, courseMap) && `（${categoryCreditsSummary(plan, courseMap)}）`} · {plan.course_ids.length} 门课程 · 每周 {calcWeeklyPeriods(plan, courseMap)} 节
                </p>
                {plan.match_score !== null && (
                  <p style={{ margin: '4px 0', color: 'var(--color-text-secondary)' }}>匹配度：{plan.match_score}%</p>
                )}
                {plan.notes && <p style={{ margin: '4px 0', color: 'var(--color-text-secondary)' }}>备注：{plan.notes}</p>}
                <p style={{ margin: '4px 0', color: 'var(--color-text-light)', fontSize: '0.9em' }}>
                  收藏时间：{new Date(plan.created_at).toLocaleString()}
                </p>
                <div style={{ display: 'flex', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
                  <button
                    className="schedule-btn"
                    onClick={() => handleOpenSchedule(plan)}
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
                    课程表
                  </button>
                  <PlanExporter plan={plan} courseMap={courseMap} />
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(plan.id)}
                    style={{
                      padding: '6px 16px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-danger)',
                      backgroundColor: 'var(--color-surface)',
                      color: 'var(--color-danger)',
                      cursor: 'pointer',
                      transition: 'background-color var(--transition-fast), color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--color-danger)';
                      e.currentTarget.style.color = '#fff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--color-surface)';
                      e.currentTarget.style.color = 'var(--color-danger)';
                    }}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 'var(--spacing-sm)',
                marginTop: 'var(--spacing-lg)',
              }}
            >
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: page === 1 ? 'var(--color-bg)' : 'var(--color-surface)',
                  cursor: page === 1 ? 'default' : 'pointer',
                  transition: 'var(--transition-fast)',
                }}
              >
                上一页
              </button>
              <span style={{ color: 'var(--color-text-secondary)' }}>
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: page === totalPages ? 'var(--color-bg)' : 'var(--color-surface)',
                  cursor: page === totalPages ? 'default' : 'pointer',
                  transition: 'var(--transition-fast)',
                }}
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
      <ScheduleModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        courses={modalCourses}
        planName={modalPlanName}
      />
      <style>{`
        .plans-list {
          display: flex;
          flex-wrap: wrap;
          gap: var(--spacing-md);
        }
        .plan-card {
          flex: 0 0 calc(20% - var(--spacing-md) * 4 / 5);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          padding: var(--spacing-md);
          background-color: var(--color-surface);
          box-shadow: var(--shadow-sm);
          transition: transform var(--transition-normal), box-shadow var(--transition-normal);
          box-sizing: border-box;
        }
        @media (max-width: 768px) {
          .plan-card {
            flex: 0 0 100%;
          }
        }
      `}</style>
    </>
  );
}
