import Link from "next/link";
import { competencyLabels, dateLabel } from "@/assessment";
import type { AttemptSummary } from "@/assessment";
import { gradeLabels, specializationLabels } from "@/types";
import type { CandidateProfile } from "@/types";

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
    <section aria-label="Текущая подтверждённая квалификация">
      <h2>Текущая подтверждённая квалификация</h2>
      {!verification ? (
        <p>Данные текущей подтверждённой квалификации недоступны.</p>
      ) : (
        <>
          {unverified && <p>Подтверждённой квалификации пока нет.</p>}
          <dl>
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
    <section className="card assessment-result">
      <section aria-label="Результат попытки">
        <h1>Результат попытки</h1>
        <h2>
          {specializationLabels[attempt.specialization]} /{" "}
          {gradeLabels[attempt.target_grade]}
        </h2>
        <p className={attempt.status === "PASSED" ? "success" : "notice"}>
          {attempt.status === "PASSED"
            ? "Попытка успешно пройдена"
            : "Попытка не пройдена"}{" "}
          — {attempt.status}
        </p>
        <dl>
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
          <p>Время вышло. Результат рассчитан по сохранённым ответам.</p>
        )}
        <dl>
          {Object.entries(attempt.competency_scores ?? {}).map(([key, value]) => (
            <div className="score-row" key={key}>
              <dt>{competencyLabels[key] ?? key}</dt>
              <dd>{value}%</dd>
            </div>
          ))}
        </dl>
        <dl aria-label="Условия подтверждения">
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
      <p>
        Следующая попытка на этом уровне — не ранее{" "}
        {dateLabel(attempt.available_at)}.
      </p>
      <div className="actions">
        <Link href="/candidate/assessment">Выбрать уровень</Link>
        <Link href="/candidate/assessment/history">История</Link>
        <Link href="/candidate">Профиль</Link>
      </div>
    </section>
  );
}
