import {useState, useMemo} from 'react';
import ChatPanel from '../components/ChatPanel/ChatPanel';
import CourseCard from '../components/CourseCard/CourseCard';
import ScheduleView from '../components/ScheduleView/ScheduleView';
import PlanActions from '../components/PlanActions/PlanActions';
import {FileUpload} from '../components/FileUpload/FileUpload';
import type {ChatMessage, RecommendationPlan, Course, Conflict} from '../types';
import {chatStream, savePlan, deletePlan} from '../services/api';

/** 按课程名称合并，将同一课程的多个时间段合并到一个 card */
function mergeCourses(courses: Course[]): Course[] {
    const map = new Map<string, Course>();
    for (const c of courses) {
        const existing = map.get(c.name);
        if (!existing) {
            map.set(c.name, {...c});
        } else {
            // 合并 schedule，去重
            const seen = new Set(existing.schedule.map(s => `${s.day_of_week}-${s.start_period}-${s.end_period}`));
            for (const slot of c.schedule) {
                const key = `${slot.day_of_week}-${slot.start_period}-${slot.end_period}`;
                if (!seen.has(key)) {
                    existing.schedule.push(slot);
                    seen.add(key);
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

/** Build bidirectional conflict graph from conflict list */
function buildConflictGraph(courses: Course[], conflicts: Conflict[]): Map<string, Set<string>> {
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

/** Compute default conflict-free selection: first-seen course in each conflict pair */
function computeDefaultSelection(courses: Course[], conflictGraph: Map<string, Set<string>>): Set<string> {
    const selected = new Set<string>();
    const excluded = new Set<string>();
    for (const c of courses) {
        if (excluded.has(c.id)) continue;
        selected.add(c.id);
        const partners = conflictGraph.get(c.id);
        if (partners) {
            for (const pid of partners) {
                excluded.add(pid);
            }
        }
    }
    return selected;
}

/** Compute credit breakdown by category */
function categoryCreditsSummary(courses: Course[]): string {
    const map = new Map<string, number>();
    for (const c of courses) {
        const key = c.category || '其他';
        map.set(key, (map.get(key) || 0) + c.credit);
    }
    if (map.size <= 1) return '';
    return Array.from(map.entries())
        .map(([cat, credits]) => `${cat} ${credits} 学分`)
        .join(' · ');
}

interface PlanSelectionState {
    selectedIds: Set<string>;
    hoveredId: string | null;
}

export default function CourseSelect() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [recommendations, setRecommendations] = useState<RecommendationPlan[]>([]);
    const [conversationId, setConversationId] = useState<string | undefined>();
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [favorites, setFavorites] = useState<RecommendationPlan[]>([]);
    const [savedPlanIds, setSavedPlanIds] = useState<Map<string, string>>(new Map());

    // Conflict swap state: per-plan selection and hover
    const [planStates, setPlanStates] = useState<Map<number, PlanSelectionState>>(new Map());

    // Build conflict graphs for each plan
    const conflictGraphs = useMemo(() => {
        const graphs: Map<string, Set<string>>[] = [];
        for (const plan of recommendations) {
            const merged = mergeCourses(plan.courses);
            graphs.push(buildConflictGraph(merged, plan.conflicts));
        }
        return graphs;
    }, [recommendations]);

    const getPlanState = (planIdx: number, courses: Course[], graph: Map<string, Set<string>>): PlanSelectionState => {
        const existing = planStates.get(planIdx);
        if (existing) return existing;
        return {
            selectedIds: computeDefaultSelection(courses, graph),
            hoveredId: null,
        };
    };

    const handleSwap = (planIdx: number, courseId: string, graph: Map<string, Set<string>>) => {
        setPlanStates(prev => {
            const next = new Map(prev);
            const mergedCourses = mergeCourses(recommendations[planIdx].courses);
            const state = getPlanState(planIdx, mergedCourses, graph);

            // No-op if already selected (FR-005)
            if (state.selectedIds.has(courseId)) return prev;

            // Find conflict partner in current selection and swap
            const partners = graph.get(courseId);
            if (!partners || partners.size === 0) return prev;

            const newSelected = new Set(state.selectedIds);
            for (const pid of partners) {
                newSelected.delete(pid);
            }
            newSelected.add(courseId);

            next.set(planIdx, {selectedIds: newSelected, hoveredId: state.hoveredId});
            return next;
        });
    };

    const handleHover = (planIdx: number, courseId: string | null) => {
        setPlanStates(prev => {
            const next = new Map(prev);
            const existing = prev.get(planIdx);
            if (existing) {
                next.set(planIdx, {selectedIds: existing.selectedIds, hoveredId: courseId});
            } else {
                // Will be initialized on next render
                const mergedCourses = mergeCourses(recommendations[planIdx].courses);
                const graph = conflictGraphs[planIdx];
                if (graph) {
                    next.set(planIdx, {
                        selectedIds: computeDefaultSelection(mergedCourses, graph),
                        hoveredId: courseId,
                    });
                }
            }
            return next;
        });
    };

    const handleToggleFavorite = async (plan: RecommendationPlan) => {
        const key = `${plan.plan_name}-${plan.total_credits}`;
        const savedId = savedPlanIds.get(key);

        if (savedId) {
            // Unfavorite: delete from backend
            try {
                await deletePlan(savedId);
            } catch { /* ignore */ }
            setSavedPlanIds((prev) => {
                const next = new Map(prev);
                next.delete(key);
                return next;
            });
            setFavorites((prev) => prev.filter(
                (f) => !(f.plan_name === plan.plan_name && f.total_credits === plan.total_credits)
            ));
        } else {
            // Favorite: save to backend
            const courseIds = plan.courses.map((c) => c.id);
            try {
                const saved = await savePlan(plan.plan_name, courseIds);
                setSavedPlanIds((prev) => new Map(prev).set(key, saved.id));
            } catch { /* ignore */ }
            setFavorites((prev) => [...prev, plan]);
        }
    };

    const isFavorited = (plan: RecommendationPlan) =>
        favorites.some(
            (f) => f.plan_name === plan.plan_name && f.total_credits === plan.total_credits
        );

    const handleSend = async (message: string) => {
        setMessages((prev) => [...prev, {role: 'user', content: message}]);
        setLoading(true);
        setHasSearched(true);
        setStreamingContent('');

        await chatStream(message, conversationId, {
            onToken: (content) => {
                setStreamingContent((prev) => prev + content);
            },
            onDone: (result) => {
                setConversationId(result.conversation_id);
                setMessages((prev) => [
                    ...prev,
                    {
                        role: 'assistant',
                        content: result.reply,
                        recommendations: result.recommendations,
                        degraded: result.degraded,
                    },
                ]);
                setRecommendations(result.recommendations);
                setStreamingContent('');
                setLoading(false);
            },
            onError: () => {
                setMessages((prev) => [
                    ...prev,
                    {role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。'},
                ]);
                setStreamingContent('');
                setLoading(false);
            },
        });
    };

    const emptyResults = hasSearched && !loading && recommendations.length === 0;

    return (
        <div className="course-select-page">
            <div className="upload-section">
                <FileUpload/>
            </div>
            <div className="chat-section">
                <ChatPanel
                    messages={messages}
                    onSend={handleSend}
                    loading={loading}
                    emptyResults={emptyResults}
                    streamingContent={streamingContent}
                />
            </div>
            <div className="recommendations-section">
                <h2 style={{fontSize: '1em', marginBottom: '8px'}}>推荐方案</h2>
                {recommendations.length === 0 && !hasSearched ? (
                    <p>在左侧对话框描述你的选课偏好，推荐方案将在这里展示。</p>
                ) : recommendations.length === 0 ? (
                    <p style={{color: 'var(--color-text-light)'}}>未找到匹配的课程方案，请尝试调整你的需求描述。</p>
                ) : (
                    recommendations.map((plan, planIdx) => {
                        const merged = mergeCourses(plan.courses);
                        const graph = conflictGraphs[planIdx] || new Map();
                        const state = getPlanState(planIdx, merged, graph);
                        const selectedCourses = merged.filter(c => state.selectedIds.has(c.id));

                        return (
                            <div key={planIdx} className="recommendation-plan">
                                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                    <h3 style={{margin: 0}}>{plan.plan_name}（匹配度：{plan.match_score}%）</h3>
                                    <PlanActions
                                        courses={selectedCourses}
                                        isFavorited={isFavorited(plan)}
                                        onToggleFavorite={() => handleToggleFavorite(plan)}
                                    />
                                </div>
                                <p>总学分：{plan.total_credits}{categoryCreditsSummary(selectedCourses) && `（${categoryCreditsSummary(selectedCourses)}）`}</p>
                                <div className="course-list">
                                    {merged.map((course) => (
                                        <CourseCard
                                            key={course.id}
                                            course={course}
                                            isSelected={state.selectedIds.has(course.id)}
                                            isConflictHighlighted={
                                                state.hoveredId !== null &&
                                                !state.selectedIds.has(course.id) &&
                                                (graph.get(state.hoveredId)?.has(course.id) ?? false)
                                            }
                                            onClick={() => handleSwap(planIdx, course.id, graph)}
                                            onMouseEnter={() => handleHover(planIdx, course.id)}
                                            onMouseLeave={() => handleHover(planIdx, null)}
                                        />
                                    ))}
                                </div>
                                <ScheduleView courses={selectedCourses} conflicts={plan.conflicts}/>
                            </div>
                        );
                    })
                )}
                {favorites.length > 0 && (
                    <div className="favorites-section">
                        <h3>收藏的方案（{favorites.length}）</h3>
                        <div className="favorites-list">
                            {favorites.map((plan, i) => (
                                <div key={i} className="favorite-item">
                                    <div className="favorite-item-info">
                                        <span className="favorite-item-name">{plan.plan_name}</span>
                                        <span className="favorite-item-meta">
                                            匹配度 {plan.match_score}% · {plan.total_credits} 学分 · {plan.courses.length} 门课程
                                        </span>
                                    </div>
                                    <button
                                        className="plan-action-btn favorite-btn favorited"
                                        onClick={() => handleToggleFavorite(plan)}
                                        title="取消收藏"
                                    >
                                        ★
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
