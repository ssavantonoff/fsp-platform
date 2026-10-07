import { EmployerInvitationsScreen } from "@/components/employer-invitations-screen";

export default async function EmployerNeedInvitationsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <EmployerInvitationsScreen key={id} needId={id} />;
}
