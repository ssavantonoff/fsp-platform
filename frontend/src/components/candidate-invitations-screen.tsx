"use client";

import { useCallback, useState } from "react";
import { acceptInvitation, declineInvitation, invitationDate, invitationStatusLabels, listCandidateInvitations, viewInvitation } from "@/invitations";
import type { CandidateInvitation } from "@/invitations";
import { gradeLabels, specializationLabels } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";
import { InvitationListState, InvitationPagination, useInvitationPage } from "./invitation-page";

export function CandidateInvitationCard({ invitation, busy, expanded, onAction, onOpen }: {
  invitation: CandidateInvitation; busy: boolean; expanded: boolean;
  onAction: (action: "accept" | "decline") => void; onOpen: () => void;
}) {
  const need = invitation.need_snapshot;
  const contact = invitation.status === "ACCEPTED" ? invitation.employer_contact : null;
  const canRespond = invitation.status === "SENT" || invitation.status === "VIEWED";
  return <article className="card invitation-card workflow-invitation">
    <div className="need-card-header"><h2>{need.company_name}</h2><span className="need-status workflow-status" data-status={invitation.status}>{invitationStatusLabels[invitation.status]}</span></div>
    <h3 className="invitation-position">{need.position_title}</h3>
    <dl className="workflow-facts">
      <dt>Специализация</dt><dd>{specializationLabels[need.specialization]}</dd>
      <dt>Требуемый уровень</dt><dd>{gradeLabels[need.required_grade]}</dd>
      <dt>Зарплата</dt><dd>{need.salary_from}–{need.salary_to} ₽ (RUB, до вычета налогов)</dd>
      <dt>Отправлено (UTC)</dt><dd>{invitationDate(invitation.sent_at)}</dd>
    </dl>
    <div className="actions">
      <button className="secondary" disabled={busy} aria-expanded={expanded} aria-controls={expanded ? `invitation-details-${invitation.id}` : undefined} onClick={onOpen}>{expanded ? "Скрыть подробности" : "Открыть"}</button>
      {canRespond && <><button disabled={busy} onClick={() => onAction("accept")}>Принять</button><button className="secondary" disabled={busy} onClick={() => onAction("decline")}>Отклонить</button></>}
    </div>
    {expanded && <section className="workflow-details" id={`invitation-details-${invitation.id}`} aria-label="Детали приглашения">
      {invitation.message && <p className="invitation-message workflow-copy">{invitation.message}</p>}
      <dl className="workflow-facts">
      <dt>Описание</dt><dd className="workflow-copy">{need.description}</dd>
      <dt>Дополнительные требования</dt><dd className="workflow-copy">{need.additional_requirements || "—"}</dd>
      <dt>Обязательные навыки</dt><dd>{need.must_have_skills.map((skill) => skill.name).join(", ") || "—"}</dd>
      <dt>Желательные навыки</dt><dd>{need.nice_to_have_skills.map((skill) => skill.name).join(", ") || "—"}</dd>
      <dt>Целевой опыт, лет</dt><dd>{need.target_experience_years ?? "Не учитывается"}</dd>
      </dl>
    </section>}
    {invitation.status === "DECLINED" && <p>Приглашение отклонено</p>}
    {invitation.status === "WITHDRAWN" && <p>Работодатель отозвал приглашение</p>}
    {contact && <section className="invitation-contacts" aria-label="Контакт работодателя"><h3>Контакт работодателя</h3><dl className="workflow-facts">
      <dt>Компания</dt><dd>{contact.company_name}</dd>
      <dt>Контактное лицо</dt><dd>{contact.contact_person_name}</dd>
      <dt>Email</dt><dd>{contact.email}</dd>
      <dt>Сайт</dt><dd>{contact.website || "Не указан"}</dd>
    </dl></section>}
  </article>;
}
export function CandidateInvitationsScreen() {
  return <RoleGate role="CANDIDATE"><CandidateInvitationsContent /></RoleGate>;
}
function CandidateInvitationsContent() {
  const fetchPage = useCallback((offset: number) => listCandidateInvitations(20, offset), []);
  const state = useInvitationPage(fetchPage);
  const [expandedIds, setExpandedIds] = useState<string[]>([]);
  function toggle(id: string) { setExpandedIds((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]); }
  async function open(item: CandidateInvitation) {
    if (item.status === "SENT") {
      if (await state.mutate(item.id, () => viewInvitation(item.id), "Приглашение просмотрено")) toggle(item.id);
    } else toggle(item.id);
  }
  function respond(id: string, action: "accept" | "decline") {
    void state.mutate(id, () => action === "accept" ? acceptInvitation(id) : declineInvitation(id), action === "accept" ? "Приглашение принято" : "Приглашение отклонено");
  }
  return <section className="need-list workflow-screen">
    <section className="card workflow-heading"><h1>Приглашения от работодателей</h1><div className="actions"><button className="secondary" disabled={state.loading || state.busyId !== null} onClick={state.retry}>Обновить</button></div></section>
    <Feedback error={state.actionError} success={state.success} />
    <InvitationListState loading={state.loading} error={state.error} empty={state.page?.total === 0} onRetry={state.retry} />
    {!state.loading && state.error == null && state.page?.items.map((item) => <CandidateInvitationCard key={item.id} invitation={item} busy={state.busyId !== null} expanded={expandedIds.includes(item.id)} onOpen={() => void open(item)} onAction={(action) => respond(item.id, action)} />)}
    <InvitationPagination page={state.page} loading={state.loading} busy={state.busyId !== null} onPageChange={state.changePage} />
  </section>;
}
