export interface Student {
  id: string;
  student_no: string;
  name: string;
  major: string;
  grade: number;
  role: 'student' | 'admin';
}

export interface ScheduleSlot {
  day_of_week: number;
  start_period: number;
  end_period: number;
  weeks: number[];
}

export interface Course {
  id: string;
  course_no: string;
  name: string;
  credit: number;
  instructor: string;
  capacity: number;
  schedule: ScheduleSlot[];
  location: string;
  campus: string;
  category: string;
  semester: string;
  is_active: boolean;
}

export interface Conflict {
  type: 'time' | 'location' | 'prerequisite' | 'commute';
  severity: 'error' | 'warning';
  course_a: string;
  course_b: string;
  message: string;
}

export interface RecommendationPlan {
  plan_name: string;
  courses: Course[];
  total_credits: number;
  match_score: number;
  conflicts: Conflict[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  recommendations?: RecommendationPlan[];
  conflicts?: Conflict[];
  degraded?: boolean;
}

export interface SavedPlan {
  id: string;
  name: string;
  course_ids: string[];
  total_credits: number;
  match_score: number | null;
  notes: string | null;
  created_at: string;
}

// Import types
export interface ColumnMapping {
  source: string;
  target: string;
  confidence: number;
}

export interface MappingResult {
  mappings: ColumnMapping[];
  unmapped_source: string[];
  unmapped_target: string[];
}

export interface DegradationImpact {
  field: string;
  impact: string;
  fallback: string;
}

export interface DegradationReport {
  missing_fields: string[];
  impacts: DegradationImpact[];
}

export interface ImportError {
  row: number;
  message: string;
}

export interface ImportAnalyzeResponse {
  mapping: MappingResult;
  sample_data: Record<string, unknown>[];
  degradation: DegradationReport;
}

export interface ImportConfirmResponse {
  courses: SessionCourse[];
  total: number;
  errors: ImportError[];
  degradation: DegradationReport;
}

export interface SessionCourse {
  id: string | null;
  name: string;
  credit: number;
  course_no: string | null;
  instructor: string | null;
  capacity: number | null;
  schedule: ScheduleSlot[];
  location: string | null;
  campus: string | null;
  category: string | null;
  semester: string | null;
  description: string | null;
}
