import type {
  Course,
  Conflict,
  RecommendationPlan,
  SavedPlan,
  ImportAnalyzeResponse,
  ImportConfirmResponse,
  SessionCourse,
  MappingResult,
  RecommendationProgress,
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(error.detail || '请求失败');
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface ChatResponse {
  conversation_id: string;
  reply: string;
  recommendations: RecommendationPlan[];
  conflicts: Conflict[];
  degraded: boolean;
}

export interface StreamCallbacks {
  onToken: (content: string) => void;
  onProgress?: (stage: RecommendationProgress['stage'], message: string) => void;
  onDone: (result: ChatResponse) => void;
  onError: (error: Error) => void;
}

let currentAbortController: AbortController | null = null;

export function cancelCurrentStream() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
}

// Chat
export const chat = (message: string, conversation_id?: string) =>
  request<ChatResponse>('/conversation/chat', {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id }),
  });

export const chatStream = async (
  message: string,
  conversation_id: string | undefined,
  callbacks: StreamCallbacks,
) => {
  cancelCurrentStream();
  const controller = new AbortController();
  currentAbortController = controller;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/conversation/chat/stream`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id }),
      signal: controller.signal,
    });
  } catch (err) {
    if (controller.signal.aborted) return;
    callbacks.onError(err instanceof Error ? err : new Error('请求失败'));
    return;
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: '请求失败' }));
    callbacks.onError(new Error(error.detail || '请求失败'));
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError(new Error('无法读取流'));
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = JSON.parse(line.slice(6));
        if (data.type === 'token') {
          callbacks.onToken(data.content);
        } else if (data.type === 'progress') {
          callbacks.onProgress?.(data.stage, data.message);
        } else if (data.type === 'done') {
          callbacks.onDone(data as ChatResponse);
        }
      }
    }
  } catch (err) {
    if (!controller.signal.aborted) {
      callbacks.onError(err instanceof Error ? err : new Error('流式读取失败'));
    }
  } finally {
    if (currentAbortController === controller) {
      currentAbortController = null;
    }
  }
};

// Courses
export const searchCourses = (q: string, semester?: string, category?: string) => {
  const params = new URLSearchParams({ q });
  if (semester) params.set('semester', semester);
  if (category) params.set('category', category);
  return request<{ courses: Course[] }>(`/courses/search?${params}`);
};

// Plans
export const savePlan = (name: string, course_ids: string[], notes?: string) =>
  request<SavedPlan>('/plans', {
    method: 'POST',
    body: JSON.stringify({ name, course_ids, notes }),
  });

export const listPlans = () =>
  request<{ plans: SavedPlan[] }>('/plans');

export const deletePlan = (plan_id: string) =>
  request<void>(`/plans/${plan_id}`, { method: 'DELETE' });


// Import
export const uploadAnalyze = async (file: File): Promise<ImportAnalyzeResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/import/analyze`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (!res.ok) {
    const error = await res.text().catch(() => '分析失败');
    throw new Error(error);
  }
  return res.json();
};

export const confirmImport = async (
  mapping: MappingResult,
  raw_data: Record<string, unknown>[],
): Promise<ImportConfirmResponse> => {
  try {
    const res = await fetch(`${API_BASE}/import/confirm`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mapping, raw_data }),
    });
    if (!res.ok) {
      const error = await res.text().catch(() => '导入失败');
      throw new Error(error);
    }
    return res.json();
  } catch (e) {
    if (e instanceof TypeError && e.message === 'Failed to fetch') {
      throw new Error('无法连接到服务器，请检查后端服务是否运行');
    }
    throw e;
  }
};

export const getSessionCourses = async (): Promise<SessionCourse[] | null> => {
  const res = await fetch(`${API_BASE}/import/session/courses`, {
    credentials: 'include',
  });
  if (res.status === 204) return null;
  const data = await res.json();
  return data.courses;
};

export const clearSessionCourses = async (): Promise<void> => {
  await fetch(`${API_BASE}/import/session/courses`, {
    method: 'DELETE',
    credentials: 'include',
  });
};
