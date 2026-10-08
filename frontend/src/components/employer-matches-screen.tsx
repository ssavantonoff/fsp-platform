"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/api";
import { getMatches, getNeed } from "@/employer-needs";
import { sendInvitation } from "@/invitations";
import type { EmployerCandidatePreview, EmployerNeed, FactorBreakdown, MatchesPage } from "@/employer-needs";
import { gradeLabels, specializationLabels } from "@/types";
import type { Skill } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";
import { FspExplanation } from "./fsp-profile";

export function formatScore(value: number): string {
  return Number.isFinite(value) ? value.toFixed(1) : "—";
}
function verificationDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toLocaleDateString("ru-RU", { timeZone: "UTC" });
}
function skillNames(skills: Skill[], empty = "—"): string {
  return skills.map((skill) => skill.name).join(", ") || empty;
}
function FactorValue({ factor }: { factor: FactorBreakdown }) {
  return <>{factor.active ? `${formatScore(factor.score)} / ${formatScore(factor.max)}` : "Не участвует в расчёте"}</>;
}
export function InvitationForm({ need, candidate, message, busy, success, error, onChange, onSubmit, onCancel }: {
  need: EmployerNeed; candidate: EmployerCandidatePreview; message: string; busy: boolean; success: string; error: unknown;
  onChange: (message: string) => void; onSubmit: () => void; onCancel: () => void;
}) {
  return <form className="invitation-form" onSubmit={(event) => { event.preventDefault(); if (!busy && message.length <= 2000) onSubmit(); }}>
    <h3>Пригласить: {candidate.display_name}</h3>
    <p>{need.position_title}</p><p>Зарплата: {need.salary_from}–{need.salary_to} ₽ (RUB, до вычета налогов)</p>
    <label>Сообщение (необязательно)<textarea value={message} maxLength={2000} disabled={busy} onChange={(event) => onChange(event.target.value)} /></label>
    <p className="hint">{message.length} / 2000</p>
    <Feedback error={error} success={success} />
    <div className="actions"><button disabled={busy || !!success || message.length > 2000} type="submit">{busy ? "Отправляем…" : "Отправить приглашение"}</button><button className="secondary" type="button" disabled={busy} onClick={onCancel}>{success ? "Закрыть" : "Отмена"}</button></div>
  </form>;
}
function InviteCandidate({ need, candidate }: { need: EmployerNeed; candidate: EmployerCandidatePreview }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const pending = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  async function submit() {
    if (pending.current || success || message.length > 2000) return;
    pending.current = true;
    setBusy(true); setError(null);
    try {
      await sendInvitation(need.id, { candidate_id: candidate.candidate_id, message: message === "" ? null : message });
      if (mounted.current) setSuccess("Приглашение отправлено");
    } catch (err) {
      if (mounted.current) setError(err instanceof ApiError && err.code === "invitation_conflict"
        ? new ApiError(err.status, err.code, "Новое приглашение недоступно. Проверьте историю приглашений по этой потребности.") : err);
    } finally {
      pending.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return open ? <InvitationForm need={need} candidate={candidate} message={message} busy={busy} error={error} success={success} onChange={setMessage} onSubmit={() => void submit()} onCancel={() => setOpen(false)} />
    : <div className="actions"><button disabled={!!success} onClick={() => setOpen(true)}>Пригласить</button><Feedback success={success} /></div>;
}
export function MatchCard({ candidate, need }: { candidate: EmployerCandidatePreview; need?: EmployerNeed }) {
  const date = verificationDate(candidate.assessment_verified_at);
  const breakdown = candidate.breakdown;
  return <article className="card match-card">
    <div className="matching-header">
      <h2>{candidate.display_name}</h2>
      <p className="match-score">Соответствие: {formatScore(candidate.professional_fit_score)} / 100 (Professional Fit)</p>
    </div>
    <FspExplanation signal={candidate} />
    <dl className="match-meta">
      <dt>Специализация</dt><dd>{specializationLabels[candidate.specialization]}</dd>
      <dt>Подтверждённый уровень</dt><dd>{gradeLabels[candidate.verified_grade]}</dd>
      <dt>Результат оценки</dt><dd>{candidate.normalized_assessment_score} / 100</dd>
      <dt>Опыт, лет</dt><dd>{candidate.years_of_experience ?? "не указан"}</dd>
    </dl>
    <p>{date ? `Компетенция подтверждена: ${date}` : "Дата подтверждения не указана"}</p>
    <dl className="match-skills">
      <dt>Навыки, указанные кандидатом</dt><dd>{skillNames(candidate.skills)}</dd>
      <dt>Обязательные навыки совпали</dt><dd>{skillNames(candidate.matched_must_have_skills)}</dd>
      <dt>Совпавшие желательные навыки</dt><dd>{skillNames(candidate.matched_nice_to_have_skills, "Нет совпадений")}</dd>
      <dt>Не хватает из желательных</dt><dd>{skillNames(candidate.missing_nice_to_have_skills, "Все желательные навыки совпали.")}</dd>
    </dl>
    <details className="match-breakdown">
      <summary>Почему такой результат</summary>
      <dl>
        <dt>Результат оценки</dt><dd><FactorValue factor={breakdown.assessment} /></dd>
        <dt>Уровень</dt><dd><FactorValue factor={breakdown.grade} /><p className="hint">{breakdown.grade.exact_match
          ? "Точное соответствие требуемому уровню" : "Допустимый более высокий уровень"}</p></dd>
        <dt>Желательные навыки</dt><dd><FactorValue factor={breakdown.nice_to_have} /><p className="hint">Совпало: {breakdown.nice_to_have.matched} из {breakdown.nice_to_have.total}</p></dd>
        <dt>Опыт</dt><dd><FactorValue factor={breakdown.experience} /></dd>
      </dl>
    </details>
    {need?.status === "ACTIVE" && <InviteCandidate need={need} candidate={candidate} />}
  </article>;
}
export function MatchingView({ need, result, loading, error, onRetry, offset = 0, onPageChange }: {
  need: EmployerNeed | null; result: MatchesPage | null; loading: boolean; error: unknown;
  onRetry: () => void; offset?: number; onPageChange?: (offset: number) => void;
}) {
  const path = need ? `/employer/needs/${encodeURIComponent(need.id)}` : null;
  const currentPage = result?.offset === offset ? result : null;
  const active = need?.status === "ACTIVE";
  return <section className="match-list">
    <section className="card match-card">
      <h1>Подбор кандидатов</h1>
      {need && <>
        <h2>{need.position_title}</h2>
        <dl>
          <dt>Специализация</dt><dd>{specializationLabels[need.specialization]}</dd>
          <dt>Требуемый уровень</dt><dd>{gradeLabels[need.required_grade]}</dd>
          <dt>Обязательные навыки</dt><dd>{skillNames(need.must_have_skills)}</dd>
          <dt>Желательные навыки</dt><dd>{skillNames(need.nice_to_have_skills)}</dd>
          <dt>Целевой опыт, лет</dt><dd>{need.target_experience_years ?? "Не учитывается"}</dd>
        </dl>
      </>}
      <div className="actions">
        {path && <Link href={`${path}/edit`}>{active ? "Редактировать потребность" : "К потребности"}</Link>}
        {path && <Link href={`${path}/invitations`}>Приглашения</Link>}
        <Link href="/employer/needs">К списку потребностей</Link>
      </div>
    </section>
    {loading ? <p role="status">Загрузка подбора…</p> : <>
      {error != null && <section className="card">
        <Feedback error={error} />
        {error instanceof ApiError && error.code === "need_not_found" && <p>Потребность не найдена.</p>}
        {error instanceof ApiError && error.code === "profile_not_found" && <p>Сначала заполните профиль компании. <Link href="/employer/edit">Заполнить профиль</Link></p>}
        <button onClick={onRetry}>Повторить</button>
      </section>}
      {need && !active ? <p className="notice">{need.status === "DRAFT"
        ? "Подбор доступен после активации потребности." : "Для закрытой потребности подбор недоступен."}</p>
        : active && error == null && (currentPage ? <>
          <p>Подходящих кандидатов: {currentPage.total}</p>
          {currentPage.items.length === 0 && currentPage.total === 0 && <section className="card">
            <p>Подходящих кандидатов пока нет.</p>
            <p>Проверьте требования или вернитесь к подбору позже.</p>
          </section>}
          {currentPage.items.map((candidate) => <MatchCard key={candidate.candidate_id} candidate={candidate} need={need} />)}
        </> : <p role="status">Загрузка подбора…</p>)}
    </>}
    {active && currentPage && error == null && onPageChange && <div className="actions match-pagination" aria-label="Страницы подбора">
      <button className="secondary" disabled={loading || offset <= 0} onClick={() => onPageChange(Math.max(0, offset - currentPage.limit))}>Назад</button>
      <button className="secondary" disabled={loading || offset + currentPage.items.length >= currentPage.total} onClick={() => onPageChange(offset + currentPage.limit)}>Далее</button>
    </div>}
  </section>;
}
export function EmployerMatchesScreen({ needId }: { needId: string }) {
  return <RoleGate role="EMPLOYER"><MatchesContent key={needId} needId={needId} /></RoleGate>;
}
function MatchesContent({ needId }: { needId: string }) {
  const [need, setNeed] = useState<EmployerNeed | null>(null);
  const [result, setResult] = useState<MatchesPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const generation = useRef(0);
  const limit = 20;
  const load = useCallback(() => {
    const request = ++generation.current;
    return getNeed(needId)
      .then(async (currentNeed) => {
        if (request !== generation.current) return;
        setNeed(currentNeed);
        if (currentNeed.status !== "ACTIVE") {
          setResult(null);
          return;
        }
        const matches = await getMatches(needId, limit, offset);
        if (request === generation.current) setResult(matches);
      })
      .catch(async (err: unknown) => {
        if (request !== generation.current) return;
        setError(err);
        setResult(null);
        if (err instanceof ApiError && err.code === "need_state_conflict") {
          // Refresh status once; a conflict must never trigger a matching retry loop.
          try {
            const currentNeed = await getNeed(needId);
            if (request === generation.current) setNeed(currentNeed);
          } catch { /* Keep the original error available for explicit retry. */ }
        }
      })
      .finally(() => {
        if (request === generation.current) setLoading(false);
      });
  }, [needId, offset]);
  useEffect(() => {
    const requests = generation;
    void load();
    return () => { requests.current++; };
  }, [load]);
  function retry() {
    setLoading(true);
    setError(null);
    setResult(null);
    void load();
  }
  function changePage(nextOffset: number) {
    setLoading(true);
    setError(null);
    setResult(null);
    generation.current++;
    setOffset(nextOffset);
  }
  return <MatchingView need={need} result={result} loading={loading} error={error}
    onRetry={retry} offset={offset} onPageChange={changePage} />;
}
