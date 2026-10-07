import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import ts from "typescript";
import { test } from "node:test";
import { ApiError } from "../src/api";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { EmployerNeedForm } from "../src/components/employer-need-form";
import type { NeedFormProps } from "../src/components/employer-need-form";
import { NeedEditorView, NeedsListView } from "../src/components/employer-needs-screen";
import {
  activateNeed, closeNeed, createNeed, defaultNeedFormValues, getNeed,
  listNeeds, needActions, needFormValues, needPayload, needsNavigationVisible,
  updateNeed, validateNeedForm,
} from "../src/employer-needs";
import type { EmployerNeed, NeedFormValues } from "../src/employer-needs";

const values: NeedFormValues = {
  position_title: " Backend engineer ", specialization: "BACKEND", required_grade: "MIDDLE",
  target_experience_years: "", salary_from: " 100000.50 ", salary_to: "200000",
  description: " Описание\nпотребности ", additional_requirements: " ",
  must_have_skill_ids: ["python"], nice_to_have_skill_ids: ["django"],
};
const need: EmployerNeed = {
  ...needPayload(values), id: "need", employer_id: "employer", status: "DRAFT",
  created_at: "2026-10-05T12:00:00Z", updated_at: "2026-10-05T12:00:00Z",
  must_have_skills: [{ id: "python", name: "Python" }],
  nice_to_have_skills: [{ id: "django", name: "Django" }],
};
test("need form rejects empty title and must-have", () => {
  const errors = validateNeedForm({ ...values, position_title: "  ", description: "\n", must_have_skill_ids: [] });
  assert.ok(errors.position_title);
  assert.ok(errors.description);
  assert.ok(errors.must_have_skill_ids);
  assert.ok(validateNeedForm({ ...values, position_title: "a".repeat(201) }).position_title);
  assert.deepEqual(validateNeedForm(values), {});
  assert.deepEqual(defaultNeedFormValues(), {
    position_title: "", specialization: "BACKEND", required_grade: "MIDDLE",
    target_experience_years: "", salary_from: "", salary_to: "", description: "",
    additional_requirements: "", must_have_skill_ids: [], nice_to_have_skill_ids: [],
  });
});
test("need form rejects salary order and nonfinite negative experience", () => {
  assert.ok(validateNeedForm({ ...values, salary_from: "200001" }).salary_from);
  for (const invalid of ["-1", "NaN", "Infinity", "-Infinity", "oops"]) {
    assert.ok(validateNeedForm({ ...values, salary_from: invalid }).salary_from, invalid);
    assert.ok(validateNeedForm({ ...values, salary_to: invalid }).salary_to, invalid);
    assert.ok(validateNeedForm({ ...values, target_experience_years: invalid }).target_experience_years, invalid);
  }
  for (const target of ["", "0", "1.5", "81"]) assert.deepEqual(validateNeedForm({ ...values, target_experience_years: target }), {});
});
test("salary validation preserves decimal precision and rejects malformed money", () => {
  for (const invalid of ["", " ", "1e5", "1,000", "1.001", "10000000000", "9999999999.999", "1foo", ".", "0x10"])
    assert.ok(validateNeedForm({ ...values, salary_from: invalid }).salary_from, invalid);
  for (const salary of ["0", "100000", "100000.5", "100000.50", "9999999999.99", "0000000000001.50"])
    assert.deepEqual(validateNeedForm({ ...values, salary_from: salary, salary_to: salary }), {});
  assert.ok(validateNeedForm({ ...values, salary_from: "0.11", salary_to: "0.10" }).salary_from);
  assert.deepEqual(validateNeedForm({ ...values, salary_from: "0.10", salary_to: "0.1" }), {});
});
test("need form rejects duplicate and overlapping skills", () => {
  assert.ok(validateNeedForm({ ...values, must_have_skill_ids: ["python", "python"] }).must_have_skill_ids);
  assert.ok(validateNeedForm({ ...values, nice_to_have_skill_ids: ["django", "django"] }).nice_to_have_skill_ids);
  const errors = validateNeedForm({ ...values, nice_to_have_skill_ids: ["python"] });
  assert.ok(errors.must_have_skill_ids);
  assert.ok(errors.nice_to_have_skill_ids);
});
test("need payload excludes ownership and calculated fields", () => {
  const payload = needPayload({ ...values, ...{ id: "injected", employer_id: "other", status: "ACTIVE", professional_fit: 100 } });
  assert.deepEqual(Object.keys(payload).sort(), ["position_title", "specialization", "required_grade", "target_experience_years", "salary_from", "salary_to", "description", "additional_requirements", "must_have_skill_ids", "nice_to_have_skill_ids"].sort());
  assert.equal(payload.position_title, "Backend engineer");
  assert.equal(payload.description, "Описание\nпотребности");
  assert.equal(payload.target_experience_years, null);
  assert.equal(needPayload({ ...values, target_experience_years: "0" }).target_experience_years, 0);
  assert.equal(needPayload({ ...values, target_experience_years: "1.5" }).target_experience_years, 1.5);
  assert.equal(payload.additional_requirements, null);
  assert.equal(payload.salary_from, "100000.50");
  assert.equal(typeof payload.salary_to, "string");
  assert.notEqual(payload.must_have_skill_ids, values.must_have_skill_ids);
  assert.notEqual(payload.nice_to_have_skill_ids, values.nice_to_have_skill_ids);
});
test("need form values preserve server strings and skill order", () => {
  const mapped = needFormValues({ ...need, target_experience_years: 0, salary_from: "100000.00", must_have_skills: [{ id: "z", name: "Z" }, { id: "a", name: "A" }] });
  assert.equal(mapped.target_experience_years, "0");
  assert.equal(mapped.salary_from, "100000.00");
  assert.equal(mapped.additional_requirements, "");
  assert.deepEqual(mapped.must_have_skill_ids, ["z", "a"]);
  assert.equal(needFormValues(need).target_experience_years, "");
});
test("need API uses cookie transport and correct methods", async () => {
  const original = globalThis.fetch;
  const calls: { url: string; method: string; body: unknown }[] = [];
  globalThis.fetch = async (url, init) => {
    assert.equal(init?.credentials, "same-origin");
    assert.equal(init?.cache, "no-store");
    assert.equal((init?.headers as Record<string, string>)["Content-Type"], "application/json");
    calls.push({ url: String(url), method: init?.method ?? "GET", body: init?.body });
    return Response.json(String(url).includes("?") ? { items: [need], total: 1, limit: 20, offset: 0 } : need);
  };
  try {
    assert.equal((await listNeeds()).items[0].id, need.id);
    await listNeeds(20, 40);
    const id = "need/a b";
    await getNeed(id);
    const payload = needPayload(values);
    await createNeed(payload);
    await updateNeed(id, payload);
    await activateNeed(id);
    await closeNeed(id);
    assert.deepEqual(calls, [
      { url: "/api/employer/needs?limit=20&offset=0", method: "GET", body: undefined },
      { url: "/api/employer/needs?limit=20&offset=40", method: "GET", body: undefined },
      { url: "/api/employer/needs/need%2Fa%20b", method: "GET", body: undefined },
      { url: "/api/employer/needs", method: "POST", body: JSON.stringify(payload) },
      { url: "/api/employer/needs/need%2Fa%20b", method: "PUT", body: JSON.stringify(payload) },
      { url: "/api/employer/needs/need%2Fa%20b/activate", method: "POST", body: undefined },
      { url: "/api/employer/needs/need%2Fa%20b/close", method: "POST", body: undefined },
    ]);
  } finally { globalThis.fetch = original; }
});
test("need API preserves server validation and state conflicts", async () => {
  const original = globalThis.fetch;
  try {
    for (const [status, code] of [[422, "validation_error"], [409, "need_state_conflict"], [404, "need_not_found"]] as const) {
      globalThis.fetch = async () => Response.json({ error: { code, message: "Ошибка", fields: [{ field: "salary_from", message: "Проверьте" }] } }, { status });
      await assert.rejects(updateNeed("need", needPayload(values)), (error: unknown) => error instanceof ApiError && error.code === code && error.fields[0].field === "salary_from");
    }
  } finally { globalThis.fetch = original; }
});
test("need statuses expose correct actions", () => {
  assert.deepEqual(needActions("DRAFT"), { edit: true, activate: true, close: false, matches: false });
  assert.deepEqual(needActions("ACTIVE"), { edit: true, activate: false, close: true, matches: true });
  assert.deepEqual(needActions("CLOSED"), { edit: false, activate: false, close: false, matches: false });
});
test("needs navigation is employer only", () => {
  assert.equal(needsNavigationVisible("EMPLOYER"), true);
  assert.equal(needsNavigationVisible("CANDIDATE"), false);
  assert.equal(needsNavigationVisible(null), false);
});

const form: NeedFormProps = {
  values, skills: [...need.must_have_skills, ...need.nice_to_have_skills],
  busy: false, errors: {}, onChange: () => { }, onSubmit: () => { },
};
const listProps = { items: [], loading: false, error: null, onRetry: () => { }, onAction: () => { } };
function editorHtml(overrides: Partial<Parameters<typeof NeedEditorView>[0]> = {}) {
  return renderToStaticMarkup(createElement(NeedEditorView, { need, loading: false, error: null, form, onRetry: () => { }, ...overrides }));
}
test("ACTIVE editor remains editable", () => {
  const html = editorHtml({ need: { ...need, status: "ACTIVE" } });
  assert.equal((html.match(/<form/g) ?? []).length, 1);
  assert.match(html, /Потребность активна/);
  assert.match(html, /следующий подбор/);
  assert.doesNotMatch(html, /<fieldset disabled/);
});
test("CLOSED editor is blocked", () => {
  const html = editorHtml({ need: { ...need, status: "CLOSED" } });
  assert.doesNotMatch(html, /<form/);
  assert.match(html, /Потребность закрыта/);
  assert.match(html, /href="\/employer\/needs"/);
  assert.match(html, /Backend engineer/);
  assert.match(html, /\/invitations"/);
});
test("invitation history remains reachable for CLOSED Needs", () => {
  const html = renderToStaticMarkup(createElement(NeedsListView, { ...listProps, items: [{ ...need, status: "CLOSED" }] }));
  assert.match(html, /\/invitations"/);
  assert.doesNotMatch(html, /\/matches"/);
});
test("need list renders loading empty and API error states", () => {
  const render = (overrides: Partial<Parameters<typeof NeedsListView>[0]>) => renderToStaticMarkup(createElement(NeedsListView, { ...listProps, ...overrides }));
  const loading = render({ loading: true, items: [need] });
  assert.match(loading, /role="status"/);
  assert.doesNotMatch(loading, /Backend engineer/);
  const empty = render({});
  assert.match(empty, /У вас пока нет потребностей/);
  assert.match(empty, /href="\/employer\/needs\/new"/);
  const error = render({ error: new ApiError(502, "backend_unavailable", "Недоступен") });
  assert.match(error, /role="alert"/);
  assert.match(error, /Повторить/);
});
test("need form disables invalid or busy submit", () => {
  const render = (overrides: Partial<NeedFormProps>) => renderToStaticMarkup(createElement(EmployerNeedForm, { ...form, ...overrides }));
  assert.match(render({ values: defaultNeedFormValues() }), /<button[^>]*type="submit"[^>]*disabled/);
  const busy = render({ busy: true });
  assert.match(busy, /<fieldset disabled/);
  assert.match(busy, /<button[^>]*type="submit"[^>]*disabled/);
  assert.doesNotMatch(render({}), /<button[^>]*type="submit"[^>]*disabled/);
});
test("skill selection disables opposite category", () => {
  const html = renderToStaticMarkup(createElement(EmployerNeedForm, form));
  const inputs = html.match(/<input[^>]*type="checkbox"[^>]*>/g)!;
  const input = (name: string, value: string) => inputs.find((tag) => tag.includes(`name="${name}"`) && tag.includes(`value="${value}"`))!;
  assert.match(input("must_have_skill_ids", "python"), /checked=""/);
  assert.match(input("nice_to_have_skill_ids", "python"), /disabled=""/);
  assert.match(input("must_have_skill_ids", "django"), /disabled=""/);
  assert.match(input("nice_to_have_skill_ids", "django"), /checked=""/);
});
test("profile not found links to employer profile", () => {
  const error = new ApiError(404, "profile_not_found", "Нет профиля");
  for (const html of [editorHtml({ error }), renderToStaticMarkup(createElement(NeedsListView, { ...listProps, error }))]) {
    assert.match(html, /Сначала заполните профиль компании/);
    assert.match(html, /href="\/employer\/edit"/);
  }
  assert.match(editorHtml({ error }), /<form/); // failed create retains the entered values
});
test("list actions follow each Need status and server order", () => {
  const items = [
    { ...need, id: "b", position_title: "First DRAFT" },
    { ...need, id: "a", position_title: "Second ACTIVE", status: "ACTIVE" as const },
    { ...need, id: "c", position_title: "Third CLOSED", status: "CLOSED" as const },
  ];
  const html = renderToStaticMarkup(createElement(NeedsListView, { ...listProps, items }));
  const cards = html.match(/<article[\s\S]*?<\/article>/g)!;
  assert.equal(cards.length, 3);
  assert.match(cards[0], /First DRAFT/);
  assert.match(cards[0], /\/b\/edit/);
  assert.match(cards[0], /Активировать/);
  assert.doesNotMatch(cards[0], /matches|Закрыть/);
  assert.match(cards[1], /Second ACTIVE/);
  assert.match(cards[1], /\/a\/edit/);
  assert.match(cards[1], /\/a\/matches/);
  assert.match(cards[1], /Закрыть/);
  assert.doesNotMatch(cards[1], /Активировать/);
  assert.doesNotMatch(cards[2], /<button|\/edit|\/matches/);
  assert.doesNotMatch(html, /employer_id|employer<\/dd>/);
});
test("editor loading and missing Need never expose a default edit form", () => {
  const loading = editorHtml({ loading: true });
  assert.match(loading, /role="status"/);
  assert.doesNotMatch(loading, /<form/);
  const missing = editorHtml({ need: null, error: new ApiError(404, "need_not_found", "Потребность не найдена.") });
  assert.doesNotMatch(missing, /<form/);
  assert.match(missing, /Потребность не найдена/);
  assert.match(missing, /href="\/employer\/needs"/);
});
test("busy list disables only the pending Need action", () => {
  const html = renderToStaticMarkup(createElement(NeedsListView, { ...listProps, items: [need, { ...need, id: "other" }], busyIds: [need.id] }));
  const cards = html.match(/<article[\s\S]*?<\/article>/g)!;
  assert.match(cards[0], /<button[^>]*disabled/);
  assert.doesNotMatch(cards[0], /href="[^\"]*\/edit"/);
  assert.doesNotMatch(cards[1], /<button[^>]*disabled/);
});
test("form shows local field errors with associated labels", () => {
  const invalid = defaultNeedFormValues();
  const html = renderToStaticMarkup(createElement(EmployerNeedForm, { ...form, values: invalid, errors: validateNeedForm(invalid) }));
  assert.match(html, /role="alert"/);
  assert.match(html, /Укажите позицию/);
  assert.match(html, /Выберите хотя бы один обязательный навык/);
  assert.match(html, /Если не указано, опыт не участвует/);
  assert.match(html, /Не влияет на Professional Fit/);
});

test("server save error preserves editable values and CLOSED conflict stays visible", () => {
  const validation = new ApiError(422, "validation_error", "Проверьте поля", [{ field: "salary_from", message: "Проверьте сумму" }]);
  const editable = editorHtml({ error: validation });
  assert.match(editable, /<form/);
  assert.match(editable, /Backend engineer/);
  assert.match(editable, /Зарплата от: Проверьте сумму/);
  const conflict = editorHtml({ need: { ...need, status: "CLOSED" }, error: new ApiError(409, "need_state_conflict", "Закрытую потребность нельзя изменить.") });
  assert.doesNotMatch(conflict, /<form/);
  assert.match(conflict, /Закрытую потребность нельзя изменить/);
});
test("failed initial editor load shows retry without editable defaults", () => {
  const html = editorHtml({ need: null, ready: false, error: new ApiError(502, "backend_unavailable", "Недоступен") });
  assert.doesNotMatch(html, /<form/);
  assert.match(html, /Повторить/);
  assert.match(html, /role="alert"/);
});
test("invalid or busy form handler does not submit", () => {
  let submitted = 0;
  let prevented = 0;
  const event = { preventDefault: () => { prevented++; } };
  for (const override of [{ values: defaultNeedFormValues() }, { busy: true }, {}]) {
    const element = EmployerNeedForm({ ...form, ...override, onSubmit: () => { submitted++; } });
    element.props.onSubmit(event);
  }
  assert.equal(prevented, 3);
  assert.equal(submitted, 1);
});

// Exercise the real submit body without mounting router/auth/hooks or copying its logic.
// router.push deliberately leaves the create component mounted with needId undefined.
function navigationSubmit() {
  const source = readFileSync("src/components/employer-needs-screen.tsx", "utf8");
  const ast = ts.createSourceFile("screen.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const editor = ast.statements.find((node): node is ts.FunctionDeclaration =>
    ts.isFunctionDeclaration(node) && node.name?.text === "NeedEditorContent");
  const submit = editor?.body?.statements.find((node): node is ts.FunctionDeclaration =>
    ts.isFunctionDeclaration(node) && node.name?.text === "submit");
  assert.ok(submit);
  const createdNeedId = { current: null as string | null };
  const pushes: { path: string; rememberedId: string | null }[] = [];
  const errors: unknown[] = [];
  const busy: boolean[] = [];
  const successes: string[] = [];
  const scope = {
    needId: undefined as string | undefined,
    createdNeedId,
    saving: { current: false },
    ready: true,
    need: null as EmployerNeed | null,
    values,
    validateNeedForm, needPayload, needFormValues,
    createNeed, updateNeed, getNeed, ApiError,
    setBusy: (value: boolean) => { busy.push(value); },
    setError: (error: unknown) => { if (error != null) errors.push(error); },
    setSuccess: (message: string) => { successes.push(message); },
    setNeed: (saved: EmployerNeed) => { scope.need = saved; },
    setValues: (saved: NeedFormValues) => { scope.values = saved; },
    router: { push: (path: string) => { pushes.push({ path, rememberedId: createdNeedId.current }); } },
  };
  const code = ts.transpileModule(`${submit.getText(ast)}\nsubmit;`, {
    compilerOptions: { target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const run = runInNewContext(code, scope) as () => Promise<void>;
  return { run, scope, pushes, errors, busy, successes };
}
test("create followed by save during pending navigation sends POST then PUT for the same Need", async () => {
  const original = globalThis.fetch;
  const calls: { path: string; method: string }[] = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ path: String(url), method: init?.method ?? "GET" });
    return Response.json({ ...need, id: "created-id" });
  };
  try {
    const editor = navigationSubmit();
    await editor.run();
    await editor.run();
    assert.deepEqual(calls, [
      { path: "/api/employer/needs", method: "POST" },
      { path: "/api/employer/needs/created-id", method: "PUT" },
    ]);
    assert.deepEqual(editor.pushes, [{ path: "/employer/needs/created-id/edit", rememberedId: "created-id" }]);
    assert.equal(editor.scope.needId, undefined);
    assert.equal(editor.scope.createdNeedId.current, "created-id");
    assert.equal(editor.scope.saving.current, false);
    assert.deepEqual(editor.busy, [true, false, true, false]);
    assert.deepEqual(editor.errors, []);
    assert.equal(editor.successes.at(-1), "Потребность сохранена.");
  } finally { globalThis.fetch = original; }
});
test("failed create can retry and a fresh editor can create a different Need", async () => {
  const original = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = async () => {
    requests++;
    return requests === 1
      ? Response.json({ error: { code: "need_conflict", message: "Не сохранено", fields: [] } }, { status: 409 })
      : Response.json({ ...need, id: `created-${requests}` });
  };
  try {
    const editor = navigationSubmit();
    await editor.run();
    assert.equal(editor.scope.createdNeedId.current, null);
    assert.equal(editor.scope.saving.current, false);
    assert.equal(editor.scope.need, null);
    assert.equal(editor.errors.length, 1);
    await editor.run();
    assert.equal(editor.scope.createdNeedId.current, "created-2");
    const fresh = navigationSubmit();
    await fresh.run();
    assert.equal(fresh.scope.createdNeedId.current, "created-3");
  } finally { globalThis.fetch = original; }
});

test("pending navigation update conflict reloads the created Need and blocks CLOSED submit", async () => {
  const original = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = async (url, init) => {
    const method = init?.method ?? "GET";
    calls.push(`${method} ${url}`);
    if (method === "PUT") return Response.json({ error: { code: "need_state_conflict", message: "Закрыта", fields: [] } }, { status: 409 });
    return Response.json({ ...need, id: "created-id", status: method === "GET" ? "CLOSED" : "DRAFT" });
  };
  try {
    const editor = navigationSubmit();
    await editor.run();
    await editor.run();
    await editor.run();
    assert.deepEqual(calls, [
      "POST /api/employer/needs",
      "PUT /api/employer/needs/created-id",
      "GET /api/employer/needs/created-id",
    ]);
    assert.equal(editor.scope.need?.status, "CLOSED");
    assert.equal(editor.scope.createdNeedId.current, "created-id");
    assert.equal(editor.errors.length, 1);
    assert.ok(editor.errors[0] instanceof ApiError);
  } finally { globalThis.fetch = original; }
});
