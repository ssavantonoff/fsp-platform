import { AssessmentAttemptScreen } from "@/components/assessment-attempt";
export default async function Page({
  params,
}: {
  params: Promise<{ attemptId: string }>;
}) {
  const { attemptId } = await params;
  return <AssessmentAttemptScreen key={attemptId} id={attemptId} />;
}
