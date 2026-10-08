import assert from "node:assert/strict";
import { afterEach, mock, test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import ts from "typescript";
import { ApiError } from "../src/api";
import { getFspStatus, verifyFsp, refreshFsp, unlinkFsp, type FspStatus } from "../src/fsp";
import { FspProfileView, FspExplanation } from "../src/components/fsp-profile";
import { deferred, handler, settle } from "./invitation-handlers";

afterEach(() => mock.restoreAll());
const status: FspStatus = {
  provider: "MOCK", fsp_id: "MOCK-WINNER", fsp_verified: true,
  fsp_verified_at: "2026-10-08T15:00:00Z", fsp_synced_at: "2026-10-08T15:01:00Z",
  fsp_achievement_score: 80, fsp_bonus: 4, competition_count: 1, best_result_level: "WINNER",
  achievements: [{ competition_name: "Cup", discipline: "Programming", year: 2025, event_date: null, result_level: "WINNER", placement: 1, scope: "TEAM" }],
};

type ProfileProps = Parameters<typeof FspProfileView>[0];
function profileHarness(read: () => Promise<FspStatus>, mutate = async () => status) {
  const values: unknown[] = [], writes: unknown[] = [];
  let index = 0;
  let effect: (() => () => void) | undefined;
  let cleanup: (() => void) | undefined;
  const file = "src/components/fsp-profile.tsx";
  const source = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const declaration = source.statements.find((node): node is ts.FunctionDeclaration => ts.isFunctionDeclaration(node) && node.name?.text === "FspProfile");
  assert.ok(declaration);
  const compiled = ts.transpileModule(declaration.getText(source).replace(/^export /, ""), {
    fileName: file,
    compilerOptions: { target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.React },
  }).outputText;
  const profile = runInNewContext(`${compiled}\nFspProfile`, {
    React: { createElement(_component: unknown, props: ProfileProps) { return props; } },
    FspProfileView, getFspStatus: read, verifyFsp: mutate, refreshFsp: mutate, unlinkFsp: mutate,
    useState(initial: unknown) {
      const slot = index++;
      if (!(slot in values)) values[slot] = initial;
      return [values[slot], (next: unknown) => { writes.push([slot, next]); values[slot] = next; }];
    },
    useRef(initial: unknown) {
      const slot = index++;
      if (!(slot in values)) values[slot] = { current: initial };
      return values[slot];
    },
    useCallback(callback: unknown) { return callback; },
    useEffect(callback: () => () => void) { effect = callback; },
  }) as () => ProfileProps;
  return {
    writes,
    render() { index = 0; return profile(); },
    mount() { cleanup = effect?.(); },
    unmount() { cleanup?.(); cleanup = undefined; },
  };
}

test("FSP initial effect starts loading without synchronous state updates", async () => {
  const read = deferred<FspStatus>();
  const profile = profileHarness(() => read.promise);
  assert.equal(profile.render().loading, true);
  profile.mount();
  assert.deepEqual(profile.writes, []);
  read.resolve(status); await settle();
  assert.equal(profile.render().status, status);
  assert.equal(profile.render().loading, false);
});

test("FSP effect restart ignores the older response without resetting request generation", async () => {
  const reads = [deferred<FspStatus>(), deferred<FspStatus>()];
  let calls = 0;
  const profile = profileHarness(() => reads[calls++].promise);
  profile.render(); profile.mount(); profile.unmount(); profile.mount();
  assert.equal(calls, 2);
  reads[0].resolve({ ...status, fsp_id: "STALE_ID" }); await settle();
  assert.equal(profile.render().status, null);
  assert.equal(profile.render().loading, true);
  reads[1].resolve(status); await settle();
  assert.equal(profile.render().status, status);
  assert.equal(profile.render().loading, false);
});

test("FSP loading failure after unmount cannot update state", async () => {
  const read = deferred<FspStatus>();
  const profile = profileHarness(() => read.promise);
  profile.render(); profile.mount(); profile.unmount();
  read.reject(new ApiError(503, "fsp_provider_unavailable", "Недоступно")); await settle();
  assert.deepEqual(profile.writes, []);
});

test("FSP retry resets loading and error in the event handler then uses server state", async () => {
  const reads = [deferred<FspStatus>(), deferred<FspStatus>()];
  let calls = 0;
  const profile = profileHarness(() => reads[calls++].promise);
  profile.render(); profile.mount();
  const error = new ApiError(503, "fsp_provider_unavailable", "Недоступно");
  reads[0].reject(error); await settle();
  assert.equal(profile.render().error, error);
  assert.equal(profile.render().loading, false);
  profile.render().onRetry();
  assert.equal(calls, 2);
  assert.equal(profile.render().loading, true);
  assert.equal(profile.render().error, null);
  reads[1].resolve(status); await settle();
  assert.equal(profile.render().status, status);
  assert.equal(profile.render().loading, false);
});

test("FSP pending mutation blocks duplicate actions and retry and ignores unmounted callbacks", async () => {
  const mutation = deferred<FspStatus>();
  let reads = 0, mutations = 0;
  const profile = profileHarness(async () => { reads++; return status; }, () => { mutations++; return mutation.promise; });
  profile.render(); profile.mount(); await settle();
  const controls = profile.render();
  controls.onAction("verify"); controls.onAction("verify"); controls.onRetry();
  assert.equal(mutations, 1); assert.equal(reads, 1);
  assert.equal(profile.render().busy, true);
  const beforeUnmount = profile.writes.length;
  profile.unmount(); mutation.resolve(status); await settle();
  assert.equal(profile.writes.length, beforeUnmount);
  controls.onAction("refresh"); controls.onRetry();
  assert.equal(mutations, 1); assert.equal(reads, 1);
});
test("FSP client uses exact endpoints, empty POST payloads and DELETE", async () => {
  const upstream = mock.method(globalThis, "fetch", async () => Response.json(status));
  assert.deepEqual(await getFspStatus(), status);
  await verifyFsp(); await refreshFsp(); await unlinkFsp();
  const calls = upstream.mock.calls.map(call => call.arguments as [string, RequestInit]);
  assert.deepEqual(calls.map(([path, init]) => [path, init.method ?? "GET"]), [
    ["/api/candidate/fsp", "GET"], ["/api/candidate/fsp/verify", "POST"],
    ["/api/candidate/fsp/refresh", "POST"], ["/api/candidate/fsp/verification", "DELETE"],
  ]);
  for (const [, init] of calls.slice(1, 3)) assert.deepEqual(JSON.parse(String(init.body)), {});
});
test("FSP errors preserve safe ApiError", async () => {
  mock.method(globalThis, "fetch", async () => Response.json({error: {code: "fsp_verification_conflict", message: "Недоступно", fields: []}}, {status: 409}));
  await assert.rejects(verifyFsp(), (err: unknown) => err instanceof ApiError && err.code === "fsp_verification_conflict");
});
function view(overrides: Partial<Parameters<typeof FspProfileView>[0]> = {}) {
  return renderToStaticMarkup(createElement(FspProfileView, {status, loading: false, busy: false, error: null, success: "", onRetry() {}, onAction() {}, ...overrides}));
}
test("candidate distinguishes entered ID and provider evidence, shows mock/team and timestamps", () => {
  const html = view();
  assert.match(html, /MOCK.*прототип/);
  assert.match(html, /Подтверждено через ФСП/);
  assert.match(html, /MOCK-WINNER/);
  assert.match(html, /Cup/);
  assert.match(html, /Командный/);
  assert.match(html, /Обновить достижения/);
  assert.match(html, /Снять проверку/);
  assert.match(html, /08\.10\.2026/);
});
test("unverified entered ID renders no fabricated achievements or contacts", () => {
  const html = view({status: {...status, fsp_verified: false, fsp_bonus: 0, achievements: [{...status.achievements[0], competition_name: "PRIVATE_OLD_EVIDENCE"}]}});
  assert.match(html, /не подтверждён/);
  assert.match(html, /Проверить FSP ID/);
  assert.doesNotMatch(html, /PRIVATE_OLD_EVIDENCE|Снять проверку/);
});
test("loading, retry, success and disabled controls", () => {
  assert.match(view({loading: true}), /Загрузка/);
  assert.match(view({error: new ApiError(503, "fsp_provider_unavailable", "Ошибка")}), /Повторить/);
  assert.match(view({busy: true, success: "Готово"}), /disabled/);
  assert.match(view({success: "Готово"}), /Готово/);
});
test("employer explanation shows aggregates only and ignores raw provider/private fields", () => {
  const fabricated = {...status, ranking_score: 88, fsp_id: "PRIVATE_FSP_ID", external_id: "PRIVATE_PROVIDER", email: "PRIVATE_EMAIL"};
  const html = renderToStaticMarkup(createElement(FspExplanation, {signal: fabricated}));
  assert.match(html, /Ranking Score: 88\.0/);
  assert.match(html, /Вклад ФСП: 4\.0 \/ 5/);
  assert.doesNotMatch(html, /PRIVATE/);
});
test("DELETE proxy route is exported for explicit unlink", () => {
  assert.match(readFileSync("src/app/api/[...path]/route.ts", "utf8"), /handler as DELETE/);
});
test("FSP mutation uses server response, rejects double submission and clears busy on failure", async () => {
  const request = deferred<FspStatus>();
  const pending = {current: false}, mounted = {current: true}, generation = {current: 0};
  const states: unknown[] = [], errors: unknown[] = [];
  let calls = 0;
  const invoke = () => { calls++; return request.promise; };
  const act = handler("src/components/fsp-profile.tsx", "FspProfile", "act", {
    pending, mounted, generation, verifyFsp: invoke, refreshFsp: invoke, unlinkFsp: invoke,
    setBusy() {}, setError(err: unknown) {errors.push(err);}, setSuccess() {}, setStatus(value: unknown) {states.push(value);},
  }) as (action: string) => Promise<void>;
  const first = act("verify"); await act("verify");
  assert.equal(calls, 1); assert.deepEqual(states, []);
  request.resolve(status); await first;
  assert.equal(states[0], status); assert.equal(pending.current, false);
  const failure = deferred<FspStatus>();
  const failedAct = handler("src/components/fsp-profile.tsx", "FspProfile", "act", {
    pending, mounted, generation, verifyFsp: () => failure.promise, refreshFsp() {}, unlinkFsp() {},
    setBusy() {}, setError(err: unknown) {errors.push(err);}, setSuccess() {}, setStatus() {assert.fail("failed mutation must not set status");},
  }) as (action: string) => Promise<void>;
  const attempt = failedAct("verify");
  const error = new ApiError(503, "fsp_provider_unavailable", "Недоступно");
  failure.reject(error); await attempt;
  assert.equal(errors.at(-1), error); assert.equal(pending.current, false);
});
test("invitation salary renders authoritative strings with RUB gross labeling", async () => {
  const {CandidateInvitationCard} = await import("../src/components/candidate-invitations-screen");
  const html = renderToStaticMarkup(createElement(CandidateInvitationCard, {
    invitation: {id: "i", need_id: "n", status: "SENT", message: null, sent_at: "2026-10-08T15:00:00Z", viewed_at: null, responded_at: null, withdrawn_at: null,
      need_snapshot: {need_id: "n", company_name: "Company", position_title: "Role", specialization: "BACKEND", required_grade: "MIDDLE", target_experience_years: null,
        salary_from: "180000.01", salary_to: "230000.99", description: "", additional_requirements: null, must_have_skills: [], nice_to_have_skills: []}},
    busy: false, expanded: false, onAction() {}, onOpen() {},
  }));
  assert.match(html, /180000\.01–230000\.99/);
  assert.match(html, /RUB, до вычета налогов/);
});
