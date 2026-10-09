import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement, isValidElement } from "react";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ApiError } from "../src/api";
import type { AssessmentQuestion, Attempt, Availability } from "../src/assessment";
import type { CandidateProfile } from "../src/types";
import { AssessmentDashboardView } from "../src/components/assessment-dashboard";
import { AssessmentAttemptView } from "../src/components/assessment-attempt";
import { AssessmentQuestion as QuestionView } from "../src/components/assessment-question";

const profile: CandidateProfile = {
  id: "candidate", user_id: "user", first_name: "Имя", last_name: "Фамилия",
  city: null, about: null, specialization: "BACKEND", declared_grade: "MIDDLE",
  verified_grade: null, normalized_assessment_score: null, assessment_verified_at: null,
  years_of_experience: null, fsp_id: null, personal_data_consent: true,
  personal_data_consent_at: "2026-10-09T09:00:00Z", skills: [],
};
const availability: Availability = {
  specialization: "BACKEND", active_attempt_id: null, server_now: "2026-10-09T10:00:00Z",
  verification: profile,
  grades: ["JUNIOR", "MIDDLE", "SENIOR"].map((grade) => ({
    grade: grade as "JUNIOR" | "MIDDLE" | "SENIOR", available: true, reason: null, available_at: null,
  })),
};
const dashboardProps: Parameters<typeof AssessmentDashboardView>[0] = {
  data: availability, loading: false, error: null, selected: null, busy: false,
  onSelect: () => {}, onStart: () => {}, onRetry: () => {}, onRefresh: () => {},
};
function dashboardHtml(overrides: Partial<typeof dashboardProps> = {}) {
  return renderToStaticMarkup(createElement(AssessmentDashboardView, { ...dashboardProps, ...overrides }));
}
function question(position: number, selected: string | null = null): AssessmentQuestion {
  return {
    attempt_question_id: `q${position}`, question_id: `bank${position}`, position,
    competency: "PROGRAMMING", difficulty: "BASIC", prompt: `Вопрос ${position}: выберите вариант`,
    selected_option_id: selected,
    options: [1, 2, 3, 4].map((number) => ({ id: `o${number}`, text: `Вариант ${number}` })),
  };
}
const attempt: Attempt = {
  id: "attempt", specialization: "BACKEND", target_grade: "MIDDLE", status: "IN_PROGRESS",
  completion_reason: null, started_at: "2026-10-09T10:00:00Z", expires_at: "2026-10-09T10:30:00Z",
  finished_at: null, normalized_assessment_score: null, competency_scores: null, available_at: null,
  server_now: "2026-10-09T10:01:00Z", questions: [question(1, "o1"), question(2), question(3)],
  verification: profile,
};
const attemptProps: Parameters<typeof AssessmentAttemptView>[0] = {
  attempt, left: 1740, loading: false, error: null, index: 1, saves: {}, saving: false,
  finishing: false, confirm: false, onRetry: () => {}, onFinish: () => {},
  onSave: () => {}, onIndexChange: () => {}, onConfirmChange: () => {},
};
function attemptHtml(overrides: Partial<typeof attemptProps> = {}) {
  return renderToStaticMarkup(createElement(AssessmentAttemptView, { ...attemptProps, ...overrides }));
}
function buttonTag(html: string, label: string) {
  const buttons = html.match(/<button[\s\S]*?<\/button>/g) ?? [];
  const found = buttons.find((button) => button.endsWith(`>${label}</button>`));
  assert.ok(found, `Missing button: ${label}`);
  return found;
}
function elements(node: unknown): ReactElement<Record<string, unknown>>[] {
  if (Array.isArray(node)) return node.flatMap(elements);
  if (!isValidElement<Record<string, unknown>>(node)) return [];
  return [node, ...elements(node.props.children)];
}
function textOf(node: unknown): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(textOf).join("");
  return isValidElement<Record<string, unknown>>(node) ? textOf(node.props.children) : "";
}
function click(tree: unknown, label: string) {
  const button = elements(tree).find((element) => element.type === "button" && textOf(element.props.children) === label);
  assert.ok(button, `Missing button: ${label}`);
  assert.notEqual(button.props.disabled, true);
  (button.props.onClick as () => void)();
}

test("assessment introduction explains purpose without treating declared grade as verified", () => {
  const html = dashboardHtml();
  assert.match(html, /подтвердить профессиональный уровень/);
  assert.match(html, /class="assessment-declared"/);
  assert.match(html, /Указан вами в профиле\. Это не подтверждение квалификации/);
  assert.match(html, /Backend/);
  assert.match(html, /История попыток/);
  assert.match(html, /href="\/candidate"/);
  assert.doesNotMatch(html, /assessment-rules|Начать тест|class="success">Подтверждён/);
});
test("selected grade shows established assessment rules and accessible choice state", () => {
  const html = dashboardHtml({ selected: "MIDDLE" });
  assert.match(html, /data-selected="true"/);
  assert.match(buttonTag(html, "Выбрать Middle"), /aria-pressed="true"/);
  assert.match(html, /20 вопросов, один ответ из четырёх/);
  assert.match(html, /30 минут/);
  assert.match(html, /70\/100/);
  assert.match(html, /50% в каждой из пяти/);
  assert.match(html, /через 7 дней, после успеха — через 90 дней/);
  assert.doesNotMatch(buttonTag(html, "Начать тест"), /disabled/);
});
test("intro renders backend availability reasons and disables unavailable or pending starts", () => {
  const unavailable = {
    ...availability, grades: availability.grades.map((grade) => ({ ...grade, available: false, reason: "EMAIL_NOT_VERIFIED" })),
  };
  const html = dashboardHtml({ data: unavailable, selected: "MIDDLE" });
  assert.match(html, /Подтвердите email перед началом теста/);
  assert.match(buttonTag(html, "Начать тест"), /disabled/);
  for (const grade of ["Junior", "Middle", "Senior"]) {
    assert.match(buttonTag(html, `Выбрать ${grade}`), /disabled/);
    assert.match(buttonTag(dashboardHtml({ selected: "MIDDLE", busy: true }), `Выбрать ${grade}`), /disabled/);
  }
  assert.match(buttonTag(dashboardHtml({ selected: "MIDDLE", busy: true }), "Начинаем…"), /disabled/);
});
test("intro retains the active attempt route and clear loading error and prerequisite states", () => {
  assert.match(dashboardHtml({ data: { ...availability, active_attempt_id: "active-id" } }), /href="\/candidate\/assessment\/active-id"/);
  const loading = dashboardHtml({ loading: true });
  assert.match(loading, /role="status"/);
  assert.doesNotMatch(loading, /<button/);
  const failed = dashboardHtml({ data: null, error: new ApiError(502, "backend_unavailable", "Недоступен") });
  assert.match(failed, /role="alert"/);
  assert.match(failed, /Повторить/);
  const noProfile = dashboardHtml({ data: null, error: new ApiError(404, "profile_not_found", "Нет профиля") });
  assert.match(noProfile, /Сначала заполните профиль кандидата/);
  assert.match(noProfile, /href="\/candidate\/edit"/);
  assert.doesNotMatch(noProfile, /Выбрать Junior|Начать тест/);
  const refresh = dashboardHtml({ error: new ApiError(409, "assessment_cooldown", "Попробуйте позднее"), busy: true });
  assert.match(refresh, /role="alert"/);
  assert.match(buttonTag(refresh, "Обновить доступность"), /disabled/);
});
test("intro passes grade start retry and refresh actions to existing callbacks", () => {
  const calls: string[] = [];
  const props = { ...dashboardProps, selected: "MIDDLE" as const,
    onSelect: (grade: string) => calls.push(grade), onStart: () => calls.push("start"),
    onRetry: () => calls.push("retry"), onRefresh: () => calls.push("refresh") };
  click(AssessmentDashboardView(props), "Выбрать Junior");
  click(AssessmentDashboardView(props), "Начать тест");
  click(AssessmentDashboardView({ ...props, data: null, error: new Error("Offline") }), "Повторить");
  click(AssessmentDashboardView({ ...props, error: new Error("Offline") }), "Обновить доступность");
  assert.deepEqual(calls, ["JUNIOR", "start", "retry", "refresh"]);
});
test("attempt shows server-saved progress and a timer without announcing each tick", () => {
  const html = attemptHtml();
  assert.match(html, /Вопрос 2 \/ 3/);
  assert.match(html, /Ответы сохранены: <strong>1 из 3/);
  assert.match(html, /<progress value="1" max="3" aria-label="Сохранённые ответы"/);
  assert.match(html, /role="timer" aria-label="Осталось времени" aria-live="off">29:00/);
  assert.match(html, /question-number answered/);
  assert.match(html, /aria-label="Вопрос 1, ответ сохранён"/);
  assert.match(html, /question-saved-marker" aria-hidden="true"> ✓/);
  assert.match(html, /aria-current="step" aria-label="Вопрос 2, без ответа"/);
  assert.match(html, /Галочка — ответ сохранён/);
});
test("saving answer stays selected and blocked while progress counts only saved answers", () => {
  const html = attemptHtml({ saving: true, saves: { q2: { option: "o2", state: "saving" } } });
  assert.match(html, /<fieldset disabled="" class="assessment-options"/);
  assert.match(html, /data-state="saving" role="status">Сохраняем…/);
  assert.match(html, /<progress value="1" max="3"/);
  assert.match(html, /data-selected="true"[^>]*><input[^>]*value="o2"/);
  assert.equal((html.match(/checked=""/g) ?? []).length, 1);
  assert.doesNotMatch(buttonTag(html, "Далее"), /disabled/);
});
test("failed autosave keeps selected answer and exposes an accessible retry", () => {
  const html = attemptHtml({ saves: { q2: { option: "o3", state: "error", error: new Error("Offline") } } });
  assert.match(html, /data-state="error" role="status">Не удалось сохранить/);
  assert.match(html, /role="alert"/);
  assert.match(html, /data-selected="true"[^>]*><input[^>]*value="o3"/);
  assert.match(html, /<progress value="1" max="3"/);
  assert.doesNotMatch(buttonTag(html, "Повторить сохранение"), /disabled/);
});
test("saved and unanswered messages follow canonical attempt selections", () => {
  assert.match(attemptHtml({ index: 0 }), /data-state="saved" role="status">Ответ сохранён/);
  assert.match(attemptHtml(), /data-state="unanswered" role="status">Ответ пока не выбран/);
  assert.match(buttonTag(attemptHtml({ index: 0 }), "Назад"), /disabled/);
  assert.doesNotMatch(buttonTag(attemptHtml(), "Назад"), /disabled/);
  const last = attemptHtml({ index: 2 });
  assert.doesNotMatch(last, />Далее<\/button>/);
  assert.doesNotMatch(buttonTag(last, "Завершить тест"), /disabled/);
});
test("finish confirmation keeps unanswered and unsaved warnings and cancellation", () => {
  const html = attemptHtml({ confirm: true, saves: { q2: { option: "o2", state: "error" } } });
  assert.match(html, /class="notice assessment-confirm" role="region" aria-label="Подтверждение завершения"/);
  assert.match(html, /Вопросов без ответа: 2/);
  assert.match(html, /Есть несохранённые изменения/);
  assert.match(html, /После завершения изменить ответы нельзя/);
  assert.match(html, /Вернуться к вопросам/);
  const allSaved = attemptHtml({ confirm: true, attempt: { ...attempt, questions: attempt.questions.map((item) => ({ ...item, selected_option_id: "o1" })) } });
  assert.doesNotMatch(allSaved, /Вопросов без ответа|Есть несохранённые изменения/);
});
test("timeout and pending finish keep answers and final submission unavailable", () => {
  const timeout = attemptHtml({ left: 0, index: 2 });
  assert.match(timeout, /Время вышло\. Завершаем тест по сохранённым ответам/);
  assert.match(timeout, /<fieldset disabled=""/);
  assert.match(buttonTag(timeout, "Завершить тест"), /disabled/);
  const pending = attemptHtml({ finishing: true, confirm: true });
  assert.match(pending, /<fieldset disabled=""/);
  assert.match(buttonTag(pending, "Назад"), /disabled/);
  assert.match(buttonTag(pending, "Далее"), /disabled/);
  assert.match(buttonTag(pending, "Вернуться к вопросам"), /disabled/);
  assert.match(buttonTag(pending, "Завершаем…"), /disabled/);
  const nav = pending.match(/<nav[\s\S]*?<\/nav>/)![0];
  assert.equal((nav.match(/disabled=""/g) ?? []).length, 3);
});
test("attempt loading and request failure retain retry and level selection routes", () => {
  const loading = attemptHtml({ loading: true });
  assert.match(loading, /role="status"/);
  assert.doesNotMatch(loading, /type="radio"|<button/);
  const failed = attemptHtml({ attempt: null, error: new ApiError(404, "assessment_not_found", "Тест не найден") });
  assert.match(failed, /role="alert"/);
  assert.match(failed, /Повторить/);
  assert.match(failed, /href="\/candidate\/assessment"/);
  const finishFailure = attemptHtml({ error: new Error("Offline") });
  assert.match(finishFailure, /role="alert"/);
  assert.doesNotMatch(buttonTag(finishFailure, "Повторить завершение"), /disabled/);
});
test("attempt navigation save retry confirmation and finish delegate existing callbacks", () => {
  const calls: unknown[] = [];
  const props = { ...attemptProps, onIndexChange: (value: number) => calls.push(value),
    onSave: (questionId: string, optionId: string) => calls.push([questionId, optionId]),
    onConfirmChange: (value: boolean) => calls.push(value), onFinish: () => calls.push("finish"), onRetry: () => calls.push("retry") };
  const tree = AssessmentAttemptView(props);
  click(tree, "Назад");
  click(tree, "Далее");
  click(tree, "3");
  click(AssessmentAttemptView({ ...props, saves: { q2: { option: "o3", state: "error" } } }), "Повторить сохранение");
  click(AssessmentAttemptView({ ...props, index: 2 }), "Завершить тест");
  const confirmTree = AssessmentAttemptView({ ...props, confirm: true });
  click(confirmTree, "Вернуться к вопросам");
  click(confirmTree, "Завершить тест");
  click(AssessmentAttemptView({ ...props, attempt: null }), "Повторить");
  assert.deepEqual(calls, [0, 2, 2, ["q2", "o3"], true, false, "finish", "retry"]);
});
test("question labels and description retain selected option and pass only its identifier", () => {
  const selected: string[] = [];
  const props = { question: question(1), selected: "o2", disabled: false, onSelect: (id: string) => selected.push(id) };
  const html = renderToStaticMarkup(createElement(QuestionView, props));
  assert.match(html, /aria-describedby="assessment-prompt-q1 assessment-option-hint-q1"/);
  assert.match(html, /id="assessment-prompt-q1"/);
  assert.match(html, /Ответ сохраняется автоматически/);
  assert.equal((html.match(/type="radio"/g) ?? []).length, 4);
  assert.equal((html.match(/checked=""/g) ?? []).length, 1);
  const second = elements(QuestionView(props)).find((item) => item.type === "input" && item.props.value === "o2")!;
  (second.props.onChange as () => void)();
  assert.deepEqual(selected, ["o2"]);
});
test("assessment view never renders injected answer keys or correctness flags", () => {
  const questions = attempt.questions.map((item) => ({ ...item, correct_answer: "hidden-key", explanation: "hidden-explanation",
    options: item.options.map((option) => ({ ...option, is_correct: true, correct_key: "private-option-key" })) }));
  const html = attemptHtml({ attempt: { ...attempt, questions } });
  assert.doesNotMatch(html, /hidden-key|hidden-explanation|private-option-key|is_correct|correct_answer/);
});
test("finalized attempt renders results and never reopens question controls", () => {
  const html = attemptHtml({ attempt: { ...attempt, status: "FAILED", completion_reason: "SUBMITTED",
    finished_at: "2026-10-09T10:05:00Z", normalized_assessment_score: 0,
    competency_scores: { PROGRAMMING: 0, HTTP_API: 0, DATABASES: 0, ARCHITECTURE: 0, TESTING_SECURITY_DEBUGGING: 0 },
    available_at: "2026-10-16T10:05:00Z" } });
  assert.doesNotMatch(html, /type="radio"|question-navigator|role="timer"|Повторить сохранение/);
  assert.match(html, /Результат попытки/);
});
