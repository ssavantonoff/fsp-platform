import { api } from "./api";
import type { CandidateProfile, Grade, Specialization } from "./types";

export type AssessmentStatus = "IN_PROGRESS" | "PASSED" | "FAILED";
export interface AssessmentQuestion {
  attempt_question_id: string;
  question_id: string;
  position: number;
  competency: string;
  difficulty: "BASIC" | "APPLIED" | "ADVANCED";
  prompt: string;
  options: { id: string; text: string }[];
  selected_option_id: string | null;
}
export interface AttemptSummary {
  id: string;
  specialization: Specialization;
  target_grade: Grade;
  status: AssessmentStatus;
  completion_reason: "SUBMITTED" | "TIMEOUT" | null;
  started_at: string;
  expires_at: string;
  finished_at: string | null;
  normalized_assessment_score: number | null;
  competency_scores: Record<string, number> | null;
  available_at: string | null;
}
export interface Attempt extends AttemptSummary {
  server_now: string;
  questions: AssessmentQuestion[];
  verification: CandidateProfile;
}
export interface GradeAvailability {
  grade: Grade;
  available: boolean;
  reason: string | null;
  available_at: string | null;
}
export interface Availability {
  specialization: Specialization;
  grades: GradeAvailability[];
  active_attempt_id: string | null;
  server_now: string;
  verification: CandidateProfile;
}
export const competencyLabels: Record<string, string> = {
  PROGRAMMING: "Программирование",
  HTTP_API: "HTTP и API",
  DATABASES: "Базы данных",
  ARCHITECTURE: "Архитектура",
  TESTING_SECURITY_DEBUGGING: "Тестирование, безопасность и отладка",
  JAVASCRIPT_TYPESCRIPT: "JavaScript и TypeScript",
  REACT_UI: "React и интерфейсы",
  BROWSER_WEB: "Браузер и веб",
  STATE_DATA: "Состояние и данные",
  TESTING_PERFORMANCE_ACCESSIBILITY:
    "Тестирование, производительность и доступность",
  PYTHON_DATA: "Python и данные",
  STATISTICS_ML: "Статистика и машинное обучение",
  DATA_PROCESSING_SQL: "Обработка данных и SQL",
  MODELING_EVALUATION: "Моделирование и оценка",
  MLOPS_PRODUCTION: "MLOps и эксплуатация",
};
export const availabilityLabels: Record<string, string> = {
  EMAIL_NOT_VERIFIED: "Подтвердите email перед началом теста.",
  CONSENT_REQUIRED: "Дайте согласие на обработку данных в профиле.",
  IN_PROGRESS: "Сначала завершите активную попытку.",
  LOWER_THAN_VERIFIED: "Уровень ниже уже подтверждённого недоступен.",
  UNAVAILABLE: "Банк вопросов для этой специализации пока недоступен.",
  COOLDOWN: "Повторная попытка пока недоступна.",
};
export function dateLabel(value: string | null) {
  return value ? new Date(value).toLocaleString("ru-RU") : "—";
}
export function availabilityLabel(grade: GradeAvailability) {
  if (grade.available) return "Можно начать тест";
  const message = availabilityLabels[grade.reason ?? ""] ?? "Тест недоступен.";
  return grade.available_at
    ? `${message} Доступно с ${dateLabel(grade.available_at)}`
    : message;
}
export interface ServerClock {
  remainingMs: number;
  receivedAt: number;
}
export function serverClock(
  attempt: Pick<Attempt, "expires_at" | "server_now">,
  requestStartedAt: number,
): ServerClock {
  return {
    remainingMs: Math.max(
      0,
      Date.parse(attempt.expires_at) - Date.parse(attempt.server_now),
    ),
    receivedAt: requestStartedAt,
  };
}
export function secondsRemaining(clock: ServerClock, monotonicNow: number) {
  return Math.max(
    0,
    Math.ceil(
      (clock.remainingMs - Math.max(0, monotonicNow - clock.receivedAt)) / 1000,
    ),
  );
}
export function timerLabel(seconds: number) {
  return `${Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;
}
const base = "/candidate/assessments";
export async function loadAttempt(id: string) {
  const began = performance.now();
  const attempt = await api<Attempt>(`${base}/${encodeURIComponent(id)}`);
  return { attempt, clock: serverClock(attempt, began) };
}
export async function saveAssessmentAnswer(
  attemptId: string,
  questionId: string,
  optionId: string,
) {
  return api<Attempt>(
    `${base}/${encodeURIComponent(attemptId)}/answers/${encodeURIComponent(questionId)}`,
    {
      method: "PUT",
      body: JSON.stringify({ selected_option_id: optionId }),
    },
  );
}
export async function submitAssessment(attemptId: string) {
  return api<Attempt>(`${base}/${encodeURIComponent(attemptId)}/submit`, {
    method: "POST",
  });
}

// A delayed autosave response must never reopen an already finalized screen.
export function applySavedAttempt(
  current: Attempt | null,
  saved: Attempt,
): Attempt {
  return current && current.status !== "IN_PROGRESS" ? current : saved;
}
