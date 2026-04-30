import {useState, useMemo, useEffect} from 'react';
import ChatPanel from '../components/ChatPanel/ChatPanel';
import CourseCard from '../components/CourseCard/CourseCard';
import ScheduleView from '../components/ScheduleView/ScheduleView';
import PlanActions from '../components/PlanActions/PlanActions';
import {FileUpload} from '../components/FileUpload/FileUpload';
import type {ChatMessage, RecommendationPlan, Course, RecommendationProgress} from '../types';
import {chatStream, savePlan, deletePlan, cancelCurrentStream} from '../services/api';
import {useNavigate} from 'react-router-dom';
import {mergeCourses, mergeCoursesWithMapping} from '../utils/courseMerge';
import {detectTimeConflicts, buildConflictGraph} from '../utils/conflictDetect';

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
    const navigate = useNavigate();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [recommendations, setRecommendations] = useState<RecommendationPlan[]>([]);
    const [conversationId, setConversationId] = useState<string | undefined>();
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [progressMessages, setProgressMessages] = useState<RecommendationProgress[]>([]);
    const [savedPlanIds, setSavedPlanIds] = useState<Map<string, string>>(new Map());
    const [toast, setToast] = useState<string | null>(null);

    // Conflict swap state: per-plan selection and hover
    const [planStates, setPlanStates] = useState<Map<number, PlanSelectionState>>(new Map());

    // Reset planStates when recommendations change to ensure default selection is applied
    useEffect(() => {
        setPlanStates(new Map());
    }, [recommendations]);

    // Build conflict graphs for each plan (re-detect after merging to avoid stale IDs)
    const conflictGraphs = useMemo(() => {
        const graphs: Map<string, Set<string>>[] = [];
        for (const plan of recommendations) {
            const merged = mergeCourses(plan.courses);
            const conflicts = detectTimeConflicts(merged);
            graphs.push(buildConflictGraph(merged, conflicts));
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

    const showToast = (msg: string) => {
        setToast(msg);
        setTimeout(() => setToast(null), 2000);
    };

    const handleToggleFavorite = async (plan: RecommendationPlan, selectedCourseIds: string[]) => {
        const key = `${plan.plan_name}-${plan.total_credits}`;
        const savedId = savedPlanIds.get(key);

        if (savedId) {
            try {
                await deletePlan(savedId);
            } catch { /* ignore */ }
            setSavedPlanIds((prev) => {
                const next = new Map(prev);
                next.delete(key);
                return next;
            });
            showToast('已取消收藏');
        } else {
            try {
                const saved = await savePlan(plan.plan_name, selectedCourseIds);
                setSavedPlanIds((prev) => new Map(prev).set(key, saved.id));
                showToast('已收藏，可在"我的方案"中查看');
            } catch { /* ignore */ }
        }
    };

    const isFavorited = (plan: RecommendationPlan) => {
        const key = `${plan.plan_name}-${plan.total_credits}`;
        return savedPlanIds.has(key);
    };

    const handleSend = async (message: string) => {
        cancelCurrentStream();
        setMessages((prev) => [...prev, {role: 'user', content: message}]);
        setLoading(true);
        setHasSearched(true);
        setStreamingContent('');
        setProgressMessages([]);

        await chatStream(message, conversationId, {
            onProgress: (stage, progressMessage) => {
                setProgressMessages((prev) => {
                    const existing = prev.find((p) => p.stage === stage);
                    if (existing) {
                        return prev.map((p) => (p.stage === stage ? {stage, message: progressMessage} : p));
                    }
                    return [...prev, {stage, message: progressMessage}];
                });
            },
            onToken: (content) => {
                setProgressMessages([]);
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
                    progressMessages={progressMessages}
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
                        const {merged, idMapping} = mergeCoursesWithMapping(plan.courses);
                        const graph = conflictGraphs[planIdx] || new Map();
                        const state = getPlanState(planIdx, merged, graph);
                        const selectedCourses = merged.filter(c => state.selectedIds.has(c.id));
                        const selectedConflicts = detectTimeConflicts(selectedCourses);
                        // 展开选中的合并课程 ID 为原始课程 ID，确保 MyPlans 能正确重建
                        const selectedOriginalIds = selectedCourses.flatMap(c => idMapping.get(c.id) || [c.id]);

                        return (
                            <div key={planIdx} className="recommendation-plan">
                                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                    <h3 style={{margin: 0}}>{plan.plan_name}（匹配度：{plan.match_score}%）</h3>
                                    <PlanActions
                                        courses={selectedCourses}
                                        isFavorited={isFavorited(plan)}
                                        onToggleFavorite={() => handleToggleFavorite(plan, selectedOriginalIds)}
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
                                <ScheduleView courses={selectedCourses} conflicts={selectedConflicts}/>
                            </div>
                        );
                    })
                )}
            </div>
            {toast && (
                <div style={{
                    position: 'fixed',
                    bottom: '24px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: 'var(--color-text)',
                    color: 'var(--color-surface)',
                    padding: '8px 20px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.9em',
                    zIndex: 1000,
                    opacity: 0.95,
                }}>
                    {toast}
                    {toast.includes('已收藏') && (
                        <span
                            style={{marginLeft: 12, textDecoration: 'underline', cursor: 'pointer'}}
                            onClick={() => navigate('/plans')}
                        >
                            查看
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}
