import assert from "node:assert/strict";
import { afterEach, mock, test } from "node:test";
import { api, ApiError } from "../src/api";

afterEach(() => mock.restoreAll());

test("API uses same-origin cookie requests and never caches user data", async () => {
  const fetchMock = mock.method(globalThis, "fetch", async () =>
    Response.json({ id: "user" }),
  );
  assert.deepEqual(await api("/auth/me"), { id: "user" });
  const [url, options] = fetchMock.mock.calls[0].arguments as [
    string,
    RequestInit,
  ];
  assert.equal(url, "/api/auth/me");
  assert.equal(options.credentials, "same-origin");
  assert.equal(options.cache, "no-store");
});

test("server validation details remain available to forms", async () => {
  mock.method(globalThis, "fetch", async () =>
    Response.json(
      {
        error: {
          code: "validation_error",
          message: "Проверьте поля",
          fields: [{ field: "first_name", message: "Required" }],
        },
      },
      { status: 422 },
    ),
  );
  await assert.rejects(
    api("/candidate/profile", { method: "POST" }),
    (err: unknown) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.status, 422);
      assert.equal(err.code, "validation_error");
      assert.deepEqual(err.fields, [
        { field: "first_name", message: "Required" },
      ]);
      return true;
    },
  );
});

test("expired session remains identifiable as 401", async () => {
  mock.method(globalThis, "fetch", async () =>
    Response.json(
      { error: { code: "unauthorized", message: "Войдите" } },
      { status: 401 },
    ),
  );
  await assert.rejects(
    api("/auth/me"),
    (err: unknown) => err instanceof ApiError && err.status === 401,
  );
});

test("unavailable network gives an actionable error", async () => {
  mock.method(globalThis, "fetch", async () => {
    throw new TypeError("Failed to fetch");
  });
  await assert.rejects(
    api("/skills"),
    (err: unknown) => err instanceof ApiError && err.code === "network_error",
  );
});

test("non-JSON server failure still gives a form error", async () => {
  mock.method(
    globalThis,
    "fetch",
    async () => new Response("upstream down", { status: 502 }),
  );
  await assert.rejects(
    api("/skills"),
    (err: unknown) => err instanceof ApiError && err.status === 502,
  );
});

test("logout accepts an empty 204 response", async () => {
  mock.method(
    globalThis,
    "fetch",
    async () => new Response(null, { status: 204 }),
  );
  assert.equal(await api("/auth/logout", { method: "POST" }), undefined);
});

test("invalid success response is reported instead of silently clearing data", async () => {
  mock.method(
    globalThis,
    "fetch",
    async () => new Response("invalid", { status: 200 }),
  );
  await assert.rejects(
    api("/candidate/profile"),
    (err: unknown) =>
      err instanceof ApiError && err.code === "invalid_response",
  );
});
