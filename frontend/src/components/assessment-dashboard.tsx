"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/api";
import { availabilityLabel } from "@/assessment";
import type { Attempt, Availability } from "@/assessment";
import { gradeLabels, specializationLabels } from "@/types";
import type { CandidateProfile, Grade } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";
import { CurrentQualification } from "./assessment-result";

export function AssessmentDashboardSummary({
  profile,
}: {
  profile: CandidateProfile;
}) {
  return (
    <div className="assessment-summary">
      <section aria-label="Заявленный уровень" className="assessment-declared">
        <h2>Заявленный уровень</h2>
        <p>{gradeLabels[profile.declared_grade]}</p>
        <p className="hint">Указан вами в профиле. Это не подтверждение квалификации.</p>
      </section>
      <CurrentQualification verification={profile} />
    </div>
  );
}

export function AssessmentDashboard() {
  return (
    <RoleGate role="CANDIDATE">
      <Dashboard />
    </RoleGate>
  );
}
function Dashboard() {
  const router = useRouter();
  const [data, setData] = useState<Availability | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Grade | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(
    () =>
      api<Availability>("/candidate/assessments/availability")
        .then((value) => {
          setData(value);
          setError(null);
        })
        .catch(setError)
        .finally(() => setLoading(false)),
    [],
  );
  useEffect(() => {
    void load();
  }, [load]);
  async function start() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const attempt = await api<Attempt>("/candidate/assessments", {
        method: "POST",
        body: JSON.stringify({ target_grade: selected }),
      });
      router.push(`/candidate/assessment/${attempt.id}`);
    } catch (err) {
      await load();
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return <AssessmentDashboardView
    data={data}
    error={error}
    loading={loading}
    selected={selected}
    busy={busy}
    onSelect={(grade) => {
      setSelected(grade);
      setError(null);
    }}
    onStart={() => void start()}
    onRetry={() => {
      setLoading(true);
      void load();
    }}
    onRefresh={() => void load()} />;
}

export function AssessmentDashboardView({ data, error, loading, selected, busy, onSelect, onStart, onRetry, onRefresh }: {
  data: Availability | null;
  error: unknown;
  loading: boolean;
  selected: Grade | null;
  busy: boolean;
  onSelect: (grade: Grade) => void;
  onStart: () => void;
  onRetry: () => void;
  onRefresh: () => void;
}) {
  if (loading) return <p className="assessment-loading" role="status">Загрузка доступных тестов…</p>;
  if (error instanceof ApiError && error.code === "profile_not_found")
    return (
      <section className="card assessment-screen">
        <h1>Подтверждение уровня</h1>
        <p>Сначала заполните профиль кандидата.</p>
        <Link className="button" href="/candidate/edit">Создать профиль</Link>
      </section>
    );
  if (!data)
    return (
      <section className="card assessment-screen">
        <h1>Подтверждение уровня</h1>
        <Feedback error={error} />
        <button onClick={onRetry}>
          Повторить
        </button>
      </section>
    );
  const profile = data.verification;
  const choice = data.grades.find((g) => g.grade === selected);
  return (
    <section className="card assessment-screen">
      <div className="assessment-heading">
        <div>
          <p className="eyebrow">Assessment</p>
          <h1>Подтверждение уровня</h1>
          <p>Пройдите тест по своей специализации, чтобы подтвердить профессиональный уровень.</p>
        </div>
        <span className="badge">{specializationLabels[data.specialization]}</span>
      </div>
      <AssessmentDashboardSummary profile={profile} />
      <div className="actions">
        <Link className="button secondary" href="/candidate">Профиль</Link>
        <Link className="button secondary" href="/candidate/assessment/history">История попыток</Link>
      </div>
      {data.active_attempt_id && (
        <section className="notice assessment-active" aria-label="Активная попытка">
          <h2>Тест уже начат</h2>
          <p>У вас есть активный тест. Вернитесь к вопросам, чтобы продолжить.</p>
          <Link className="button" href={`/candidate/assessment/${data.active_attempt_id}`}>
            Продолжить тест
          </Link>
        </section>
      )}
      <div className="grade-cards">
        {data.grades.map((grade) => (
          <article className="grade-card assessment-grade-card" data-selected={selected === grade.grade} key={grade.grade}>
            <h2>{gradeLabels[grade.grade]}</h2>
            {grade.grade === profile.verified_grade && (
              <p className="success">Подтверждён</p>
            )}
            {grade.grade === profile.declared_grade && (
              <p className="hint">Ваш заявленный уровень</p>
            )}
            <p>{availabilityLabel(grade)}</p>
            <button
              className={selected === grade.grade ? "" : "secondary"}
              aria-pressed={selected === grade.grade}
              disabled={!grade.available || busy}
              onClick={() => onSelect(grade.grade)}
            >
              Выбрать {gradeLabels[grade.grade]}
            </button>
          </article>
        ))}
      </div>
      {selected && (
        <section className="assessment-rules" aria-labelledby="assessment-rules-heading">
          <h2 id="assessment-rules-heading">
            Перед началом: {specializationLabels[data.specialization]} /{" "}
            {gradeLabels[selected]}
          </h2>
          <ul>
            <li>20 вопросов, один ответ из четырёх.</li>
            <li>30 минут. Таймер не останавливается при закрытии страницы.</li>
            <li>
              Ответ сохраняется сразу после выбора. Следите за статусом
              сохранения.
            </li>
            <li>
              Для подтверждения: минимум 70/100 в целом и 50% в каждой из пяти
              компетенций.
            </li>
            <li>Вопрос без ответа даёт 0 баллов.</li>
            <li>
              Повтор после неуспеха — через 7 дней, после успеха — через 90 дней
              на том же уровне.
            </li>
          </ul>
          <div className="actions">
            <button disabled={busy || !choice?.available} onClick={onStart}>
              {busy ? "Начинаем…" : "Начать тест"}
            </button>
          </div>
        </section>
      )}
      <Feedback error={error} />
      {Boolean(error) && (
        <button
          className="secondary"
          disabled={busy}
          onClick={onRefresh}
        >
          Обновить доступность
        </button>
      )}
    </section>
  );
}
