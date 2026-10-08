"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/api";
import {
  activateNeed, closeNeed, createNeed, defaultNeedFormValues, getNeed,
  listNeeds, needActions, needFormValues, needPayload, updateNeed, validateNeedForm,
} from "@/employer-needs";
import type { EmployerNeed, Page } from "@/employer-needs";
import { gradeLabels, specializationLabels } from "@/types";
import type { Skill } from "@/types";
import { RoleGate } from "./auth";
import { EmployerNeedForm } from "./employer-need-form";
import type { NeedFormProps } from "./employer-need-form";
import { Feedback } from "./feedback";

const statusLabels = { DRAFT: "Черновик", ACTIVE: "Активна", CLOSED: "Закрыта" };
function NeedSummary({ need }: { need: EmployerNeed }) {
  return <dl className="need-meta">
    <dt>Специализация</dt><dd>{specializationLabels[need.specialization]}</dd>
    <dt>Требуемый уровень</dt><dd>{gradeLabels[need.required_grade]}</dd>
    <dt>Зарплата</dt><dd>{need.salary_from}–{need.salary_to} ₽ (RUB, до вычета налогов)</dd>
    <dt>Целевой опыт, лет</dt><dd>{need.target_experience_years ?? "Не учитывается"}</dd>
    <dt>Обязательные навыки</dt><dd>{need.must_have_skills.map((skill) => skill.name).join(", ") || "—"}</dd>
    <dt>Желательные навыки</dt><dd>{need.nice_to_have_skills.map((skill) => skill.name).join(", ") || "—"}</dd>
  </dl>;
}
function NeedError({ error }: { error: unknown }) {
  return <>
    <Feedback error={error} />
    {error instanceof ApiError && error.code === "profile_not_found" && <p>
      Сначала заполните профиль компании. <Link href="/employer/edit">Заполнить профиль</Link>
    </p>}
    {error instanceof ApiError && error.code === "need_not_found" && <p>Потребность не найдена.</p>}
  </>;
}
export function NeedsListView({ items, loading, error, onRetry, onAction, busyIds = [] }: {
  items: EmployerNeed[]; loading: boolean; error: unknown; onRetry: () => void;
  onAction: (id: string, action: "activate" | "close") => void;
  busyIds?: string[];
}) {
  return <section className="need-list">
    <div className="need-card-header"><h1>Потребности</h1><Link className="button" href="/employer/needs/new">Новая потребность</Link></div>
    {loading ? <p role="status">Загрузка потребностей…</p> : <>
      {error != null && <section className="card"><NeedError error={error} /><button onClick={onRetry}>Повторить</button></section>}
      {!items.length && error == null && <section className="card"><p>У вас пока нет потребностей.</p><Link className="button" href="/employer/needs/new">Создать потребность</Link></section>}
      {items.map((need) => {
        const actions = needActions(need.status);
        const busy = busyIds.includes(need.id);
        const path = `/employer/needs/${encodeURIComponent(need.id)}`;
        return <article className="card need-card" key={need.id}>
          <div className="need-card-header"><h2>{need.position_title}</h2><span className="need-status">{statusLabels[need.status]}</span></div>
          <NeedSummary need={need} />
          <div className="actions need-actions">
            <Link href={`${path}/invitations`}>Приглашения</Link>
            {actions.edit && (busy ? <span>Редактировать</span> : <Link href={`${path}/edit`}>Редактировать</Link>)}
            {actions.matches && (busy ? <span>Подбор кандидатов</span> : <Link href={`${path}/matches`}>Подбор кандидатов</Link>)}
            {actions.activate && <button disabled={busy} onClick={() => onAction(need.id, "activate")}>{busy ? "Активируем…" : "Активировать"}</button>}
            {actions.close && <button className="secondary" disabled={busy} onClick={() => onAction(need.id, "close")}>{busy ? "Закрываем…" : "Закрыть"}</button>}
            {need.status === "CLOSED" && <p className="hint">Потребность закрыта.</p>}
          </div>
        </article>;
      })}
    </>}
  </section>;
}
export function EmployerNeedsScreen() {
  return <RoleGate role="EMPLOYER"><NeedsContent /></RoleGate>;
}
function NeedsContent() {
  const [page, setPage] = useState<Page<EmployerNeed> | null>(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [busyIds, setBusyIds] = useState<string[]>([]);
  const pending = useRef(new Set<string>());
  const generation = useRef(0);
  const limit = 20;
  const load = useCallback(async () => {
    const request = ++generation.current;
    try {
      const result = await listNeeds(limit, offset);
      if (request === generation.current) setPage(result);
    } catch (err) {
      if (request === generation.current) setError(err);
    } finally {
      if (request === generation.current) setLoading(false);
    }
  }, [offset]);
  useEffect(() => {
    const requests = generation;
    void load();
    return () => { requests.current++; };
  }, [load]);
  function retry() {
    setLoading(true);
    setError(null);
    void load();
  }
  async function action(id: string, action: "activate" | "close") {
    if (pending.current.has(id)) return;
    if (action === "close" && !window.confirm("Закрыть потребность? После закрытия редактирование и подбор будут недоступны.")) return;
    pending.current.add(id);
    setBusyIds([...pending.current]);
    setError(null);
    try {
      const saved = await (action === "activate" ? activateNeed(id) : closeNeed(id));
      setPage((current) => current ? { ...current, items: current.items.map((item) => item.id === saved.id ? saved : item) } : current);
    } catch (err) {
      setError(err);
    } finally {
      pending.current.delete(id);
      setBusyIds([...pending.current]);
    }
  }
  const currentPage = page?.offset === offset ? page : null;
  return <>
    <NeedsListView
      items={currentPage?.items ?? []}
      loading={loading}
      error={error}
      onRetry={retry}
      onAction={(id, kind) => void action(id, kind)}
      busyIds={busyIds} />
    {currentPage && <div className="actions need-pagination" aria-label="Страницы потребностей">
      <button
        className="secondary"
        disabled={loading || offset <= 0}
        onClick={() => {
          setLoading(true);
          setError(null);
          setOffset(Math.max(0, offset - limit));
        }}>Назад</button>
      <span>Всего: {currentPage.total}</span>
      <button
        className="secondary"
        disabled={loading || offset + currentPage.items.length >= currentPage.total}
        onClick={() => {
          setLoading(true);
          setError(null);
          setOffset(offset + limit);
        }}>Далее</button>
    </div>}
  </>;
}
export function NeedEditorView({ need, loading, error, form, onRetry, ready = true, success = "" }: {
  need: EmployerNeed | null; loading: boolean; error: unknown;
  form: NeedFormProps; onRetry: () => void; ready?: boolean; success?: string;
}) {
  if (loading) return <p role="status">Загрузка потребности…</p>;
  const missing = error instanceof ApiError && error.code === "need_not_found";
  return <section className="card need-card">
    <h1>{need ? need.position_title : "Новая потребность"}</h1>
    <NeedError error={error} />
    {!ready && error != null && !missing && <button onClick={onRetry}>Повторить</button>}
    {need?.status === "CLOSED" ? <>
      <p className="notice">Потребность закрыта. Редактирование и подбор недоступны.</p>
      <NeedSummary need={need} />
      <dl><dt>Описание</dt><dd>{need.description}</dd><dt>Дополнительные требования</dt><dd>{need.additional_requirements || "—"}</dd></dl>
    </> : ready && !missing && <>
      {need && <p className="notice">{need.status === "ACTIVE"
        ? "Потребность активна. После сохранения следующий подбор будет рассчитан по обновлённым требованиям."
        : "Черновик можно редактировать. После активации станет доступен подбор кандидатов."}</p>}
      <Feedback success={success} />
      <EmployerNeedForm {...form} submitLabel={need ? "Сохранить" : "Создать потребность"} />
    </>}
    <p><Link href="/employer/needs">К списку потребностей</Link></p>
    {need && <p><Link href={`/employer/needs/${encodeURIComponent(need.id)}/invitations`}>Приглашения</Link></p>}
  </section>;
}
export function EmployerNeedEditor({ needId }: { needId?: string }) {
  return <RoleGate role="EMPLOYER"><NeedEditorContent key={needId ?? "new"} needId={needId} /></RoleGate>;
}
function NeedEditorContent({ needId }: { needId?: string }) {
  const router = useRouter();
  const [need, setNeed] = useState<EmployerNeed | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [values, setValues] = useState(defaultNeedFormValues);
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const saving = useRef(false);
  const createdNeedId = useRef<string | null>(null);
  const generation = useRef(0);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const load = useCallback(() => {
    const request = ++generation.current;
    return Promise.all([
      needId ? getNeed(needId) : Promise.resolve(null),
      api<Skill[]>("/skills"),
    ])
      .then(([existing, catalog]) => {
        if (request !== generation.current) return;
        // Preserve referenced skills if the catalog is unexpectedly incomplete.
        const known = new Set(catalog.map((skill) => skill.id));
        const available = [...catalog];
        for (const skill of [
          ...(existing?.must_have_skills ?? []),
          ...(existing?.nice_to_have_skills ?? []),
        ]) {
          if (!known.has(skill.id)) {
            available.push(skill);
            known.add(skill.id);
          }
        }
        setNeed(existing);
        setSkills(available);
        if (existing) setValues(needFormValues(existing));
        setReady(true);
      })
      .catch ((err) => {
        if (request === generation.current) setError(err);
      })
      .finally(() => {
        if (request === generation.current) setLoading(false);
      });
  }, [needId]);
  useEffect(() => {
    const requests = generation;
    void load();
    return () => { requests.current++; };
  }, [load]);
  function retry() {
    setLoading(true);
    setError(null);
    void load();
  }
  async function submit() {
    if (saving.current || !ready || need?.status === "CLOSED" || Object.keys(validateNeedForm(values)).length) return;
    const targetId = needId ?? createdNeedId.current;
    saving.current = true;
    setBusy(true);
    setError(null);
    setSuccess("");
    try {
      const payload = needPayload(values);
      let saved: EmployerNeed;
      if (targetId) {
        saved = await updateNeed(targetId, payload);
      } else {
        saved = await createNeed(payload);
        // Navigation can leave this create component mounted after the response.
        createdNeedId.current = saved.id;
      }
      setNeed(saved);
      setValues(needFormValues(saved));
      if (!targetId) router.push(`/employer/needs/${encodeURIComponent(saved.id)}/edit`);
      else setSuccess("Потребность сохранена.");
    } catch (err) {
      setError(err);
      if (targetId && err instanceof ApiError && err.code === "need_state_conflict") {
        try { setNeed(await getNeed(targetId)); }
        catch { /* Keep the original conflict and user input available for retry. */ }
      }
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }
  return <NeedEditorView
    need={need}
    loading={loading}
    error={error}
    ready={ready}
    success={success}
    onRetry={retry}
    form={{
      values,
      skills,
      busy,
      errors: validateNeedForm(values),
      onChange: (next) => {
        setValues(next);
        setSuccess("");
      },
      onSubmit: () => void submit(),
    }} />;
}
