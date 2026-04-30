import type { Course } from '../types';

/**
 * 按课程号合并课程，将同一课程的多个时间段合并到一个 card。
 * 以 course_no 为主键；course_no 为空时降级使用 name。
 */
export function mergeCourses(courses: Course[]): Course[] {
    const map = new Map<string, Course>();
    for (const c of courses) {
        const key = c.course_no || `__name__:${c.name}`;
        const existing = map.get(key);
        if (!existing) {
            map.set(key, {...c});
        } else {
            // 合并 schedule，去重
            const seen = new Set(existing.schedule.map(s => `${s.day_of_week}-${s.start_period}-${s.end_period}`));
            for (const slot of c.schedule) {
                const slotKey = `${slot.day_of_week}-${slot.start_period}-${slot.end_period}`;
                if (!seen.has(slotKey)) {
                    existing.schedule.push(slot);
                    seen.add(slotKey);
                }
            }
            // 保留非空值
            if (!existing.instructor && c.instructor) existing.instructor = c.instructor;
            if (!existing.location && c.location) existing.location = c.location;
            if (!existing.campus && c.campus) existing.campus = c.campus;
            if (!existing.category && c.category) existing.category = c.category;
        }
    }
    return [...map.values()];
}

/**
 * 合并课程并返回 ID 映射：merged course ID → 原始课程 ID 列表。
 * 用于收藏时将选中的合并课程 ID 展开为原始 ID，确保 MyPlans 能正确重建。
 */
export function mergeCoursesWithMapping(courses: Course[]): {
    merged: Course[];
    idMapping: Map<string, string[]>;
} {
    const courseMap = new Map<string, Course>();
    const keyMapping = new Map<string, string[]>(); // merge key → original IDs

    for (const c of courses) {
        const key = c.course_no || `__name__:${c.name}`;
        const existing = courseMap.get(key);
        if (!existing) {
            courseMap.set(key, {...c});
            keyMapping.set(key, [c.id]);
        } else {
            keyMapping.get(key)!.push(c.id);
            const seen = new Set(existing.schedule.map(s => `${s.day_of_week}-${s.start_period}-${s.end_period}`));
            for (const slot of c.schedule) {
                const slotKey = `${slot.day_of_week}-${slot.start_period}-${slot.end_period}`;
                if (!seen.has(slotKey)) {
                    existing.schedule.push(slot);
                    seen.add(slotKey);
                }
            }
            if (!existing.instructor && c.instructor) existing.instructor = c.instructor;
            if (!existing.location && c.location) existing.location = c.location;
            if (!existing.campus && c.campus) existing.campus = c.campus;
            if (!existing.category && c.category) existing.category = c.category;
        }
    }

    const merged = [...courseMap.values()];
    const idMapping = new Map<string, string[]>();
    for (const course of merged) {
        const key = course.course_no || `__name__:${course.name}`;
        idMapping.set(course.id, keyMapping.get(key) || [course.id]);
    }

    return {merged, idMapping};
}
