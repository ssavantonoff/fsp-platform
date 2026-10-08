import { api } from "./api";

export type FspResultLevel = "PARTICIPANT" | "FINALIST" | "PRIZE_WINNER" | "WINNER";
export interface FspSummary {
  fsp_verified: boolean;
  fsp_achievement_score: number;
  fsp_bonus: number;
  competition_count: number;
  best_result_level: FspResultLevel | null;
}
export interface FspAchievement {
  competition_name: string;
  discipline: string;
  year: number | null;
  event_date: string | null;
  result_level: FspResultLevel;
  placement: number | null;
  scope: "INDIVIDUAL" | "TEAM" | null;
}
export interface FspStatus extends FspSummary {
  provider: "MOCK";
  fsp_id: string | null;
  fsp_verified_at: string | null;
  fsp_synced_at: string | null;
  achievements: FspAchievement[];
}
export const fspResultLabels: Record<FspResultLevel, string> = {
  PARTICIPANT: "Участник", FINALIST: "Финалист", PRIZE_WINNER: "Призёр", WINNER: "Победитель",
};
export const getFspStatus = () => api<FspStatus>("/candidate/fsp");
export const verifyFsp = () => api<FspStatus>("/candidate/fsp/verify", { method: "POST", body: "{}" });
export const refreshFsp = () => api<FspStatus>("/candidate/fsp/refresh", { method: "POST", body: "{}" });
export const unlinkFsp = () => api<FspStatus>("/candidate/fsp/verification", { method: "DELETE", body: "{}" });
