import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import ts from "typescript";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ApiError } from "../src/api";
import { getMatches } from "../src/employer-needs";
import type { EmployerNeed, EmployerCandidatePreview, MatchesPage } from "../src/employer-needs";
import type { MatchingView } from "../src/components/employer-matches-screen";
import { deferred as actionDeferred, handler } from "./invitation-handlers";

const python = { id: "python", name: "Python" };
const fastapi = { id: "fastapi", name: "FastAPI" };
const postgres = { id: "postgres", name: "PostgreSQL" };
const django = { id: "django", name: "Django" };
const need: EmployerNeed = {
  id: "need-1", employer_id: "employer", position_title: "Backend Engineer",
  specialization: "BACKEND", required_grade: "MIDDLE", status: "ACTIVE",
  target_experience_years: 3, salary_from: "100000.00", salary_to: "200000.00",
  description: "Backend development", additional_requirements: null,
  created_at: "2026-10-05T12:00:00Z", updated_at: "2026-10-05T12:00:00Z",
  must_have_skills: [python, fastapi], nice_to_have_skills: [postgres, django],
};
const candidate = {
  candidate_id: "candidate-1", display_name: "Мария С.", specialization: "BACKEND",
  verified_grade: "MIDDLE", skills: [python, fastapi, postgres], years_of_experience: 3,
  normalized_assessment_score: 90, assessment_verified_at: "2026-09-18T12:00:00Z",
  professional_fit_score: 76,
  ranking_score: 72.2, fsp_verified: false, fsp_achievement_score: 0,
  fsp_bonus: 0, competition_count: 0, best_result_level: null,
  breakdown: {
    assessment: { score: 60, max: 70, active: true },
    grade: { score: 16, max: 30, active: true, exact_match: false },
    nice_to_have: { score: 0, max: 0, active: false, matched: 1, total: 2 },
    experience: { score: 0, max: 0, active: false },
  },
  matched_must_have_skills: [python, fastapi], matched_nice_to_have_skills: [postgres],
  missing_nice_to_have_skills: [django],
} satisfies EmployerCandidatePreview;
const page: MatchesPage = { items: [candidate], total: 1, limit: 20, offset: 0 };
async function view(overrides: Partial<Parameters<typeof MatchingView>[0]> = {}) {
  const { MatchingView } = await import("../src/components/employer-matches-screen");
  return renderToStaticMarkup(createElement(MatchingView, {
    need, result: page, loading: false, error: null, onRetry: () => {}, ...overrides,
  }));
}
async function card(overrides: Partial<EmployerCandidatePreview> = {}) {
  const { MatchCard } = await import("../src/components/employer-matches-screen");
  return renderToStaticMarkup(createElement(MatchCard, { candidate: { ...candidate, ...overrides } }));
}
test("matching renders loading", async () => {
  const html = await view({ need: null, result: null, loading: true });
  assert.match(html, /role="status"/);
  assert.match(html, /Загрузка подбора/);
  assert.doesNotMatch(html, /<article/);
  assert.doesNotMatch(await view({ loading: true }), /Мария С\./);
});
test("matching renders empty pool", async () => {
  const html = await view({ result: { ...page, items: [], total: 0 } });
  assert.match(html, /Подходящих кандидатов пока нет/);
  assert.match(html, /Проверьте требования или вернитесь к подбору позже/);
  assert.match(html, /href="\/employer\/needs\/need-1\/edit"/);
  assert.doesNotMatch(html, /<article/);
});
test("matching renders API error with retry", async () => {
  const html = await view({ error: new ApiError(502, "backend_unavailable", "Недоступен") });
  assert.match(html, /role="alert"/);
  assert.match(html, /Недоступен/);
  assert.match(html, /Повторить/);
  assert.doesNotMatch(html, /<article/);
});
test("matching preserves ranked candidate order", async () => {
  const items = [
    { ...candidate, candidate_id: "b", display_name: "Candidate B", professional_fit_score: 76.03 },
    { ...candidate, candidate_id: "a", display_name: "Candidate A", professional_fit_score: 76.04 },
    { ...candidate, candidate_id: "c", display_name: "Candidate C", professional_fit_score: 99 },
  ];
  const html = await view({ result: { ...page, items, total: 3 } });
  assert.ok(html.indexOf("Candidate B") < html.indexOf("Candidate A"));
  assert.ok(html.indexOf("Candidate A") < html.indexOf("Candidate C"));
  assert.equal((html.match(/76\.0 \/ 100/g) ?? []).length, 2);
  assert.deepEqual(items.map((item) => item.professional_fit_score), [76.03, 76.04, 99]);
});
test("matching renders effective breakdown and excluded factors", async () => {
  const html = await card();
  assert.match(html, /aria-label="Professional Fit"[\s\S]*76\.0 \/ 100/);
  assert.match(html, /60\.0 \/ 70\.0/);
  assert.match(html, /16\.0 \/ 30\.0/);
  assert.equal((html.match(/Не участвует в расчёте/g) ?? []).length, 2);
  assert.doesNotMatch(html, /0\.0 \/ 0\.0|45\.0|25\.0/);
  assert.match(html, /<details/);
  assert.match(html, /<summary>Почему такой результат<\/summary>/);
});
test("matching separates server Professional Fit, Ranking Score and FSP bonus without recalculating", async () => {
  const html = await card({ professional_fit_score: 76, ranking_score: 81, fsp_verified: true,
    fsp_bonus: 4, fsp_achievement_score: 80, competition_count: 1, best_result_level: "WINNER" });
  assert.match(html, /class="metric metric-primary" aria-label="Professional Fit"[\s\S]*?76\.0 \/ 100/);
  assert.match(html, /class="metric metric-ranking" aria-label="Ranking Score"[\s\S]*?81\.0 \/ 100/);
  assert.equal((html.match(/Ranking Score/g) ?? []).length, 2);
  assert.match(html, /Вклад ФСП: 4\.0 \/ 5/);
  assert.match(html, /MOCK \/ прототип/);
  assert.doesNotMatch(html, /76\.2 \/ 100|вероятность|Шанс найма/i);
});
test("matching renders assessment verification date", async () => {
  assert.match(await card(), /Компетенция подтверждена: 18\.09\.2026/);
  assert.match(await card({ assessment_verified_at: "2026-09-18T23:59:00Z" }), /18\.09\.2026/);
  for (const value of [null, "invalid"]) {
    const html = await card({ assessment_verified_at: value });
    assert.match(html, /Дата подтверждения не указана/);
    assert.doesNotMatch(html, /Invalid Date/);
  }
});
test("matching preview renders masked name and no contacts", async () => {
  assert.deepEqual(Object.keys(candidate).sort(), [
    "ranking_score", "fsp_verified", "fsp_achievement_score", "fsp_bonus", "competition_count", "best_result_level",
    "candidate_id", "display_name", "specialization", "verified_grade", "skills",
    "years_of_experience", "normalized_assessment_score", "assessment_verified_at",
    "professional_fit_score", "breakdown", "matched_must_have_skills",
    "matched_nice_to_have_skills", "missing_nice_to_have_skills",
  ].sort());
  const injected = {
    ...candidate, email: "PRIVATE_EMAIL_MARKER", phone: "PRIVATE_PHONE_MARKER",
    telegram: "PRIVATE_TG_MARKER", last_name: "PRIVATE_SURNAME_MARKER",
    fsp_id: "PRIVATE_FSP_MARKER", about: "PRIVATE_ABOUT_MARKER",
  };
  for (const html of [await card(injected), await view({ result: { ...page, items: [injected] } })]) {
    assert.match(html, /Мария С\./);
    assert.doesNotMatch(html, /PRIVATE_|Связаться|Телефон|Email|Telegram|Открыть контакты|<pre/);
  }
});
test("matching offers invitation action and history for ACTIVE Need", async () => {
  const html = await view();
  assert.match(html, /Пригласить/);
  assert.match(html, /href="\/employer\/needs\/need-1\/invitations"/);
});
test("invitation form preserves plain text and shows salary, busy and feedback", async () => {
  const { InvitationForm } = await import("../src/components/employer-matches-screen");
  const props = { need, candidate, message: "<b>hello</b>", busy: false, success: "", error: null, onChange: () => {}, onSubmit: () => {}, onCancel: () => {} };
  const html = renderToStaticMarkup(createElement(InvitationForm, props));
  assert.match(html, /100000\.00–200000\.00/);
  assert.match(html, /maxLength="2000"/);
  assert.match(html, /&lt;b&gt;hello/);
  assert.match(html, /Отправить приглашение/);
  assert.match(renderToStaticMarkup(createElement(InvitationForm, { ...props, busy: true })), /disabled=""/);
  assert.match(renderToStaticMarkup(createElement(InvitationForm, { ...props, success: "Приглашение отправлено" })), /Приглашение отправлено/);
  assert.match(renderToStaticMarkup(createElement(InvitationForm, { ...props, error: new ApiError(404, "candidate_not_available", "Кандидат недоступен") })), /Кандидат недоступен/);
});
test("invite submit guards double clicks, success repeats and preserves input on server error", async () => {
  const response = actionDeferred<unknown>();
  const calls: unknown[] = [];
  const pending = { current: false }; const mounted = { current: true };
  let success = ""; let error: unknown = null; let busy = false;
  const scope = { pending, mounted, need, candidate, success, message: "  Сообщение  ", ApiError,
    sendInvitation: async (id: string, payload: unknown) => { calls.push([id, payload]); return response.promise; },
    setBusy: (value: boolean) => { busy = value; }, setError: (value: unknown) => { error = value; }, setSuccess: (value: string) => { success = value; },
  };
  const submit = handler("src/components/employer-matches-screen.tsx", "InviteCandidate", "submit", scope);
  const first = submit(); await submit(); assert.equal(calls.length, 1); assert.equal(busy, true);
  response.resolve({ status: "SENT" }); await first;
  assert.equal(success, "Приглашение отправлено"); assert.equal(error, null); assert.equal(busy, false);
  assert.equal(JSON.stringify(calls[0]), JSON.stringify([need.id, { candidate_id: candidate.candidate_id, message: "  Сообщение  " }]));
  const conflict = new ApiError(404, "candidate_not_available", "Кандидат недоступен");
  const retry = handler("src/components/employer-matches-screen.tsx", "InviteCandidate", "submit", { ...scope, success: "", sendInvitation: async () => { throw conflict; } });
  await retry(); assert.equal(error, conflict); assert.equal(pending.current, false);
  const repeated = handler("src/components/employer-matches-screen.tsx", "InviteCandidate", "submit", { ...scope, success: "sent" });
  await repeated(); assert.equal(calls.length, 1);
});
test("matching blocks non ACTIVE need", async () => {
  for (const status of ["DRAFT", "CLOSED"] as const) {
    const html = await view({ need: { ...need, status } });
    assert.match(html, status === "DRAFT" ? /Подбор доступен после активации потребности/ : /Для закрытой потребности подбор недоступен/);
    assert.match(html, /К потребности/);
    assert.doesNotMatch(html, /Мария С\.|<article/);
  }
});
test("matching API forwards limit offset and errors", async () => {
  const original = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = async (url, init) => {
    calls.push(String(url));
    assert.equal(init?.method ?? "GET", "GET");
    assert.equal(init?.credentials, "same-origin");
    assert.equal(init?.cache, "no-store");
    return Response.json(page);
  };
  try {
    assert.deepEqual(await getMatches("need/a b"), page);
    await getMatches("need", 10, 30);
    assert.deepEqual(calls, [
      "/api/employer/needs/need%2Fa%20b/matches?limit=20&offset=0",
      "/api/employer/needs/need/matches?limit=10&offset=30",
    ]);
    globalThis.fetch = async () => Response.json({ error: { code: "need_state_conflict", message: "Закрыта", fields: [] } }, { status: 409 });
    await assert.rejects(getMatches("need"), (error: unknown) => error instanceof ApiError && error.status === 409 && error.code === "need_state_conflict");
  } finally { globalThis.fetch = original; }
});
test("matching renders matched and missing nice skills", async () => {
  const html = await card();
  assert.match(html, /Обязательные навыки совпали<\/dt><dd>Python, FastAPI/);
  assert.match(html, /Совпавшие желательные навыки<\/dt><dd>PostgreSQL/);
  assert.match(html, /Не хватает из желательных<\/dt><dd>Django/);
  assert.match(html, /Совпало: 1 из 2/);
  const empty = await card({ matched_nice_to_have_skills: [], missing_nice_to_have_skills: [] });
  assert.match(empty, /Нет совпадений/);
  assert.match(empty, /Все желательные навыки совпали/);
});
test("matching identifies self-declared skills", async () => {
  const html = await card();
  assert.match(html, /Навыки, указанные кандидатом/);
  assert.match(html, /Результат оценки<\/dt><dd>90 \/ 100/);
  assert.doesNotMatch(html, /Подтверждённые навыки|Подтверждённый опыт|Вероятность|AI score|Шанс найма/);
});
test("matching explains exact and compatible grade", async () => {
  assert.match(await card(), /Допустимый более высокий уровень/);
  assert.match(await card({ breakdown: { ...candidate.breakdown, grade: { ...candidate.breakdown.grade, exact_match: true } } }), /Точное соответствие требуемому уровню/);
});
test("matching distinguishes null experience and active zero factor", async () => {
  const html = await card({ years_of_experience: null, breakdown: { ...candidate.breakdown, experience: { score: 0, max: 15, active: true } } });
  assert.match(html, /Опыт, лет<\/dt><dd>не указан/);
  assert.match(html, /Опыт<\/dt><dd>0\.0 \/ 15\.0/);
  assert.equal((html.match(/Не участвует в расчёте/g) ?? []).length, 1);
  assert.match(await card({ years_of_experience: 0 }), /Опыт, лет<\/dt><dd>0<\/dd>/);
});
test("matching pagination uses total and server page boundaries", async () => {
  const first = { ...page, items: Array.from({ length: 20 }, (_, i) => ({ ...candidate, candidate_id: String(i) })), total: 21 };
  const html = await view({ result: first, onPageChange: () => {} });
  assert.match(html, /Подходящих кандидатов: 21/);
  const buttons = html.match(/<button[^>]*>(?:Назад|Далее)<\/button>/g)!;
  assert.match(buttons[0], /disabled/);
  assert.doesNotMatch(buttons[1], /disabled/);
  const last = await view({ result: { ...page, total: 21, offset: 20 }, offset: 20, onPageChange: () => {} });
  const lastButtons = last.match(/<button[^>]*>(?:Назад|Далее)<\/button>/g)!;
  assert.doesNotMatch(lastButtons[0], /disabled/);
  assert.match(lastButtons[1], /disabled/);
});
test("matching hides results for a different requested offset", async () => {
  const html = await view({ offset: 20 });
  assert.match(html, /Загрузка подбора/);
  assert.doesNotMatch(html, /Мария С\./);
  const beyond = await view({ result: { ...page, total: 21, items: [], offset: 40 }, offset: 40 });
  assert.doesNotMatch(beyond, /Подходящих кандидатов пока нет/);
  assert.match(beyond, /Подходящих кандидатов: 21/);
});
test("matching missing Need and profile errors provide safe navigation", async () => {
  const missing = await view({ need: null, error: new ApiError(404, "need_not_found", "Потребность не найдена.") });
  assert.match(missing, /Потребность не найдена/);
  assert.match(missing, /href="\/employer\/needs"/);
  assert.doesNotMatch(missing, /<article/);
  const profile = await view({ need: null, error: new ApiError(404, "profile_not_found", "Нет профиля") });
  assert.match(profile, /Сначала заполните профиль компании/);
  assert.match(profile, /href="\/employer\/edit"/);
});
test("matching formats scores for display only", async () => {
  const { formatScore } = await import("../src/components/employer-matches-screen");
  assert.equal(formatScore(93.75), "93.8");
  assert.equal(formatScore(76), "76.0");
  for (const value of [NaN, Infinity, -Infinity]) assert.equal(formatScore(value), "—");
});

// Run the actual request callback, as in Task 9, without mounting DOM/auth hooks.
function requestLoader() {
  const source = readFileSync("src/components/employer-matches-screen.tsx", "utf8");
  const ast = ts.createSourceFile("screen.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const content = ast.statements.find((node): node is ts.FunctionDeclaration =>
    ts.isFunctionDeclaration(node) && node.name?.text === "MatchesContent");
  const declaration = content?.body?.statements.filter(ts.isVariableStatement)
    .flatMap((statement) => [...statement.declarationList.declarations])
    .find((node) => node.name.getText(ast) === "load");
  assert.ok(declaration?.initializer && ts.isCallExpression(declaration.initializer));
  const callback = declaration.initializer.arguments[0];
  const code = ts.transpileModule(`(${callback.getText(ast)});`, {
    compilerOptions: { target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const state = { need: null as EmployerNeed | null, result: null as MatchesPage | null, error: null as unknown, loading: true };
  const calls: string[] = [];
  const generation = { current: 0 };
  const providers = {
    getNeed: async (): Promise<EmployerNeed> => need,
    getMatches: async (offset: number): Promise<MatchesPage> => ({ ...page, offset }),
  };
  function load(offset = 0): Promise<void> {
    const run = runInNewContext(code, {
      needId: need.id, offset, limit: 20, generation, ApiError,
      getNeed: async () => { calls.push("need"); return providers.getNeed(); },
      getMatches: async (_id: string, limit: number, offset: number) => {
        calls.push(`matches:${limit}:${offset}`); return providers.getMatches(offset);
      },
      setNeed: (value: EmployerNeed) => { state.need = value; },
      setResult: (value: MatchesPage | null) => { state.result = value; },
      setError: (value: unknown) => { state.error = value; },
      setLoading: (value: boolean) => { state.loading = value; },
    }) as () => Promise<void>;
    return run();
  }
  return { load, state, calls, generation, providers };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
test("matching requests Need first and never matches DRAFT or CLOSED", async () => {
  const active = requestLoader();
  await active.load(20);
  assert.deepEqual(active.calls, ["need", "matches:20:20"]);
  for (const status of ["DRAFT", "CLOSED"] as const) {
    const loader = requestLoader();
    loader.providers.getNeed = async () => ({ ...need, status });
    await loader.load();
    assert.deepEqual(loader.calls, ["need"]);
    assert.equal(loader.state.result, null);
    assert.equal(loader.state.need?.status, status);
    assert.equal(loader.state.loading, false);
  }
});
test("matching conflict refreshes status once without retrying matches", async () => {
  const loader = requestLoader();
  let reads = 0;
  loader.providers.getNeed = async () => ({ ...need, status: ++reads === 1 ? "ACTIVE" : "CLOSED" });
  const conflict = new ApiError(409, "need_state_conflict", "Закрыта");
  loader.providers.getMatches = async () => { throw conflict; };
  await loader.load();
  assert.deepEqual(loader.calls, ["need", "matches:20:0", "need"]);
  assert.equal(loader.state.need?.status, "CLOSED");
  assert.equal(loader.state.error, conflict);
  assert.equal(loader.state.result, null);
});
test("matching ignores late page responses and writes after unmount", async () => {
  const loader = requestLoader();
  const old = deferred<MatchesPage>();
  const started = deferred<void>();
  loader.providers.getMatches = async (offset) => {
    if (offset === 0) { started.resolve(); return old.promise; }
    return { ...page, offset, items: [{ ...candidate, display_name: "New page" }] };
  };
  const first = loader.load();
  await started.promise;
  await loader.load(20);
  const current = loader.state.result;
  old.resolve(page);
  await first;
  assert.equal(loader.state.result, current);
  assert.equal(loader.state.result?.offset, 20);
  const unmounted = requestLoader();
  const pendingNeed = deferred<EmployerNeed>();
  unmounted.providers.getNeed = () => pendingNeed.promise;
  const pending = unmounted.load();
  unmounted.generation.current++;
  pendingNeed.resolve(need);
  await pending;
  assert.deepEqual(unmounted.calls, ["need"]);
  assert.equal(unmounted.state.need, null);
  assert.equal(unmounted.state.loading, true);
});
test("matching retry refreshes Need after failed initial load", async () => {
  const loader = requestLoader();
  const failure = new ApiError(503, "backend_unavailable", "Недоступен");
  loader.providers.getNeed = async () => { throw failure; };
  await loader.load();
  assert.deepEqual(loader.calls, ["need"]);
  assert.equal(loader.state.error, failure);
  loader.state.error = null;
  loader.providers.getNeed = async () => need;
  await loader.load();
  assert.deepEqual(loader.calls, ["need", "need", "matches:20:0"]);
  assert.deepEqual(loader.state.result, page);
});
