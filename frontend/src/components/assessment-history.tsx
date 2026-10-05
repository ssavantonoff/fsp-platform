"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/api";
import type { AttemptSummary } from "@/assessment";
import { competencyLabels, dateLabel } from "@/assessment";
import { gradeLabels, specializationLabels } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";

export function AssessmentHistory() {
  return (
    <RoleGate role="CANDIDATE">
      <History />
    </RoleGate>
  );
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
  return (
    <section className="card">
      <h1>История попыток</h1>
      <Link href="/candidate/assessment">Выбор уровня</Link>
      {loading ? (
        <p role="status">Загрузка истории…</p>
      ) : error ? (
        <>
          <Feedback error={error} />
          <button
            onClick={() => {
              setLoading(true);
              void load();
            }}
          >
            Повторить
          </button>
        </>
      ) : attempts.length === 0 ? (
        <p>У вас пока нет попыток.</p>
      ) : (
        <ul className="attempt-history">
          {attempts.map((attempt) => (
            <li key={attempt.id}>
              <h2>
                {specializationLabels[attempt.specialization]} /{" "}
                {gradeLabels[attempt.target_grade]}
              </h2>
              <p>
                Начало: {dateLabel(attempt.started_at)}. Завершение:{" "}
                {dateLabel(attempt.finished_at)}.
              </p>
              <p>
                {attempt.status === "IN_PROGRESS"
                  ? "В процессе"
                  : `${attempt.status} · ${attempt.normalized_assessment_score} / 100 · ${attempt.completion_reason === "TIMEOUT" ? "Время вышло" : "Завершено кандидатом"}`}
              </p>
              {attempt.competency_scores && (
                <p>
                  {Object.entries(attempt.competency_scores)
                    .map(
                      ([key, score]) =>
                        `${competencyLabels[key] ?? key}: ${score}%`,
                    )
                    .join(" · ")}
                </p>
              )}
              <Link href={`/candidate/assessment/${attempt.id}`}>
                {attempt.status === "IN_PROGRESS" ? "Продолжить" : "Результат"}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
