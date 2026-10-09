import Link from "next/link";
import { competencyLabels, dateLabel } from "@/assessment";
import type { AttemptSummary } from "@/assessment";
import { gradeLabels, specializationLabels } from "@/types";
import type { CandidateProfile } from "@/types";

export const assessmentOutcomeLabels: Record<AttemptSummary["status"], string> = {
  IN_PROGRESS: "Тестирование не завершено",
  PASSED: "Попытка успешно пройдена",
  FAILED: "Попытка не пройдена",
};

export function CurrentQualification({
  verification,
}: {
  verification?: CandidateProfile;
}) {
  const unverified =
    verification &&
    verification.verified_grade === null &&
    verification.normalized_assessment_score === null &&
    verification.assessment_verified_at === null;
  return (
    <section aria-label="Текущая подтверждённая квалификация" className="assessment-current">
      <h2>Текущая подтверждённая квалификация</h2>
      {!verification ? (
        <p>Данные текущей подтверждённой квалификации недоступны.</p>
      ) : (
        <>
          {unverified && <p className="notice">Подтверждённой квалификации пока нет.</p>}
          <dl className="workflow-facts">
            <dt>Специализация</dt>
            <dd>{specializationLabels[verification.specialization]}</dd>
            <dt>Подтверждённый уровень</dt>
            <dd>
              {verification.verified_grade
                ? gradeLabels[verification.verified_grade]
                : "—"}
            </dd>
            <dt>Оценка подтверждения</dt>
            <dd>
              {verification.normalized_assessment_score === null
                ? "—"
                : `${verification.normalized_assessment_score} / 100`}
            </dd>
            <dt>Дата подтверждения</dt>
            <dd>{dateLabel(verification.assessment_verified_at)}</dd>
          </dl>
        </>
      )}
    </section>
  );
}

export function AssessmentResult({
  attempt,
  verification,
}: {
  attempt: AttemptSummary;
  verification?: CandidateProfile;
}) {
  const failed = Object.entries(attempt.competency_scores ?? {}).filter(
    ([, value]) => value < 50,
  );
  const expectedCompetencies =
    attempt.specialization === "BACKEND"
      ? [
          "PROGRAMMING",
          "HTTP_API",
          "DATABASES",
          "ARCHITECTURE",
          "TESTING_SECURITY_DEBUGGING",
        ]
      : Object.keys(attempt.competency_scores ?? {});
  const overallMet =
    attempt.normalized_assessment_score !== null &&
    attempt.normalized_assessment_score >= 70;
  const competenciesMet =
    expectedCompetencies.length === 5 &&
    expectedCompetencies.every((key) => {
      const score = attempt.competency_scores?.[key];
      return typeof score === "number" && score >= 50;
    });
  return (
    <section className="card assessment-screen assessment-result">
      <section aria-label="Результат попытки" className="assessment-summary">
        <div className="assessment-result-heading">
          <h1>Результат попытки</h1>
          <p className="hint">Assessment · тестирование квалификации</p>
        </div>
        <h2>
          {specializationLabels[attempt.specialization]} /{" "}
          {gradeLabels[attempt.target_grade]}
        </h2>
        <p className={`assessment-outcome ${attempt.status === "PASSED" ? "success" : "notice"}`}>
          {assessmentOutcomeLabels[attempt.status]}
        </p>
        <dl className="workflow-facts">
          <dt>Оценка попытки</dt>
          <dd>
            {attempt.normalized_assessment_score === null
              ? "—"
              : `${attempt.normalized_assessment_score} / 100`}
          </dd>
          <dt>Дата завершения попытки</dt>
          <dd>{dateLabel(attempt.finished_at)}</dd>
        </dl>
        {attempt.completion_reason === "TIMEOUT" && (
          <p className="notice">Время вышло. Результат рассчитан по сохранённым ответам.</p>
        )}
        <h3>Результаты по компетенциям</h3>
        <dl className="assessment-score-grid">
          {Object.entries(attempt.competency_scores ?? {}).map(([key, value]) => (
            <div className="score-row" key={key}>
              <dt>{competencyLabels[key] ?? key}</dt>
              <dd>{value}%</dd>
            </div>
          ))}
        </dl>
        <dl className="workflow-facts assessment-thresholds" aria-label="Условия подтверждения">
          <dt>Общий балл &gt;=70</dt>
          <dd>{overallMet ? "Выполнено" : "Не выполнено"}</dd>
          <dt>Каждая компетенция &gt;=50</dt>
          <dd>{competenciesMet ? "Выполнено" : "Не выполнено"}</dd>
        </dl>
        {attempt.status === "FAILED" && (
          <>
            <p>
              Для подтверждения {gradeLabels[attempt.target_grade]} необходимо
              минимум 70/100 в целом и минимум 50% в каждом блоке.
            </p>
            {failed.length > 0 && (
              <p>
                Блоки ниже порога:{" "}
                {failed.map(([key]) => competencyLabels[key] ?? key).join(", ")}.
              </p>
            )}
          </>
        )}
      </section>
      <CurrentQualification verification={verification} />
      {verification && <section aria-label="Заявленный уровень" className="assessment-declared">
        <h2>Заявленный уровень</h2>
        <p>{gradeLabels[verification.declared_grade]}</p>
        <p className="hint">Указан вами в профиле. Для подтверждения квалификации нужно тестирование.</p>
      </section>}
      {attempt.available_at ? <p className="hint">
          Следующая попытка на этом уровне — не ранее{" "}
          {dateLabel(attempt.available_at)}.
        </p> : <p className="hint">Доступность следующей попытки указана на странице выбора уровня.</p>}
      <div className="actions">
        <Link className="button" href="/candidate/assessment">Выбрать уровень</Link>
        <Link className="button secondary" href="/candidate/assessment/history">История</Link>
        <Link className="button secondary" href="/candidate">Профиль</Link>
      </div>
    </section>
  );
}
