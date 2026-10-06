import { EmployerMatchesScreen } from "@/components/employer-matches-screen";

export default async function EmployerNeedMatchesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <EmployerMatchesScreen key={id} needId={id} />;
}
