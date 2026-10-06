import { EmployerNeedEditor } from "@/components/employer-needs-screen";
export default async function EditEmployerNeed({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <EmployerNeedEditor key={id} needId={id} />;
}
