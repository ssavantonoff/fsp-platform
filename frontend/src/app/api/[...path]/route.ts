import { proxy } from "@/backend-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function handler(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxy(request, (await context.params).path);
}
export { handler as GET, handler as POST, handler as PUT };
