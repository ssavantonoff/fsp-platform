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
  return <article className="card invitation-card">
    <div className="need-card-header"><h2>{candidate.display_name}</h2><span className="need-status">{invitationStatusLabels[invitation.status]}</span></div>
    <dl>
      <dt>Позиция</dt><dd>{need.position_title}</dd>
      <dt>Отправлено (UTC)</dt><dd>{invitationDate(invitation.sent_at)}</dd>
      <dt>Зарплата при отправке</dt><dd>{need.salary_from}–{need.salary_to} ₽ (RUB, до вычета налогов)</dd>
      <dt>Соответствие при отправке</dt><dd>{formatScore(candidate.professional_fit_score)} / 100</dd>
    </dl>
    <FspExplanation signal={candidate} />
    {invitation.message && <p className="invitation-message">{invitation.message}</p>}
    {contact && <section aria-label="Контакт кандидата"><h3>Контакт кандидата</h3><p>{contact.first_name} {contact.last_name}</p><p>{contact.email}</p></section>}
    {(invitation.status === "SENT" || invitation.status === "VIEWED") && <button className="secondary" disabled={busy} onClick={onWithdraw}>{busy ? "Отзываем…" : "Отозвать приглашение"}</button>}
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
  return <section className="need-list">
    <section className="card invitation-card"><h1>Приглашения по потребности</h1><div className="actions"><Link href="/employer/needs">К списку потребностей</Link><button className="secondary" disabled={state.loading || state.busyId !== null} onClick={state.retry}>Обновить</button></div></section>
    <Feedback error={state.actionError} success={state.success} />
    <InvitationListState loading={state.loading} error={state.error} empty={state.page?.total === 0} onRetry={state.retry} />
    {!state.loading && state.error == null && state.page?.items.map((item) => <EmployerInvitationCard key={item.id} invitation={item} busy={state.busyId !== null} onWithdraw={() => withdraw(item.id)} />)}
    <InvitationPagination page={state.page} loading={state.loading} busy={state.busyId !== null} onPageChange={state.changePage} />
  </section>;
}
