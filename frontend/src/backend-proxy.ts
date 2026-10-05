export async function proxy(
  request: Request,
  segments: string[],
): Promise<Response> {
  const base = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const path = segments.map(encodeURIComponent).join("/");
  const headers = new Headers();
  for (const name of ["content-type", "cookie", "origin"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const response = await fetch(
      `${base}/${path}${new URL(request.url).search}`,
      {
        method: request.method,
        headers,
        body: request.method === "GET" ? undefined : await request.text(),
        cache: "no-store",
        redirect: "manual",
        signal: AbortSignal.timeout(15000),
      },
    );
    const forwarded = new Headers({ "Cache-Control": "no-store" });
    const contentType = response.headers.get("content-type");
    if (contentType) forwarded.set("content-type", contentType);
    for (const cookie of response.headers.getSetCookie())
      forwarded.append("set-cookie", cookie);
    return new Response(
      response.status === 204 ? null : await response.text(),
      {
        status: response.status,
        headers: forwarded,
      },
    );
  } catch {
    return Response.json(
      {
        error: {
          code: "backend_unavailable",
          message: "Сервер недоступен. Попробуйте позже.",
          fields: [],
        },
      },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
