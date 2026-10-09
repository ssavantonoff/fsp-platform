"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/api";
import type { AttemptSummary } from "@/assessment";
import { competencyLabels, dateLabel } from "@/assessment";
import { gradeLabels, specializationLabels } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";
import { assessmentOutcomeLabels } from "./assessment-result";

export function AssessmentHistory() {
  return (
    <RoleGate role="CANDIDATE">
      <History />
    </RoleGate>
  );
}

export function AssessmentHistoryList({
  attempts,
}: {
  attempts: AttemptSummary[];
}) {
  return (
    <>
      <p className="notice">
        История попыток не заменяет текущую подтверждённую квалификацию.
      </p>
      {attempts.length === 0 ? (
        <div className="empty-state"><h2>У вас пока нет попыток.</h2><p>Начать тестирование можно на странице выбора уровня.</p></div>
      ) : (
        <ul className="attempt-history">
          {attempts.map((attempt) => (
            <li className="assessment-history-card" key={attempt.id}>
              <h2>
                Попытка: {specializationLabels[attempt.specialization]} /{" "}
                {gradeLabels[attempt.target_grade]}
              </h2>
              <p className={`assessment-outcome ${attempt.status === "PASSED" ? "success" : "notice"}`}>
                {assessmentOutcomeLabels[attempt.status]}
              </p>
              <p className="hint">
                Начало: {dateLabel(attempt.started_at)}. Завершение:{" "}
                {dateLabel(attempt.finished_at)}.
              </p>
              <p>
                {attempt.status === "IN_PROGRESS"
                  ? "В процессе · Оценка: —"
                  : `Оценка: ${attempt.normalized_assessment_score === null ? "—" : `${attempt.normalized_assessment_score} / 100`} · ${attempt.completion_reason === "TIMEOUT" ? "Время вышло" : "Завершено кандидатом"}`}
              </p>
              {attempt.competency_scores && (
                <details className="workflow-details">
                  <summary>Результаты по компетенциям</summary>
                  <dl className="assessment-score-grid">
                    {Object.entries(attempt.competency_scores).map(([key, score]) => <div className="score-row" key={key}>
                      <dt>{competencyLabels[key] ?? key}</dt><dd>{score}%</dd>
                    </div>)}
                  </dl>
                </details>
              )}
              <Link className="button secondary" href={`/candidate/assessment/${attempt.id}`}>
                {attempt.status === "IN_PROGRESS" ? "Продолжить" : "Результат"}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export function AssessmentHistoryView({ attempts, loading, error, onRetry }: {
  attempts: AttemptSummary[]; loading: boolean; error: unknown; onRetry: () => void;
}) {
  return <section className="card assessment-screen assessment-history-screen">
    <div className="assessment-result-heading"><h1>История попыток</h1><p className="hint">Assessment · результаты тестирования</p></div>
    <div className="actions"><Link className="button secondary" href="/candidate/assessment">Выбор уровня</Link></div>
    {loading ? <p role="status">Загрузка истории…</p> : error ? <>
      <Feedback error={error} />
      <button onClick={onRetry}>Повторить</button>
    </> : <AssessmentHistoryList attempts={attempts} />}
  </section>;
}

function History() {
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(
    () =>
      api<AttemptSummary[]>("/candidate/assessments/history")
        .then((value) => {
          setAttempts(value);
          setError(null);
        })
        .catch(setError)
        .finally(() => setLoading(false)),
    [],
  );
  useEffect(() => {
    void load();
  }, [load]);
  return <AssessmentHistoryView attempts={attempts} loading={loading} error={error} onRetry={() => {
    setLoading(true);
    void load();
  }} />;
}
