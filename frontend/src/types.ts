export type Role = "CANDIDATE" | "EMPLOYER";
export type Grade = "JUNIOR" | "MIDDLE" | "SENIOR";
export type Specialization = "BACKEND" | "FRONTEND" | "DATA_ML";

export interface User {
  id: string;
  email: string;
  role: Role;
  email_verified: boolean;
}
export interface Skill {
  id: string;
  name: string;
}
export interface CandidateProfile {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  city: string | null;
  about: string | null;
  specialization: Specialization;
  declared_grade: Grade;
  verified_grade: Grade | null;
  normalized_assessment_score: number | null;
  assessment_verified_at: string | null;
  years_of_experience: number | null;
  fsp_id: string | null;
  personal_data_consent: boolean;
  personal_data_consent_at: string | null;
  skills: Skill[];
}
export interface EmployerProfile {
  id: string;
  user_id: string;
  company_name: string;
  company_description: string | null;
  website: string | null;
  contact_person_name: string;
}
export const gradeLabels: Record<Grade, string> = {
  JUNIOR: "Junior",
  MIDDLE: "Middle",
  SENIOR: "Senior",
};
export const specializationLabels: Record<Specialization, string> = {
  BACKEND: "Backend",
  FRONTEND: "Frontend",
  DATA_ML: "Data / ML",
};
