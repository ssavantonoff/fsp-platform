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
    <>
      <section aria-label="Заявленный уровень">
        <h2>Заявленный уровень</h2>
        <p>{gradeLabels[profile.declared_grade]}</p>
      </section>
      <CurrentQualification verification={profile} />
    </>
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
  if (loading) return <p role="status">Загрузка доступных тестов…</p>;
  if (error instanceof ApiError && error.code === "profile_not_found")
    return (
      <section className="card">
        <h1>Подтверждение уровня</h1>
        <p>Сначала заполните профиль кандидата.</p>
        <Link href="/candidate/edit">Создать профиль</Link>
      </section>
    );
  if (!data)
    return (
      <section className="card">
        <Feedback error={error} />
        <button
          onClick={() => {
            setLoading(true);
            void load();
          }}
        >
          Повторить
        </button>
      </section>
    );
  const profile = data.verification;
  const choice = data.grades.find((g) => g.grade === selected);
  return (
    <section className="card">
      <h1>Подтверждение уровня</h1>
      <AssessmentDashboardSummary profile={profile} />
      <div className="actions">
        <Link href="/candidate">Профиль</Link>
        <Link href="/candidate/assessment/history">История попыток</Link>
      </div>
      {data.active_attempt_id && (
        <p className="notice">
          У вас есть активный тест.{" "}
          <Link href={`/candidate/assessment/${data.active_attempt_id}`}>
            Продолжить тест
          </Link>
        </p>
      )}
      <div className="grade-cards">
        {data.grades.map((grade) => (
          <article className="grade-card" key={grade.grade}>
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
              disabled={!grade.available || busy}
              onClick={() => {
                setSelected(grade.grade);
                setError(null);
              }}
            >
              Выбрать {gradeLabels[grade.grade]}
            </button>
          </article>
        ))}
      </div>
      {selected && (
        <div className="assessment-rules">
          <h2>
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
          <button
            disabled={busy || !choice?.available}
            onClick={() => void start()}
          >
            {busy ? "Начинаем…" : "Начать тест"}
          </button>
        </div>
      )}
      <Feedback error={error} />
      {Boolean(error) && (
        <button
          className="secondary"
          disabled={busy}
          onClick={() => void load()}
        >
          Обновить доступность
        </button>
      )}
    </section>
  );
}
