import assert from "node:assert/strict";
import { afterEach, mock, test } from "node:test";
import { proxy } from "../src/backend-proxy";

afterEach(() => mock.restoreAll());

test("login proxy forwards origin and body and preserves HttpOnly cookie", async () => {
  const body = JSON.stringify({
    email: "candidate@example.com",
    password: "test-password",
  });
  const upstream = mock.method(globalThis, "fetch", async () =>
    Response.json(
      { role: "CANDIDATE" },
      {
        headers: {
          "Set-Cookie": "fsp_session=opaque; HttpOnly; SameSite=Lax; Path=/",
        },
      },
    ),
  );
  const result = await proxy(
    new Request("http://localhost:3000/api/auth/login", {
      method: "POST",
      body,
      headers: {
        Origin: "http://localhost:3000",
        "Content-Type": "application/json",
      },
    }),
    ["auth", "login"],
  );
  const [, options] = upstream.mock.calls[0].arguments as [string, RequestInit];
  assert.equal(
    new Headers(options.headers).get("origin"),
    "http://localhost:3000",
  );
  assert.equal(options.body, body);
  assert.match(result.headers.get("set-cookie") ?? "", /HttpOnly/);
  assert.equal(result.headers.get("cache-control"), "no-store");
});

test("authenticated read forwards cookie", async () => {
  const upstream = mock.method(globalThis, "fetch", async () =>
    Response.json({ id: "user" }),
  );
  await proxy(
    new Request("http://localhost:3000/api/auth/me", {
      headers: { Cookie: "fsp_session=opaque" },
    }),
    ["auth", "me"],
  );
  const [, options] = upstream.mock.calls[0].arguments as [string, RequestInit];
  assert.equal(
    new Headers(options.headers).get("cookie"),
    "fsp_session=opaque",
  );
});

test("missing Origin is never synthesized into trusted Origin", async () => {
  const upstream = mock.method(
    globalThis,
    "fetch",
    async () => new Response(null, { status: 403 }),
  );
  const result = await proxy(
    new Request("http://localhost:3000/api/auth/logout", {
      method: "POST",
      headers: { Cookie: "fsp_session=opaque" },
    }),
    ["auth", "logout"],
  );
  const [, options] = upstream.mock.calls[0].arguments as [string, RequestInit];
  assert.equal(new Headers(options.headers).get("origin"), null);
  assert.equal(result.status, 403);
});

test("logout proxy preserves cookie deletion and empty response", async () => {
  mock.method(
    globalThis,
    "fetch",
    async () =>
      new Response(null, {
        status: 204,
        headers: {
          "Set-Cookie": "fsp_session=; Max-Age=0; HttpOnly; Path=/",
        },
      }),
  );
  const result = await proxy(
    new Request("http://localhost:3000/api/auth/logout", { method: "POST" }),
    ["auth", "logout"],
  );
  assert.equal(result.status, 204);
  assert.equal(await result.text(), "");
  assert.match(result.headers.get("set-cookie") ?? "", /Max-Age=0/);
});

test("backend outage is converted into a structured 502 without sensitive details", async () => {
  mock.method(globalThis, "fetch", async () => {
    throw new Error("private-infrastructure-details");
  });
  const result = await proxy(new Request("http://localhost:3000/api/skills"), [
    "skills",
  ]);
  assert.equal(result.status, 502);
  assert.equal((await result.json()).error.code, "backend_unavailable");
});
