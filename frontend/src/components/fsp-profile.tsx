"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { fspResultLabels, getFspStatus, refreshFsp, unlinkFsp, verifyFsp } from "@/fsp";
import type { FspStatus, FspSummary } from "@/fsp";
import { invitationDate } from "@/invitations";
import { Feedback } from "./feedback";

type Action = "verify" | "refresh" | "unlink";
export function FspExplanation({ signal }: { signal: Partial<{ [K in keyof FspSummary]: FspSummary[K] | null }> & { ranking_score?: number | null } }) {
  if (signal.ranking_score == null && signal.fsp_verified == null) return null;
  return <section className="fsp-explanation" aria-label="Рейтинг и ФСП">
    {signal.ranking_score != null && <p><strong>Ranking Score: {signal.ranking_score.toFixed(1)} / 100</strong></p>}
    {signal.fsp_verified === true ? <>
      <p>Подтверждено через ФСП · MOCK / прототип</p>
      <p>Участий: {signal.competition_count} · Лучший результат: {signal.best_result_level ? fspResultLabels[signal.best_result_level] : "Нет достижений"}</p>
      <p>Достижения: {signal.fsp_achievement_score?.toFixed(1)} / 100 · Вклад ФСП: {signal.fsp_bonus?.toFixed(1)} / 5</p>
    </> : <p>ФСП не подтверждена · Вклад ФСП: 0 / 5</p>}
    <p className="hint">Ranking V2: 95% Professional Fit + до 5 баллов за подтверждённые достижения ФСП.</p>
  </section>;
}
export function FspProfileView({ status, loading, busy, error, success, onRetry, onAction }: {
  status: FspStatus | null; loading: boolean; busy: boolean; error: unknown; success: string;
  onRetry: () => void; onAction: (action: Action) => void;
}) {
  return <section className="fsp-profile" aria-label="Профиль ФСП">
    <h2>Профиль ФСП</h2>
    <p className="hint">MOCK / прототип интеграции. Проверка использует тестовый реестр, а не реальную связь с ФСП.</p>
    {loading ? <p role="status">Загрузка ФСП…</p> : <>
      <Feedback error={error} success={success} />
      {error != null && <button className="secondary" disabled={busy} onClick={onRetry}>Повторить</button>}
      {status && <>
        <dl><dt>Введённый FSP ID</dt><dd>{status.fsp_id || "Не указан"}</dd>
          <dt>Проверка реестром</dt><dd>{status.fsp_verified ? "Подтверждено через ФСП (MOCK)" : "ID не подтверждён; бонус отсутствует"}</dd>
          {status.fsp_verified && <><dt>Подтверждён (UTC)</dt><dd>{status.fsp_verified_at ? invitationDate(status.fsp_verified_at) : "—"}</dd>
            <dt>Последняя синхронизация (UTC)</dt><dd>{status.fsp_synced_at ? invitationDate(status.fsp_synced_at) : "—"}</dd>
            <dt>Достижения / вклад ФСП</dt><dd>{status.fsp_achievement_score.toFixed(1)} / 100 · {status.fsp_bonus.toFixed(1)} / 5</dd></>}
        </dl>
        {status.fsp_verified && (status.achievements.length ? <ul>{status.achievements.map((item, index) => <li key={index}>
          <strong>{item.competition_name}</strong> · {item.discipline} · {item.year ?? "Год не указан"}
          {item.event_date && <> · {invitationDate(item.event_date)}</>} · {fspResultLabels[item.result_level]}
          {item.placement != null && <> · Место: {item.placement}</>}
          {item.scope && <> · {item.scope === "TEAM" ? "Командный результат" : "Индивидуальный результат"}</>}
        </li>)}</ul> : <p>Подтверждённых достижений пока нет.</p>)}
        <div className="actions">
          {status.fsp_verified ? <><button disabled={busy} onClick={() => onAction("refresh")}>Обновить достижения</button><button disabled={busy} className="secondary" onClick={() => onAction("unlink")}>Снять проверку</button></>
            : <button disabled={busy || !status.fsp_id} onClick={() => onAction("verify")}>Проверить FSP ID</button>}
          <Link href="/candidate/edit">Изменить FSP ID в профиле</Link>
        </div>
        {busy && <p role="status">Обновляем данные ФСП…</p>}
      </>}
    </>}
  </section>;
}
export function FspProfile() {
  const [status, setStatus] = useState<FspStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const generation = useRef(0);
  const pending = useRef(false);
  const mounted = useRef(true);
  const load = useCallback(() => {
    const request = ++generation.current;
    return getFspStatus().then(
      (result) => { if (mounted.current && request === generation.current) setStatus(result); },
      (err) => { if (mounted.current && request === generation.current) setError(err); },
    ).finally(() => { if (mounted.current && request === generation.current) setLoading(false); });
  }, []);
  useEffect(() => {
    const requestGeneration = generation;
    mounted.current = true;
    void load();
    return () => { mounted.current = false; requestGeneration.current++; };
  }, [load]);
  function retry() {
    if (pending.current || !mounted.current) return;
    setLoading(true); setError(null);
    void load();
  }
  async function act(action: Action) {
    if (pending.current || !mounted.current) return;
    pending.current = true;
    generation.current++;
    setBusy(true); setError(null); setSuccess("");
    try {
      const result = await ({ verify: verifyFsp, refresh: refreshFsp, unlink: unlinkFsp })[action]();
      if (mounted.current) {
        setStatus(result);
        setSuccess(action === "unlink" ? "Проверка ФСП снята" : "Данные ФСП подтверждены (MOCK)");
      }
    } catch (err) { if (mounted.current) setError(err); }
    finally { pending.current = false; if (mounted.current) setBusy(false); }
  }
  return <FspProfileView status={status} loading={loading} busy={busy} error={error} success={success} onRetry={retry} onAction={(action) => void act(action)} />;
}
