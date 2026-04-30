import type { Course, Conflict, ScheduleSlot } from '../types';

function slotsOverlap(a: ScheduleSlot, b: ScheduleSlot): boolean {
    if (a.day_of_week !== b.day_of_week) return false;
    const aWeeks = new Set(a.weeks);
    const bWeeks = new Set(b.weeks);
    if (aWeeks.size > 0 && bWeeks.size > 0) {
        let hasCommon = false;
        for (const w of aWeeks) {
            if (bWeeks.has(w)) { hasCommon = true; break; }
        }
        if (!hasCommon) return false;
    }
    return a.start_period < b.end_period && b.start_period < a.end_period;
}

/** 在前端重新检测课程间的时间冲突（基于合并后的课程列表） */
export function detectTimeConflicts(courses: Course[]): Conflict[] {
    const conflicts: Conflict[] = [];
    for (let i = 0; i < courses.length; i++) {
        for (let j = i + 1; j < courses.length; j++) {
            const a = courses[i];
            const b = courses[j];
            if (a.id === b.id) continue;
            for (const slotA of a.schedule) {
                for (const slotB of b.schedule) {
                    if (slotsOverlap(slotA, slotB)) {
                        conflicts.push({
                            type: 'time',
                            severity: 'error',
                            course_a: a.id,
                            course_b: b.id,
                            message: `时间冲突：${a.name} 与 ${b.name}`,
                        });
                    }
                }
            }
        }
    }
    return conflicts;
}

/** 从冲突列表构建双向冲突图 */
export function buildConflictGraph(courses: Course[], conflicts: Conflict[]): Map<string, Set<string>> {
    const graph = new Map<string, Set<string>>();
    for (const c of courses) {
        graph.set(c.id, new Set());
    }
    for (const conflict of conflicts) {
        if (conflict.type === 'time') {
            graph.get(conflict.course_a)?.add(conflict.course_b);
            graph.get(conflict.course_b)?.add(conflict.course_a);
        }
    }
    return graph;
}
