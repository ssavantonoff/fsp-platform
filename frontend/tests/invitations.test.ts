import assert from "node:assert/strict";
import { test } from "node:test";
import { ApiError } from "../src/api";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { CandidateInvitation, EmployerInvitation, InvitationStatus } from "../src/invitations";
import { deferred, handler, pageHarness, settle } from "./invitation-handlers";

const snapshot = {
  need_id: "need", position_title: "Backend", specialization: "BACKEND", required_grade: "MIDDLE",
  target_experience_years: 3, salary_from: "180000.00", salary_to: "230000.00", description: "Описание",
  additional_requirements: null, must_have_skills: [{ id: "python", name: "Python" }], nice_to_have_skills: [], company_name: "Компания",
} satisfies CandidateInvitation["need_snapshot"];
const candidateSnapshot = {
  candidate_id: "candidate", display_name: "Мария С.", specialization: "BACKEND", verified_grade: "MIDDLE",
  normalized_assessment_score: 90, assessment_verified_at: null, professional_fit_score: 88,
  breakdown: { assessment: { score: 40, max: 45, active: true }, grade: { score: 25, max: 25, active: true, exact_match: true },
    nice_to_have: { score: 0, max: 0, active: false, matched: 0, total: 0 }, experience: { score: 10, max: 15, active: true } },
} satisfies EmployerInvitation["candidate_snapshot"];
function invitation(status: InvitationStatus = "SENT"): CandidateInvitation {
  return { id: "invitation", need_id: "need", status, message: "<script>alert('message')</script>", need_snapshot: snapshot,
    sent_at: "2026-10-07T23:59:00Z", viewed_at: null, responded_at: null, withdrawn_at: null };
}
const contacts = {
  candidate_contact: { first_name: "Мария", last_name: "PRIVATE_FULL_SURNAME", email: "PRIVATE_CANDIDATE_EMAIL", fsp_id: "PRIVATE_FSP", about: "PRIVATE_ABOUT" },
  employer_contact: { company_name: "Компания", contact_person_name: "PRIVATE_EMPLOYER_CONTACT", email: "PRIVATE_EMPLOYER_EMAIL", website: "PRIVATE_WEBSITE", user_id: "PRIVATE_USER_ID" },
};
test("employer invitation cards use snapshots, five statuses and accepted-only contact allowlist", async () => {
  const { EmployerInvitationCard } = await import("../src/components/employer-invitations-screen");
  for (const status of ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"] as const) {
    const item = { ...invitation(status), candidate_snapshot: { ...candidateSnapshot, email: "PRIVATE_OTHER_EMAIL", about: "PRIVATE_ABOUT" }, ...contacts };
    const html = renderToStaticMarkup(createElement(EmployerInvitationCard, { invitation: item, busy: false, onWithdraw: () => {} }));
    assert.match(html, /Мария С\.|Мария/);
    assert.match(html, /180000\.00–230000\.00/);
    assert.match(html, /07\.10\.2026/);
    assert.match(html, /88\.0/);
    assert.equal(html.includes("Отозвать приглашение"), status === "SENT" || status === "VIEWED");
    assert.equal(html.includes("PRIVATE_CANDIDATE_EMAIL"), status === "ACCEPTED");
    assert.equal(html.includes("PRIVATE_FULL_SURNAME"), status === "ACCEPTED");
    assert.doesNotMatch(html, /PRIVATE_FSP|PRIVATE_ABOUT|PRIVATE_USER_ID|PRIVATE_OTHER_EMAIL|PRIVATE_EMPLOYER/);
  }
});
test("invitation list renders loading, empty, error/retry and page boundaries", async () => {
  const { InvitationListState, InvitationPagination } = await import("../src/components/invitation-page");
  for (const [props, expected] of [
    [{ loading: true, empty: false, error: null }, /Загрузка приглашений/],
    [{ loading: false, empty: true, error: null }, /Приглашений пока нет/],
    [{ loading: false, empty: false, error: new Error("Недоступен") }, /Недоступен[\s\S]*Повторить/],
  ] as const) assert.match(renderToStaticMarkup(createElement(InvitationListState, { ...props, onRetry: () => {} })), expected);
  for (const [offset, total, previous, next] of [[0, 21, true, false], [20, 21, false, true]] as const) {
    const html = renderToStaticMarkup(createElement(InvitationPagination, { page: { items: [invitation()], total, offset, limit: 20 }, loading: false, busy: false, onPageChange: () => {} }));
    assert.equal(/<button[^>]*disabled=""[^>]*>Назад/.test(html), previous);
    assert.equal(/<button[^>]*disabled=""[^>]*>Далее/.test(html), next);
  }
});
test("invitation page ignores stale GET and unmount results", async () => {
  const first = deferred<{ items: CandidateInvitation[]; total: number; limit: number; offset: number }>();
  let reads = 0;
  const fresh = { items: [invitation("VIEWED")], total: 1, offset: 0, limit: 20 };
  const harness = pageHarness(() => ++reads === 1 ? first.promise : Promise.resolve(fresh));
  let state = harness.render(); harness.mount(); state.retry(); await settle();
  assert.equal(harness.render().page?.items[0].status, "VIEWED");
  first.resolve({ ...fresh, items: [invitation("SENT")] }); await settle();
  assert.equal(harness.render().page?.items[0].status, "VIEWED");
  state = harness.render(); const operation = deferred<CandidateInvitation>();
  const pending = state.mutate("invitation", () => operation.promise, "accepted");
  harness.unmount(); operation.resolve(invitation("ACCEPTED"));
  assert.equal(await pending, false);
  assert.equal(harness.render().page?.items[0].status, "VIEWED");
});
test("mutations use server response, prevent double clicks and refresh state conflict", async () => {
  let reads = 0;
  const harness = pageHarness(async () => ({ items: [invitation(++reads === 1 ? "SENT" : "WITHDRAWN")], total: 1, offset: 0, limit: 20 }));
  let state = harness.render(); harness.mount(); await settle(); state = harness.render();
  const operation = deferred<CandidateInvitation>();
  const pending = state.mutate("invitation", () => operation.promise, "Приглашение принято");
  assert.equal(harness.render().page?.items[0].status, "SENT");
  assert.equal(await state.mutate("invitation", async () => { throw new Error("double click submitted"); }, "duplicate"), false);
  operation.resolve(invitation("ACCEPTED")); assert.equal(await pending, true);
  assert.equal(harness.render().page?.items[0].status, "ACCEPTED");
  assert.equal(harness.render().success, "Приглашение принято");
  state = harness.render();
  const conflict = new ApiError(409, "invitation_state_conflict", "Работодатель отозвал приглашение");
  assert.equal(await state.mutate("invitation", async () => { throw conflict; }, "incorrect success"), false);
  const final = harness.render();
  assert.equal(reads, 2); assert.equal(final.page?.items[0].status, "WITHDRAWN");
  assert.equal(final.actionError, conflict); assert.equal(final.success, ""); assert.equal(final.busyId, null);
});
test("failed list retries, mutation errors stay visible and pagination requests server offset", async () => {
  let fail = true; const offsets: number[] = [];
  const harness = pageHarness(async (offset) => {
    offsets.push(offset); if (fail) throw new Error("Network unavailable");
    return { items: [invitation()], total: 30, offset, limit: 20 };
  });
  let state = harness.render(); harness.mount(); await settle(); assert.equal(harness.render().page, null);
  fail = false; state.retry(); await settle(); state = harness.render(); assert.equal(state.page?.total, 30);
  const error = new ApiError(403, "forbidden", "Ошибка");
  await state.mutate("invitation", async () => { throw error; }, "success"); assert.equal(harness.render().actionError, error);
  state.changePage(20); state = harness.render(); harness.mount(); await settle();
  assert.equal(harness.render().page?.offset, 20); assert.deepEqual(offsets, [0, 0, 20]);
});
test("explicit Open is the only VIEW action, while direct ACCEPT/DECLINE work from SENT", async () => {
  const actions: string[] = []; const expanded: string[] = [];
  const scope = {
    state: { mutate: async (_id: string, operation: () => Promise<unknown>) => { await operation(); return true; } },
    toggle: (id: string) => expanded.push(id),
    viewInvitation: async (id: string) => { actions.push(`view:${id}`); },
    acceptInvitation: async (id: string) => { actions.push(`accept:${id}`); },
    declineInvitation: async (id: string) => { actions.push(`decline:${id}`); },
  };
  const open = handler("src/components/candidate-invitations-screen.tsx", "CandidateInvitationsContent", "open", scope);
  const respond = handler("src/components/candidate-invitations-screen.tsx", "CandidateInvitationsContent", "respond", scope);
  assert.deepEqual(actions, []);
  respond("direct", "accept"); respond("decline", "decline"); await settle();
  assert.deepEqual(actions, ["accept:direct", "decline:decline"]);
  await open(invitation()); await open(invitation("VIEWED"));
  assert.deepEqual(actions, ["accept:direct", "decline:decline", "view:invitation"]);
  assert.deepEqual(expanded, ["invitation", "invitation"]);
});
test("withdraw confirmation cancellation never sends a request", () => {
  let sends = 0; let confirmed = false;
  const withdraw = handler("src/components/employer-invitations-screen.tsx", "EmployerInvitationsContent", "withdraw", {
    window: { confirm: () => confirmed }, state: { mutate: () => { sends++; } }, withdrawInvitation: () => {},
  });
  withdraw("id"); assert.equal(sends, 0); confirmed = true; withdraw("id"); assert.equal(sends, 1);
});
test("candidate cards expose explicit actions and never render stored contacts before acceptance", async () => {
  const { CandidateInvitationCard } = await import("../src/components/candidate-invitations-screen");
  for (const status of ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"] as const) {
    const item = { ...invitation(status), ...contacts, need_snapshot: { ...snapshot, contact_person_name: "PRIVATE_STORED_CONTACT", website: "PRIVATE_STORED_WEBSITE" } };
    const html = renderToStaticMarkup(createElement(CandidateInvitationCard, { invitation: item, busy: false, expanded: true, onAction: () => {}, onOpen: () => {} }));
    assert.equal(html.includes("Принять"), status === "SENT" || status === "VIEWED");
    assert.equal(html.includes("Отклонить"), status === "SENT" || status === "VIEWED");
    assert.equal(html.includes("PRIVATE_EMPLOYER_EMAIL"), status === "ACCEPTED");
    assert.equal(html.includes("PRIVATE_EMPLOYER_CONTACT"), status === "ACCEPTED");
    assert.equal(html.includes("PRIVATE_WEBSITE"), status === "ACCEPTED");
    assert.doesNotMatch(html, /PRIVATE_STORED_|PRIVATE_CANDIDATE|PRIVATE_FULL|PRIVATE_FSP|PRIVATE_ABOUT|PRIVATE_USER_ID|<script>/);
    assert.match(html, /&lt;script&gt;/);
  }
});

test("invitation client sends only candidate_id/message and uses all nine encoded endpoints", async () => {
  const client = await import("../src/invitations");
  const original = globalThis.fetch;
  const calls: { url: string; method: string; body: unknown }[] = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), method: init?.method ?? "GET", body: init?.body ? JSON.parse(String(init.body)) : null });
    assert.equal(init?.credentials, "same-origin");
    return Response.json({ id: "saved" });
  };
  try {
    const injected = { candidate_id: "candidate", message: "  Plain <b>text</b>  ", employer_id: "foreign", status: "ACCEPTED", need_snapshot: {} };
    await client.sendInvitation("need/a b", injected);
    await client.listEmployerInvitations("need/a b", 20, 40);
    await client.getEmployerInvitation("id/a b");
    await client.withdrawInvitation("id/a b");
    await client.listCandidateInvitations();
    await client.getCandidateInvitation("id/a b");
    await client.viewInvitation("id/a b");
    await client.acceptInvitation("id/a b");
    await client.declineInvitation("id/a b");
    assert.deepEqual(calls, [
      { url: "/api/employer/needs/need%2Fa%20b/invitations", method: "POST", body: { candidate_id: "candidate", message: injected.message } },
      { url: "/api/employer/needs/need%2Fa%20b/invitations?limit=20&offset=40", method: "GET", body: null },
      { url: "/api/employer/invitations/id%2Fa%20b", method: "GET", body: null },
      { url: "/api/employer/invitations/id%2Fa%20b/withdraw", method: "POST", body: null },
      { url: "/api/candidate/invitations?limit=20&offset=0", method: "GET", body: null },
      ...["", "/view", "/accept", "/decline"].map((suffix) => ({ url: `/api/candidate/invitations/id%2Fa%20b${suffix}`, method: suffix ? "POST" : "GET", body: null })),
    ]);
    globalThis.fetch = async () => Response.json({ error: { code: "invitation_state_conflict", message: "Состояние изменилось", fields: [] } }, { status: 409 });
    await assert.rejects(client.acceptInvitation("id"), (error: unknown) => error instanceof ApiError && error.code === "invitation_state_conflict" && error.status === 409);
  } finally { globalThis.fetch = original; }
});
