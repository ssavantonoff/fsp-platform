"use client";

import Link from "next/link";
import { useCallback } from "react";
import { invitationDate, invitationStatusLabels, listEmployerInvitations, withdrawInvitation } from "@/invitations";
import type { EmployerInvitation } from "@/invitations";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";
import { FspExplanation } from "./fsp-profile";
import { formatScore } from "./employer-matches-screen";
import { InvitationListState, InvitationPagination, useInvitationPage } from "./invitation-page";

export function EmployerInvitationCard({ invitation, busy, onWithdraw }: {
  invitation: EmployerInvitation; busy: boolean; onWithdraw: () => void;
}) {
  const need = invitation.need_snapshot;
  const candidate = invitation.candidate_snapshot;
  const contact = invitation.status === "ACCEPTED" ? invitation.candidate_contact : null;
  return <article className="card invitation-card workflow-invitation">
    <div className="need-card-header"><h2>{candidate.display_name}</h2><span className="need-status workflow-status" data-status={invitation.status}>{invitationStatusLabels[invitation.status]}</span></div>
    <h3 className="invitation-position">{need.position_title}</h3>
    <dl className="workflow-facts">
      <dt>Отправлено (UTC)</dt><dd>{invitationDate(invitation.sent_at)}</dd>
      <dt>Зарплата при отправке</dt><dd>{need.salary_from}–{need.salary_to} ₽ (RUB, до вычета налогов)</dd>
    </dl>
    {(invitation.status === "SENT" || invitation.status === "VIEWED") && <div className="actions"><button className="secondary" disabled={busy} onClick={onWithdraw}>{busy ? "Отзываем…" : "Отозвать приглашение"}</button></div>}
    <details className="workflow-details">
      <summary>Детали приглашения</summary>
      <dl className="workflow-facts"><dt>Соответствие при отправке</dt><dd>{formatScore(candidate.professional_fit_score)} / 100</dd></dl>
      <FspExplanation signal={candidate} />
      {invitation.message && <p className="invitation-message workflow-copy">{invitation.message}</p>}
    </details>
    {contact && <section className="invitation-contacts" aria-label="Контакт кандидата"><h3>Контакт кандидата</h3><dl className="workflow-facts">
      <dt>Имя</dt><dd>{contact.first_name} {contact.last_name}</dd>
      <dt>Email</dt><dd>{contact.email}</dd>
    </dl></section>}
  </article>;
}
export function EmployerInvitationsScreen({ needId }: { needId: string }) {
  return <RoleGate role="EMPLOYER"><EmployerInvitationsContent key={needId} needId={needId} /></RoleGate>;
}
function EmployerInvitationsContent({ needId }: { needId: string }) {
  const fetchPage = useCallback((offset: number) => listEmployerInvitations(needId, 20, offset), [needId]);
  const state = useInvitationPage(fetchPage);
  function withdraw(id: string) {
    if (!window.confirm("Отозвать приглашение? Кандидат больше не сможет его принять.")) return;
    void state.mutate(id, () => withdrawInvitation(id), "Приглашение отозвано");
  }
  return <section className="need-list workflow-screen">
    <section className="card workflow-heading"><h1>Приглашения по потребности</h1><div className="actions"><Link className="button secondary" href="/employer/needs">К списку потребностей</Link><button className="secondary" disabled={state.loading || state.busyId !== null} onClick={state.retry}>Обновить</button></div></section>
    <Feedback error={state.actionError} success={state.success} />
    <InvitationListState loading={state.loading} error={state.error} empty={state.page?.total === 0} onRetry={state.retry} />
    {!state.loading && state.error == null && state.page?.items.map((item) => <EmployerInvitationCard key={item.id} invitation={item} busy={state.busyId !== null} onWithdraw={() => withdraw(item.id)} />)}
    <InvitationPagination page={state.page} loading={state.loading} busy={state.busyId !== null} onPageChange={state.changePage} />
  </section>;
}
