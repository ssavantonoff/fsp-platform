import { api } from "./api";
import type { MatchBreakdown, Page } from "./employer-needs";
import type { Grade, Skill, Specialization } from "./types";
import type { FspResultLevel } from "./fsp";

export type InvitationStatus = "SENT" | "VIEWED" | "ACCEPTED" | "DECLINED" | "WITHDRAWN";
export interface NeedSnapshot {
  need_id: string;
  position_title: string;
  specialization: Specialization;
  required_grade: Grade;
  target_experience_years: number | null;
  salary_from: string;
  salary_to: string;
  description: string;
  additional_requirements: string | null;
  must_have_skills: Skill[];
  nice_to_have_skills: Skill[];
  company_name: string;
}
export interface CandidateSnapshot {
  ranking_score?: number | null;
  fsp_verified?: boolean | null;
  fsp_achievement_score?: number | null;
  fsp_bonus?: number | null;
  competition_count?: number | null;
  best_result_level?: FspResultLevel | null;
  candidate_id: string;
  display_name: string;
  specialization: Specialization;
  verified_grade: Grade;
  normalized_assessment_score: number;
  assessment_verified_at: string | null;
  professional_fit_score: number;
  breakdown: MatchBreakdown;
}
export interface CandidateContact { first_name: string; last_name: string; email: string }
export interface EmployerContact { company_name: string; contact_person_name: string; email: string; website: string | null }
interface Invitation {
  id: string;
  need_id: string;
  status: InvitationStatus;
  message: string | null;
  need_snapshot: NeedSnapshot;
  sent_at: string;
  viewed_at: string | null;
  responded_at: string | null;
  withdrawn_at: string | null;
}
export interface EmployerInvitation extends Invitation {
  candidate_snapshot: CandidateSnapshot;
  candidate_contact?: CandidateContact | null;
}
export interface CandidateInvitation extends Invitation { employer_contact?: EmployerContact | null }
export type EmployerInvitationPage = Page<EmployerInvitation>;
export type CandidateInvitationPage = Page<CandidateInvitation>;
export const invitationStatusLabels: Record<InvitationStatus, string> = {
  SENT: "Отправлено", VIEWED: "Просмотрено", ACCEPTED: "Принято", DECLINED: "Отклонено", WITHDRAWN: "Отозвано",
};
export function invitationDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("ru-RU", { timeZone: "UTC" });
}
const employerPath = (id: string) => `/employer/invitations/${encodeURIComponent(id)}`;
const candidatePath = (id: string) => `/candidate/invitations/${encodeURIComponent(id)}`;
export function sendInvitation(needId: string, input: { candidate_id: string; message: string | null }): Promise<EmployerInvitation> {
  return api<EmployerInvitation>(`/employer/needs/${encodeURIComponent(needId)}/invitations`, {
    method: "POST", body: JSON.stringify({ candidate_id: input.candidate_id, message: input.message }),
  });
}
export function listEmployerInvitations(needId: string, limit = 20, offset = 0): Promise<EmployerInvitationPage> {
  return api<EmployerInvitationPage>(`/employer/needs/${encodeURIComponent(needId)}/invitations?limit=${limit}&offset=${offset}`);
}
export function getEmployerInvitation(id: string): Promise<EmployerInvitation> { return api<EmployerInvitation>(employerPath(id)); }
export function withdrawInvitation(id: string): Promise<EmployerInvitation> { return api<EmployerInvitation>(`${employerPath(id)}/withdraw`, { method: "POST" }); }
export function listCandidateInvitations(limit = 20, offset = 0): Promise<CandidateInvitationPage> {
  return api<CandidateInvitationPage>(`/candidate/invitations?limit=${limit}&offset=${offset}`);
}
export function getCandidateInvitation(id: string): Promise<CandidateInvitation> { return api<CandidateInvitation>(candidatePath(id)); }
export function viewInvitation(id: string): Promise<CandidateInvitation> { return api<CandidateInvitation>(`${candidatePath(id)}/view`, { method: "POST" }); }
export function acceptInvitation(id: string): Promise<CandidateInvitation> { return api<CandidateInvitation>(`${candidatePath(id)}/accept`, { method: "POST" }); }
export function declineInvitation(id: string): Promise<CandidateInvitation> { return api<CandidateInvitation>(`${candidatePath(id)}/decline`, { method: "POST" }); }
