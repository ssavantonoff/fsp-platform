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
import { AssessmentResult } from "../src/components/assessment-result";

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
  assert.ok(!html.includes("Первый вариант"));
});
test("passed result shows aggregate score and next attempt date", () => {
  const html = renderToStaticMarkup(
    createElement(AssessmentResult, {
      attempt: {
        ...result,
        status: "PASSED",
        normalized_assessment_score: 100,
        completion_reason: "SUBMITTED",
      },
    }),
  );
  assert.match(html, /Уровень подтверждён/);
  assert.match(html, /PASSED/);
  assert.match(html, /Следующая попытка/);
  assert.ok(!html.includes("Блоки ниже порога"));
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
