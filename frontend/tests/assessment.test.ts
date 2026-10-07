import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ApiError } from "../src/api";
import {
  applySavedAttempt,
  availabilityLabel,
  dateLabel,
  loadAttempt,
  saveAssessmentAnswer,
  secondsRemaining,
  serverClock,
  submitAssessment,
  timerLabel,
} from "../src/assessment";
import type { AssessmentQuestion, Attempt, AttemptSummary } from "../src/assessment";
import { AssessmentQuestion as QuestionView } from "../src/components/assessment-question";
import { AssessmentResult, CurrentQualification } from "../src/components/assessment-result";
import { AssessmentDashboardSummary } from "../src/components/assessment-dashboard";
import { AssessmentHistoryList } from "../src/components/assessment-history";
import type { CandidateProfile } from "../src/types";

const question: AssessmentQuestion = {
  attempt_question_id: "q1",
  question_id: "bank1",
  position: 1,
  competency: "PROGRAMMING",
  difficulty: "BASIC",
  prompt: "Вопрос",
  options: [
    { id: "o1", text: "Первый вариант" },
    { id: "o2", text: "Второй вариант" },
    { id: "o3", text: "Третий вариант" },
    { id: "o4", text: "Четвёртый вариант" },
  ],
  selected_option_id: null,
};
const result: AttemptSummary = {
  id: "attempt",
  specialization: "BACKEND",
  target_grade: "MIDDLE",
  status: "FAILED",
  completion_reason: "TIMEOUT",
  started_at: "2026-01-01T00:00:00Z",
  expires_at: "2026-01-01T00:30:00Z",
  finished_at: "2026-01-01T00:30:00Z",
  normalized_assessment_score: 80,
  competency_scores: {
    PROGRAMMING: 100,
    HTTP_API: 100,
    DATABASES: 25,
    ARCHITECTURE: 100,
    TESTING_SECURITY_DEBUGGING: 75,
  },
  available_at: "2026-01-08T00:30:00Z",
};
const verification: CandidateProfile = {
  id: "candidate", user_id: "user", first_name: "Имя", last_name: "Фамилия",
  city: null, about: null, specialization: "BACKEND", declared_grade: "SENIOR",
  verified_grade: "MIDDLE", normalized_assessment_score: 80,
  assessment_verified_at: "2026-10-07T09:10:00Z", years_of_experience: null,
  fsp_id: null, personal_data_consent: true,
  personal_data_consent_at: "2026-10-07T09:00:00Z", skills: [],
};
const g3Scores = {
  PROGRAMMING: 75, HTTP_API: 75, DATABASES: 75, ARCHITECTURE: 50,
  TESTING_SECURITY_DEBUGGING: 50,
};
const fullScores = {
  PROGRAMMING: 100, HTTP_API: 100, DATABASES: 100, ARCHITECTURE: 100,
  TESTING_SECURITY_DEBUGGING: 100,
};
function semanticSection(html: string, label: string) {
  const match = html.match(new RegExp(`<section aria-label="${label}">([\\s\\S]*?)</section>`));
  assert.ok(match, `Missing section: ${label}`);
  return match[1];
}
function assertConditions(html: string, overall: string, competencies: string) {
  assert.ok(html.includes(`<dt>Общий балл &gt;=70</dt><dd>${overall}</dd>`));
  assert.ok(html.includes(`<dt>Каждая компетенция &gt;=50</dt><dd>${competencies}</dd>`));
}

test("assessment dates show explicit UTC with seconds and 24-hour time", () => {
  assert.equal(dateLabel("2026-10-07T09:10:05Z"), "07.10.2026, 09:10:05 UTC");
});
test("equivalent timestamp offsets show the same UTC instant", () => {
  assert.equal(dateLabel("2026-10-07T12:10:05+03:00"), "07.10.2026, 09:10:05 UTC");
});
test("assessment dates cross calendar boundaries in UTC", () => {
  assert.equal(dateLabel("2026-10-08T01:05:06+03:00"), "07.10.2026, 22:05:06 UTC");
  assert.equal(dateLabel("2026-10-08T00:00:00Z"), "08.10.2026, 00:00:00 UTC");
});
test("null assessment date keeps the empty label", () => {
  assert.equal(dateLabel(null), "—");
});

test("timer uses server deadline and monotonic elapsed time, including request latency", () => {
  const clock = serverClock(
    { server_now: "2026-01-01T00:00:00Z", expires_at: "2026-01-01T00:30:00Z" },
    100,
  );
  assert.equal(secondsRemaining(clock, 100), 1800);
  assert.equal(secondsRemaining(clock, 1100), 1799);
  assert.equal(secondsRemaining(clock, 1800100), 0);
  assert.equal(secondsRemaining(clock, 1900100), 0);
  assert.equal(timerLabel(1800), "30:00");
  assert.equal(timerLabel(7), "00:07");
});
test("expired server deadline starts at zero", () => {
  assert.equal(
    secondsRemaining(
      serverClock(
        {
          server_now: "2026-01-01T01:00:00Z",
          expires_at: "2026-01-01T00:30:00Z",
        },
        5,
      ),
      5,
    ),
    0,
  );
});
test("availability explains cooldown, lower grades, missing bank and prerequisites", () => {
  assert.match(
    availabilityLabel({
      grade: "MIDDLE",
      available: true,
      reason: null,
      available_at: null,
    }),
    /Можно начать/,
  );
  for (const [reason, phrase] of [
    ["COOLDOWN", "Повторная"],
    ["LOWER_THAN_VERIFIED", "ниже"],
    ["UNAVAILABLE", "Банк"],
    ["EMAIL_NOT_VERIFIED", "email"],
    ["CONSENT_REQUIRED", "согласие"],
    ["IN_PROGRESS", "активную"],
  ]) {
    assert.ok(
      availabilityLabel({
        grade: "JUNIOR",
        available: false,
        reason,
        available_at: null,
      }).includes(phrase),
    );
  }
  assert.match(
    availabilityLabel({
      grade: "MIDDLE",
      available: false,
      reason: "COOLDOWN",
      available_at: result.available_at,
    }),
    /Доступно с/,
  );
});
test("question renders exactly four radios with saved answer and disabled state", () => {
  const html = renderToStaticMarkup(
    createElement(QuestionView, {
      question,
      selected: "o2",
      disabled: true,
      onSelect: () => {},
    }),
  );
  assert.equal((html.match(/type="radio"/g) ?? []).length, 4);
  assert.match(html, /Программирование/);
  assert.match(html, /disabled/);
  assert.equal((html.match(/checked=""/g) ?? []).length, 1);
});
test("failed result shows threshold and weak competency without correct answers", () => {
  const html = renderToStaticMarkup(
    createElement(AssessmentResult, { attempt: result }),
  );
  assert.match(html, /80 \/ 100/);
  assert.match(html, /FAILED/);
  assert.match(html, /70\/100/);
  assert.match(html, /50%/);
  assert.match(html, /Базы данных/);
  assert.match(html, /Время вышло/);
  assertConditions(semanticSection(html, "Результат попытки"), "Выполнено", "Не выполнено");
  assert.match(html, /Дата завершения попытки/);
  assert.match(html, /01\.01\.2026, 00:30:00 UTC/);
  assert.ok(!html.includes("Первый вариант"));
});
test("passed result shows aggregate score and next attempt date", () => {
  const html = renderToStaticMarkup(
    createElement(AssessmentResult, {
      attempt: {
        ...result,
        status: "PASSED",
        normalized_assessment_score: 100,
        competency_scores: fullScores,
        completion_reason: "SUBMITTED",
        available_at: "2026-04-01T00:30:00Z",
      },
    }),
  );
  assert.match(html, /Попытка успешно пройдена/);
  assert.match(html, /PASSED/);
  assert.match(html, /Следующая попытка/);
  assert.ok(!html.includes("Блоки ниже порога"));
  assertConditions(semanticSection(html, "Результат попытки"), "Выполнено", "Выполнено");
  assert.equal((semanticSection(html, "Результат попытки").match(/class="score-row"/g) ?? []).length, 5);
  assert.equal((semanticSection(html, "Результат попытки").match(/100%/g) ?? []).length, 5);
  assert.match(html, /Дата завершения попытки/);
  assert.match(html, /01\.01\.2026, 00:30:00 UTC/);
  assert.match(html, /Следующая попытка на этом уровне — не ранее 01\.04\.2026, 00:30:00 UTC/);
});
test("G3 result explains failed overall and fulfilled competency condition", () => {
  const html = renderToStaticMarkup(createElement(AssessmentResult, {
    attempt: { ...result, normalized_assessment_score: 65, competency_scores: g3Scores },
  }));
  const attempt = semanticSection(html, "Результат попытки");
  assert.match(attempt, /FAILED/);
  assert.match(attempt, /65 \/ 100/);
  assertConditions(attempt, "Не выполнено", "Выполнено");
});
test("failed Senior attempt and current Middle qualification have separate scores and dates", () => {
  const html = renderToStaticMarkup(createElement(AssessmentResult, {
    attempt: { ...result, target_grade: "SENIOR", normalized_assessment_score: 65,
      competency_scores: g3Scores, completion_reason: "SUBMITTED",
      started_at: "2026-10-07T09:20:00Z", expires_at: "2026-10-07T09:50:00Z",
      finished_at: "2026-10-07T09:25:00Z", available_at: "2026-10-14T09:25:00Z" },
    verification,
  }));
  const attempt = semanticSection(html, "Результат попытки");
  const current = semanticSection(html, "Текущая подтверждённая квалификация");
  assert.match(attempt, /Backend \/ Senior/);
  assert.match(attempt, /FAILED/);
  assert.match(attempt, /65 \/ 100/);
  assert.match(attempt, /07\.10\.2026, 09:25:00 UTC/);
  assert.doesNotMatch(attempt, /Middle|80 \/ 100|09:10:00/);
  assert.match(current, /Специализация<\/dt><dd>Backend/);
  assert.match(current, /Подтверждённый уровень<\/dt><dd>Middle/);
  assert.match(current, /Оценка подтверждения<\/dt><dd>80 \/ 100/);
  assert.match(current, /Дата подтверждения<\/dt><dd>07\.10\.2026, 09:10:00 UTC/);
  assert.doesNotMatch(current, /Senior|65 \/ 100|09:25:00/);
});
test("dashboard keeps declared Senior separate from current Middle qualification", () => {
  const html = renderToStaticMarkup(createElement(AssessmentDashboardSummary, { profile: verification }));
  assert.match(semanticSection(html, "Заявленный уровень"), /Senior/);
  const current = semanticSection(html, "Текущая подтверждённая квалификация");
  assert.match(current, /Middle/);
  assert.match(current, /80 \/ 100/);
  assert.doesNotMatch(current, /Senior/);
});
test("canonical null triple explicitly has no qualification and never uses declared grade", () => {
  const profile = { ...verification, verified_grade: null, normalized_assessment_score: null, assessment_verified_at: null };
  for (const view of [
    createElement(CurrentQualification, { verification: profile }),
    createElement(AssessmentDashboardSummary, { profile }),
    createElement(AssessmentResult, { attempt: result, verification: profile }),
  ]) {
    const current = semanticSection(renderToStaticMarkup(view), "Текущая подтверждённая квалификация");
    assert.match(current, /Подтверждённой квалификации пока нет\./);
    assert.doesNotMatch(current, /Senior|Middle|80 \/ 100/);
  }
});
test("omitted verification means unavailable data rather than an unverified candidate", () => {
  const html = renderToStaticMarkup(createElement(AssessmentResult, { attempt: result }));
  const current = semanticSection(html, "Текущая подтверждённая квалификация");
  assert.match(current, /Данные текущей подтверждённой квалификации недоступны/);
  assert.doesNotMatch(current, /Подтверждённой квалификации пока нет|Middle|80 \/ 100/);
});
test("finished result never renders attached questions, options, solutions or answer keys", () => {
  const sentinel = "PRIVATE_ANSWER_SENTINEL";
  const attempt = { ...result, questions: [{ ...question, prompt: sentinel,
    options: [{ id: "correct", text: sentinel }] }], answer_key: sentinel, solution: sentinel,
    correct_option_index: 0, explanation: sentinel };
  const html = renderToStaticMarkup(createElement(AssessmentResult, { attempt, verification }));
  assert.doesNotMatch(html, /PRIVATE_ANSWER_SENTINEL|answer_key|correct_option_index|solution|type="radio"/);
});
test("server FAILED remains authoritative even when both aggregate conditions are fulfilled", () => {
  const html = renderToStaticMarkup(createElement(AssessmentResult, {
    attempt: { ...result, normalized_assessment_score: 100, competency_scores: fullScores },
  }));
  const attempt = semanticSection(html, "Результат попытки");
  assert.match(attempt, /FAILED/);
  assert.doesNotMatch(attempt, /PASSED/);
  assertConditions(attempt, "Выполнено", "Выполнено");
});
test("server PASSED remains authoritative even when aggregate conditions are not fulfilled", () => {
  const html = renderToStaticMarkup(createElement(AssessmentResult, {
    attempt: { ...result, status: "PASSED", normalized_assessment_score: 0, competency_scores: null },
  }));
  const attempt = semanticSection(html, "Результат попытки");
  assert.match(attempt, /PASSED/);
  assert.doesNotMatch(attempt, /FAILED/);
  assertConditions(attempt, "Не выполнено", "Не выполнено");
});
for (const [label, scores] of [
  ["null", null], ["empty", {}],
  ["missing block", { PROGRAMMING: 100, HTTP_API: 100, ARCHITECTURE: 100, TESTING_SECURITY_DEBUGGING: 100 }],
  ["unknown key replacing a missing block", { PROGRAMMING: 100, HTTP_API: 100, ARCHITECTURE: 100, TESTING_SECURITY_DEBUGGING: 100, UNKNOWN: 100 }],
] as const) {
  test(`${label} competency data cannot fulfill the block condition`, () => {
    const html = renderToStaticMarkup(createElement(AssessmentResult, {
      attempt: { ...result, competency_scores: scores },
    }));
    assertConditions(semanticSection(html, "Результат попытки"), "Выполнено", "Не выполнено");
  });
}
test("historical Backend Middle PASS does not substitute for current Frontend Senior qualification", () => {
  const html = renderToStaticMarkup(createElement(AssessmentResult, {
    attempt: { ...result, status: "PASSED", normalized_assessment_score: 100, competency_scores: fullScores },
    verification: { ...verification, specialization: "FRONTEND", verified_grade: "SENIOR",
      normalized_assessment_score: 70, assessment_verified_at: "2026-10-08T12:00:00Z" },
  }));
  const attempt = semanticSection(html, "Результат попытки");
  assert.match(attempt, /Backend \/ Middle/);
  assert.match(attempt, /PASSED/);
  assert.match(attempt, /100 \/ 100/);
  const current = semanticSection(html, "Текущая подтверждённая квалификация");
  assert.match(current, /Frontend/);
  assert.match(current, /Senior/);
  assert.match(current, /70 \/ 100/);
  assert.match(current, /08\.10\.2026, 12:00:00 UTC/);
  assert.doesNotMatch(current, /Backend|Middle|100 \/ 100/);
});

const historyCopy = "История попыток не заменяет текущую подтверждённую квалификацию.";
test("empty history explains its meaning and contains no fabricated qualification", () => {
  const html = renderToStaticMarkup(createElement(AssessmentHistoryList, { attempts: [] }));
  assert.ok(html.includes(historyCopy));
  assert.match(html, /У вас пока нет попыток/);
  assert.doesNotMatch(html, /<li|Оценка подтверждения|Дата подтверждения|verified_grade/);
});
test("historical PASS describes an attempt with all aggregate scores and UTC dates", () => {
  const html = renderToStaticMarkup(createElement(AssessmentHistoryList, {
    attempts: [{ ...result, status: "PASSED", normalized_assessment_score: 100,
      competency_scores: fullScores, completion_reason: "SUBMITTED", available_at: "2026-04-01T00:30:00Z" }],
  }));
  assert.ok(html.includes(historyCopy));
  assert.match(html, /Попытка: Backend \/ Middle/);
  assert.match(html, /PASSED · 100 \/ 100 · Завершено кандидатом/);
  for (const label of ["Программирование", "HTTP и API", "Базы данных", "Архитектура", "Тестирование, безопасность и отладка"]) {
    assert.ok(html.includes(`${label}: 100%`));
  }
  assert.match(html, /Начало: 01\.01\.2026, 00:00:00 UTC/);
  assert.match(html, /Завершение: 01\.01\.2026, 00:30:00 UTC/);
  assert.match(html, /href="\/candidate\/assessment\/attempt"[^>]*>Результат/);
  assert.doesNotMatch(html, /Текущая подтверждённая квалификация|Оценка подтверждения|Дата подтверждения|Уровень подтверждён/);
});
test("historical FAILED retains its own score, timeout reason and weak competency", () => {
  const html = renderToStaticMarkup(createElement(AssessmentHistoryList, { attempts: [result] }));
  assert.ok(html.includes(historyCopy));
  assert.match(html, /Попытка: Backend \/ Middle/);
  assert.match(html, /FAILED · 80 \/ 100 · Время вышло/);
  assert.match(html, /Базы данных: 25%/);
  assert.doesNotMatch(html, /PASSED|Оценка подтверждения/);
});
test("IN_PROGRESS history remains in progress with continue navigation and absent result", () => {
  const html = renderToStaticMarkup(createElement(AssessmentHistoryList, {
    attempts: [{ ...result, status: "IN_PROGRESS", normalized_assessment_score: null,
      competency_scores: null, completion_reason: null, finished_at: null, available_at: null }],
  }));
  assert.ok(html.includes(historyCopy));
  assert.match(html, /IN_PROGRESS · В процессе · Оценка: —/);
  assert.match(html, /Завершение: —/);
  assert.match(html, /href="\/candidate\/assessment\/attempt"[^>]*>Продолжить/);
  assert.doesNotMatch(html, /PASSED|FAILED|80 \/ 100|Время вышло|Завершено кандидатом/);
});
test("history dates normalize offset timestamps across UTC calendar days", () => {
  const html = renderToStaticMarkup(createElement(AssessmentHistoryList, {
    attempts: [{ ...result, started_at: "2026-10-08T02:50:00+03:00",
      finished_at: "2026-10-08T03:10:00+03:00", expires_at: "2026-10-08T03:20:00+03:00",
      completion_reason: "SUBMITTED", available_at: "2026-10-15T00:10:00Z" }],
  }));
  assert.match(html, /Начало: 07\.10\.2026, 23:50:00 UTC/);
  assert.match(html, /Завершение: 08\.10\.2026, 00:10:00 UTC/);
});
test("history ignores injected profile and answer fields instead of fabricating current qualification", () => {
  const attempt = { ...result, verification, questions: [question], answer_key: "PRIVATE_HISTORY_KEY" };
  const html = renderToStaticMarkup(createElement(AssessmentHistoryList, { attempts: [attempt] }));
  assert.ok(html.includes(historyCopy));
  assert.doesNotMatch(html, /Текущая подтверждённая квалификация|Оценка подтверждения|Дата подтверждения|09:10:00|Senior|PRIVATE_HISTORY_KEY|Первый вариант|verified_grade/);
});
test("answer save sends only selected option and returns canonical response", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    assert.equal(url, "/api/candidate/assessments/a/answers/q");
    assert.equal(init?.method, "PUT");
    assert.equal(init?.body, JSON.stringify({ selected_option_id: "o" }));
    return Response.json({
      questions: [{ ...question, selected_option_id: "o" }],
    });
  };
  try {
    assert.equal(
      (await saveAssessmentAnswer("a", "q", "o")).questions[0]
        .selected_option_id,
      "o",
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("failed save stays failed and can be retried explicitly", async () => {
  const original = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = async () => {
    requests++;
    return requests === 1
      ? Response.json(
          {
            error: {
              code: "backend_unavailable",
              message: "Недоступен",
              fields: [],
            },
          },
          { status: 502 },
        )
      : Response.json({ questions: [question] });
  };
  try {
    await assert.rejects(
      saveAssessmentAnswer("a", "q", "o"),
      (error: unknown) =>
        error instanceof ApiError && error.code === "backend_unavailable",
    );
    assert.equal(requests, 1);
    assert.equal(
      (await saveAssessmentAnswer("a", "q", "o")).questions.length,
      1,
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("finished answer error is identifiable so UI can load finalized result", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () =>
    Response.json(
      {
        error: { code: "assessment_finished", message: "Завершён", fields: [] },
      },
      { status: 409 },
    );
  try {
    await assert.rejects(
      saveAssessmentAnswer("a", "q", "o"),
      (error: unknown) =>
        error instanceof ApiError && error.code === "assessment_finished",
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("load is read-only and submit requires explicit POST", async () => {
  const original = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = async (url, init) => {
    calls.push(`${init?.method ?? "GET"} ${url}`);
    return Response.json({
      ...result,
      server_now: result.started_at,
      questions: [],
    });
  };
  try {
    const loaded = await loadAttempt("a");
    assert.equal(loaded.attempt.status, "FAILED");
    assert.ok(loaded.clock.remainingMs > 0);
    await submitAssessment("a");
    assert.deepEqual(calls, [
      "GET /api/candidate/assessments/a",
      "POST /api/candidate/assessments/a/submit",
    ]);
  } finally {
    globalThis.fetch = original;
  }
});

test("late autosave response cannot replace a finalized result", () => {
  const finalized = {
    ...result,
    server_now: result.finished_at!,
    verification: {
      id: "candidate", user_id: "user", first_name: "Имя", last_name: "Фамилия",
      city: null, about: null, specialization: "BACKEND", declared_grade: "MIDDLE",
      verified_grade: null, normalized_assessment_score: null, assessment_verified_at: null,
      years_of_experience: null, fsp_id: null, personal_data_consent: true,
      personal_data_consent_at: result.started_at, skills: [],
    },
    questions: [],
  } as Attempt;
  const saved = {
    ...finalized,
    status: "IN_PROGRESS",
    questions: [question],
  } as Attempt;
  assert.equal(applySavedAttempt(finalized, saved), finalized);
  assert.equal(applySavedAttempt(saved, saved), saved);
});
