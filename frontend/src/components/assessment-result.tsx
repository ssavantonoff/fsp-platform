import Link from "next/link";
import { competencyLabels, dateLabel } from "@/assessment";
import type { AttemptSummary } from "@/assessment";
import { gradeLabels, specializationLabels } from "@/types";
import type { CandidateProfile } from "@/types";

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
  return (
    <section className="card assessment-result">
      <h1>
        {specializationLabels[attempt.specialization]} /{" "}
        {gradeLabels[attempt.target_grade]}
      </h1>
      <p className={attempt.status === "PASSED" ? "success" : "notice"}>
        {attempt.status === "PASSED"
          ? "Уровень подтверждён — PASSED"
          : "Уровень не подтверждён — FAILED"}
      </p>
      <h2>{attempt.normalized_assessment_score} / 100</h2>
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
      {verification && (
        <p>
          Текущий подтверждённый уровень:{" "}
          {verification.verified_grade
            ? gradeLabels[verification.verified_grade]
            : "не подтверждён"}
          .
        </p>
      )}
      <p>
        Следующая попытка на этом уровне: {dateLabel(attempt.available_at)}.
      </p>
      <div className="actions">
        <Link href="/candidate/assessment">Выбрать уровень</Link>
        <Link href="/candidate/assessment/history">История</Link>
        <Link href="/candidate">Профиль</Link>
      </div>
    </section>
  );
}
