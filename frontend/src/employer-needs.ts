import { api } from "./api";
import type { Grade, Role, Skill, Specialization } from "./types";

export type NeedStatus = "DRAFT" | "ACTIVE" | "CLOSED";
export interface NeedWrite {
  position_title: string;
  specialization: Specialization;
  required_grade: Grade;
  target_experience_years: number | null;
  salary_from: string;
  salary_to: string;
  description: string;
  additional_requirements: string | null;
  must_have_skill_ids: string[];
  nice_to_have_skill_ids: string[];
}
export interface EmployerNeed {
  id: string;
  employer_id: string;
  position_title: string;
  specialization: Specialization;
  required_grade: Grade;
  target_experience_years: number | null;
  salary_from: string;
  salary_to: string;
  description: string;
  additional_requirements: string | null;
  status: NeedStatus;
  created_at: string;
  updated_at: string;
  must_have_skills: Skill[];
  nice_to_have_skills: Skill[];
}
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
export interface FactorBreakdown {
  score: number;
  max: number;
  active: boolean;
}
export interface GradeBreakdown extends FactorBreakdown {
  exact_match: boolean;
}
export interface NiceToHaveBreakdown extends FactorBreakdown {
  matched: number;
  total: number;
}
export interface MatchBreakdown {
  assessment: FactorBreakdown;
  grade: GradeBreakdown;
  nice_to_have: NiceToHaveBreakdown;
  experience: FactorBreakdown;
}
export interface EmployerCandidatePreview {
  candidate_id: string;
  display_name: string;
  specialization: Specialization;
  verified_grade: Grade;
  skills: Skill[];
  years_of_experience: number | null;
  normalized_assessment_score: number;
  assessment_verified_at: string | null;
  professional_fit_score: number;
  breakdown: MatchBreakdown;
  matched_must_have_skills: Skill[];
  matched_nice_to_have_skills: Skill[];
  missing_nice_to_have_skills: Skill[];
}
export type MatchesPage = Page<EmployerCandidatePreview>;
export interface NeedFormValues extends Omit<NeedWrite, "target_experience_years" | "additional_requirements"> {
  target_experience_years: string;
  additional_requirements: string;
}
export function defaultNeedFormValues(): NeedFormValues {
  return {
    position_title: "",
    specialization: "BACKEND",
    required_grade: "MIDDLE",
    target_experience_years: "",
    salary_from: "",
    salary_to: "",
    description: "",
    additional_requirements: "",
    must_have_skill_ids: [],
    nice_to_have_skill_ids: [],
  };
}
export function needFormValues(need: EmployerNeed): NeedFormValues {
  return {
    position_title: need.position_title,
    specialization: need.specialization,
    required_grade: need.required_grade,
    target_experience_years: need.target_experience_years === null ? "" : String(need.target_experience_years),
    salary_from: need.salary_from,
    salary_to: need.salary_to,
    description: need.description,
    additional_requirements: need.additional_requirements ?? "",
    must_have_skill_ids: need.must_have_skills.map((skill) => skill.id),
    nice_to_have_skill_ids: need.nice_to_have_skills.map((skill) => skill.id),
  };
}
// Compare integer cents without converting Decimal transport values to floats.
function salaryCents(value: string): bigint | null {
  const text = value.trim();
  if (!/^\d+(?:\.\d{1,2})?$/.test(text)) return null;
  const [whole, fraction = ""] = text.split(".");
  const significantWhole = whole.replace(/^0+/, "") || "0";
  if (significantWhole.length > 10) return null;
  return BigInt(significantWhole) * 100n + BigInt(fraction.padEnd(2, "0"));
}
export function validateNeedForm(values: NeedFormValues): Record<string, string> {
  const errors: Record<string, string> = {};
  const title = values.position_title.trim();
  if (!title) errors.position_title = "Укажите позицию.";
  else if (title.length > 200) errors.position_title = "Позиция не должна превышать 200 символов.";
  if (!values.description.trim()) errors.description = "Добавьте описание.";
  const from = salaryCents(values.salary_from);
  const to = salaryCents(values.salary_to);
  if (from === null) errors.salary_from = "Укажите корректную зарплату от (до 10 цифр до точки и 2 после).";
  if (to === null) errors.salary_to = "Укажите корректную зарплату до (до 10 цифр до точки и 2 после).";
  if (from !== null && to !== null && from > to) errors.salary_from = "Зарплата от не может быть больше зарплаты до.";
  const target = values.target_experience_years.trim();
  if (target && (!/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(target) || !Number.isFinite(Number(target)) || Number(target) < 0))
    errors.target_experience_years = "Опыт должен быть неотрицательным числом.";
  const must = values.must_have_skill_ids;
  const nice = values.nice_to_have_skill_ids;
  if (!must.length) errors.must_have_skill_ids = "Выберите хотя бы один обязательный навык.";
  if (new Set(must).size !== must.length) errors.must_have_skill_ids = "Обязательные навыки не должны повторяться.";
  if (new Set(nice).size !== nice.length) errors.nice_to_have_skill_ids = "Желательные навыки не должны повторяться.";
  if (must.some((id) => nice.includes(id))) {
    errors.must_have_skill_ids = errors.nice_to_have_skill_ids = "Навык не может быть одновременно обязательным и желательным.";
  }
  return errors;
}
export function needPayload(values: NeedFormValues): NeedWrite {
  return {
    position_title: values.position_title.trim(),
    specialization: values.specialization,
    required_grade: values.required_grade,
    target_experience_years: values.target_experience_years.trim() === "" ? null : Number(values.target_experience_years.trim()),
    salary_from: values.salary_from.trim(),
    salary_to: values.salary_to.trim(),
    description: values.description.trim(),
    additional_requirements: values.additional_requirements.trim() || null,
    must_have_skill_ids: [...values.must_have_skill_ids],
    nice_to_have_skill_ids: [...values.nice_to_have_skill_ids],
  };
}
const base = "/employer/needs";
const needPath = (id: string) => `${base}/${encodeURIComponent(id)}`;
export function listNeeds(limit = 20, offset = 0): Promise<Page<EmployerNeed>> {
  return api<Page<EmployerNeed>>(`${base}?limit=${limit}&offset=${offset}`);
}
export function getNeed(id: string): Promise<EmployerNeed> {
  return api<EmployerNeed>(needPath(id));
}
export function getMatches(id: string, limit = 20, offset = 0): Promise<MatchesPage> {
  return api<MatchesPage>(`${needPath(id)}/matches?limit=${limit}&offset=${offset}`);
}
export function createNeed(data: NeedWrite): Promise<EmployerNeed> {
  return api<EmployerNeed>(base, { method: "POST", body: JSON.stringify(data) });
}
export function updateNeed(id: string, data: NeedWrite): Promise<EmployerNeed> {
  return api<EmployerNeed>(needPath(id), { method: "PUT", body: JSON.stringify(data) });
}
export function activateNeed(id: string): Promise<EmployerNeed> {
  return api<EmployerNeed>(`${needPath(id)}/activate`, { method: "POST" });
}
export function closeNeed(id: string): Promise<EmployerNeed> {
  return api<EmployerNeed>(`${needPath(id)}/close`, { method: "POST" });
}
export function needActions(status: NeedStatus) {
  return {
    edit: status !== "CLOSED",
    activate: status === "DRAFT",
    close: status === "ACTIVE",
    matches: status === "ACTIVE",
  };
}
export function needsNavigationVisible(role: Role | null): boolean {
  return role === "EMPLOYER";
}
