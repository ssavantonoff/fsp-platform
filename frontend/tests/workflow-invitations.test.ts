import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CandidateInvitationCard } from "../src/components/candidate-invitations-screen";
import { EmployerInvitationCard } from "../src/components/employer-invitations-screen";
import { InvitationListState, InvitationPagination } from "../src/components/invitation-page";
import { invitationStatusLabels } from "../src/invitations";
import type { CandidateInvitation, EmployerInvitation, InvitationStatus } from "../src/invitations";

const candidateInvitation: CandidateInvitation = {
  id: "invitation", need_id: "need", status: "SENT", message: "Сообщение работодателя",
  need_snapshot: {
    need_id: "need", company_name: "Компания", position_title: "Backend Engineer",
    specialization: "BACKEND", required_grade: "MIDDLE", target_experience_years: 3,
    salary_from: "180000.00", salary_to: "230000.00", description: "Описание позиции",
    additional_requirements: "Дополнительные условия", must_have_skills: [{ id: "python", name: "Python" }],
    nice_to_have_skills: [{ id: "django", name: "Django" }],
  },
  sent_at: "2026-10-07T23:59:00Z", viewed_at: null, responded_at: null, withdrawn_at: null,
};
const employerInvitation: EmployerInvitation = {
  ...candidateInvitation,
  candidate_snapshot: {
    candidate_id: "candidate", display_name: "Мария С.", specialization: "BACKEND", verified_grade: "MIDDLE",
    normalized_assessment_score: 90, assessment_verified_at: null, professional_fit_score: 88,
    ranking_score: 86.1, fsp_verified: true, fsp_achievement_score: 50, fsp_bonus: 2.5,
    competition_count: 2, best_result_level: "FINALIST",
    breakdown: {
      assessment: { score: 40, max: 45, active: true }, grade: { score: 25, max: 25, active: true, exact_match: true },
      nice_to_have: { score: 0, max: 0, active: false, matched: 0, total: 0 }, experience: { score: 10, max: 15, active: true },
    },
  },
};
const noop = () => {};
function candidateHtml(invitation: CandidateInvitation = candidateInvitation, expanded = false, busy = false) {
  return renderToStaticMarkup(createElement(CandidateInvitationCard, { invitation, expanded, busy, onOpen: noop, onAction: noop }));
}
function employerHtml(invitation: EmployerInvitation = employerInvitation, busy = false) {
  return renderToStaticMarkup(createElement(EmployerInvitationCard, { invitation, busy, onWithdraw: noop }));
}

test("compact employer card keeps candidate, offer and available withdrawal outside secondary details", () => {
  const html = employerHtml();
  const [summary, details] = html.split('<details class="workflow-details">');
  assert.match(summary, /<h2>Мария С\.<\/h2>/);
  assert.match(summary, /invitation-position[^>]*>Backend Engineer/);
  assert.match(summary, /180000\.00–230000\.00/);
  assert.match(summary, /07\.10\.2026/);
  assert.match(summary, /Отозвать приглашение/);
  assert.doesNotMatch(summary, /Соответствие при отправке|Сообщение работодателя|Ranking Score/);
  assert.match(details, /<summary>Детали приглашения<\/summary>/);
  assert.match(details, /Соответствие при отправке[\s\S]*88\.0 \/ 100/);
  assert.match(details, /Ranking Score: 86\.1 \/ 100/);
  assert.match(details, /Участий: 2[\s\S]*Финалист/);
  assert.match(details, /Достижения: 50\.0 \/ 100 · Вклад ФСП: 2\.5 \/ 5/);
  assert.match(details, /Сообщение работодателя/);
});

test("candidate offer and response actions remain visible before explicit opening", () => {
  const compact = candidateHtml();
  assert.match(compact, /<h2>Компания<\/h2>/);
  assert.match(compact, /Backend Engineer/);
  assert.match(compact, /180000\.00–230000\.00/);
  assert.match(compact, /07\.10\.2026/);
  assert.match(compact, /aria-expanded="false" aria-controls="invitation-details-invitation"[^>]*>Открыть/);
  assert.match(compact, />Принять<\/button>/);
  assert.match(compact, />Отклонить<\/button>/);
  assert.doesNotMatch(compact, /Описание позиции|Дополнительные условия|Сообщение работодателя/);
  const expanded = candidateHtml(candidateInvitation, true);
  assert.match(expanded, /aria-expanded="true"[\s\S]*Скрыть подробности/);
  assert.match(expanded, /id="invitation-details-invitation" aria-label="Детали приглашения"/);
  for (const text of ["Описание позиции", "Дополнительные условия", "Сообщение работодателя", "Python", "Django", "Целевой опыт, лет"])
    assert.ok(expanded.includes(text), text);
});

test("five Russian statuses retain lifecycle actions and accepted-only contacts when collapsed or expanded", () => {
  const candidateContact = { first_name: "Мария", last_name: "PRIVATE_SURNAME", email: "PRIVATE_CANDIDATE_EMAIL", fsp_id: "PRIVATE_FSP" };
  const employerContact = { company_name: "Компания", contact_person_name: "PRIVATE_CONTACT_PERSON", email: "PRIVATE_EMPLOYER_EMAIL", website: "PRIVATE_WEBSITE", user_id: "PRIVATE_USER" };
  const statuses: InvitationStatus[] = ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"];
  for (const status of statuses) {
    const employer = employerHtml({ ...employerInvitation, status, candidate_contact: candidateContact });
    assert.ok(employer.includes(`data-status="${status}">${invitationStatusLabels[status]}`));
    assert.equal(employer.includes("Отозвать приглашение"), status === "SENT" || status === "VIEWED");
    assert.equal(employer.includes("PRIVATE_CANDIDATE_EMAIL"), status === "ACCEPTED");
    assert.equal(employer.includes("PRIVATE_SURNAME"), status === "ACCEPTED");
    assert.doesNotMatch(employer, /PRIVATE_FSP/);
    for (const expanded of [false, true]) {
      const candidate = candidateHtml({ ...candidateInvitation, status, employer_contact: employerContact }, expanded);
      assert.ok(candidate.includes(`data-status="${status}">${invitationStatusLabels[status]}`));
      assert.equal(candidate.includes(">Принять</button>"), status === "SENT" || status === "VIEWED");
      assert.equal(candidate.includes(">Отклонить</button>"), status === "SENT" || status === "VIEWED");
      for (const contact of ["PRIVATE_CONTACT_PERSON", "PRIVATE_EMPLOYER_EMAIL", "PRIVATE_WEBSITE"])
        assert.equal(candidate.includes(contact), status === "ACCEPTED", `${status}: ${contact}`);
      assert.doesNotMatch(candidate, /PRIVATE_USER/);
    }
  }
});

test("accepted contact sections remain outside disclosures even when details are collapsed", () => {
  const employer = employerHtml({ ...employerInvitation, status: "ACCEPTED", candidate_contact: { first_name: "Мария", last_name: "Смирнова", email: "candidate@example.com" } });
  assert.match(employer, /<\/details><section class="invitation-contacts" aria-label="Контакт кандидата">/);
  assert.match(employer, /candidate@example\.com/);
  const candidate = candidateHtml({ ...candidateInvitation, status: "ACCEPTED", employer_contact: { company_name: "Компания", contact_person_name: "Анна", email: "employer@example.com", website: null } });
  assert.match(candidate, /aria-expanded="false"/);
  assert.match(candidate, /invitation-contacts[^>]*aria-label="Контакт работодателя"/);
  assert.match(candidate, /employer@example\.com/);
  assert.match(candidate, /Не указан/);
});

test("busy state disables opening and all permitted response or withdrawal actions", () => {
  const candidateButtons = candidateHtml(candidateInvitation, false, true).match(/<button[^>]*>/g) ?? [];
  assert.equal(candidateButtons.length, 3);
  assert.ok(candidateButtons.every((button) => button.includes('disabled=""')));
  assert.match(employerHtml(employerInvitation, true), /<button[^>]*disabled=""[^>]*>Отзываем…<\/button>/);
});

test("disclosures escape long user text instead of rendering markup", () => {
  const payload = "<script>alert('unsafe')</script>";
  const invitation = { ...candidateInvitation, message: payload, need_snapshot: { ...candidateInvitation.need_snapshot, company_name: payload, position_title: payload, description: payload, additional_requirements: payload } };
  const candidate = candidateHtml(invitation, true);
  assert.doesNotMatch(candidate, /<script>/);
  assert.equal(candidate.match(/&lt;script&gt;/g)?.length, 5);
  const employer = employerHtml({ ...employerInvitation, message: payload, candidate_snapshot: { ...employerInvitation.candidate_snapshot, display_name: payload } });
  assert.doesNotMatch(employer, /<script>/);
  assert.equal(employer.match(/&lt;script&gt;/g)?.length, 2);
});

test("invitation state panels and pagination keep accessible loading, retry and busy feedback", () => {
  const loading = renderToStaticMarkup(createElement(InvitationListState, { loading: true, error: new Error("Should not display"), empty: true, onRetry: noop }));
  assert.match(loading, /workflow-list-state/);
  assert.match(loading, /role="status">Загрузка приглашений/);
  assert.doesNotMatch(loading, /Should not display|Приглашений пока нет|Повторить/);
  const error = renderToStaticMarkup(createElement(InvitationListState, { loading: false, error: new Error("Недоступно"), empty: false, onRetry: noop }));
  assert.match(error, /Недоступно[\s\S]*Повторить/);
  const empty = renderToStaticMarkup(createElement(InvitationListState, { loading: false, error: null, empty: true, onRetry: noop }));
  assert.match(empty, /Приглашений пока нет/);
  const pagination = renderToStaticMarkup(createElement(InvitationPagination, { page: { items: [candidateInvitation], total: 50, offset: 20, limit: 20 }, loading: false, busy: true, onPageChange: noop }));
  assert.match(pagination, /aria-label="Страницы приглашений"/);
  assert.equal(pagination.match(/disabled=""/g)?.length, 2);
});
