import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import { ApiError } from "../src/api";
import { AuthFormView } from "../src/components/auth-form";
import { VerifyEmailView } from "../src/components/verify-email-form";

const authProps = { register: true, busy: false, error: null, success: false, onSubmit: () => {} };
const verifyProps = { token: "", busy: false, error: null, success: false, onTokenChange: () => {}, onSubmit: () => {} };
function authView(overrides: Partial<Parameters<typeof AuthFormView>[0]> = {}) {
  return renderToStaticMarkup(createElement(AuthFormView, { ...authProps, ...overrides }));
}
function verifyView(overrides: Partial<Parameters<typeof VerifyEmailView>[0]> = {}) {
  return renderToStaticMarkup(createElement(VerifyEmailView, { ...verifyProps, ...overrides }));
}
function input(html: string, name: string) {
  return html.match(new RegExp(`<input[^>]*name="${name}"[^>]*>`))![0];
}

test("registration keeps existing fields, roles and constraints with associated labels and hints", () => {
  const html = authView();
  assert.match(html, /<h1 id="auth-title">Регистрация<\/h1>/);
  assert.match(html, /<form[^>]*aria-labelledby="auth-title"/);
  for (const field of ["email", "password", "role"]) assert.ok(html.includes(`for="auth-${field}"`));
  assert.match(input(html, "email"), /type="email"[^>]*required=""[^>]*maxLength="254"[^>]*autoComplete="email"/);
  assert.match(input(html, "email"), /aria-describedby="auth-email-hint"/);
  assert.match(input(html, "password"), /type="password"[^>]*required=""[^>]*minLength="10"[^>]*maxLength="128"[^>]*autoComplete="new-password"/);
  assert.match(input(html, "password"), /aria-describedby="auth-password-hint"/);
  assert.match(html, /<select[^>]*name="role" required=""[^>]*aria-describedby="auth-role-hint"/);
  assert.match(html, /value="CANDIDATE">Кандидат/);
  assert.match(html, /value="EMPLOYER">Работодатель/);
  assert.match(html, /От 10 до 128 символов\./);
  assert.match(html, /выбирается один раз при регистрации/);
  assert.match(html, /href="\/login">Войти/);
  assert.doesNotMatch(html, /восстанов|сброс|reset|forgot/i);
});

test("login keeps current password rules and does not submit a role", () => {
  const html = authView({ register: false });
  assert.match(html, /<h1 id="auth-title">Вход<\/h1>/);
  assert.match(input(html, "password"), /minLength="1"[^>]*maxLength="128"[^>]*autoComplete="current-password"/);
  assert.doesNotMatch(html, /name="role"|auth-password-hint|auth-role-hint|От 10 до 128/);
  assert.match(html, /href="\/register">Зарегистрироваться/);
});

test("auth busy state announces the request and disables all existing inputs and submit", () => {
  for (const register of [true, false]) {
    const html = authView({ register, busy: true });
    assert.match(html, /<form[^>]*aria-busy="true"/);
    assert.match(html, /<fieldset[^>]*disabled=""/);
    assert.match(html, /<button type="submit" disabled="">Отправляем…/);
  }
});

test("auth server field errors are linked to affected controls and escaped", () => {
  const error = new ApiError(422, "validation_error", "Проверьте поля <script>unsafe()</script>", [
    { field: "email", message: "Email занят" },
    { field: "password", message: "Слишком короткий пароль" },
    { field: "role", message: "Проверьте тип аккаунта" },
  ]);
  const html = authView({ error });
  assert.match(html, /<form[^>]*aria-describedby="auth-feedback"/);
  assert.match(html, /id="auth-feedback"><div role="alert"/);
  for (const field of ["email", "password"]) {
    assert.match(input(html, field), /aria-invalid="true"/);
    assert.ok(input(html, field).includes(`aria-describedby="auth-${field}-hint auth-feedback"`));
  }
  assert.match(html, /<select[^>]*aria-invalid="true"[^>]*aria-describedby="auth-role-hint auth-feedback"/);
  assert.match(html, /&lt;script&gt;unsafe\(\)&lt;\/script&gt;/);
  assert.doesNotMatch(html, /<script>/);
  const network = authView({ error: new ApiError(0, "network_error", "Повторите попытку.") });
  assert.match(network, /aria-describedby="auth-feedback"/);
  assert.doesNotMatch(network, /aria-invalid="true"/);
});

test("registration success offers only existing routes without exposing deployment details", () => {
  const html = authView({ success: true });
  assert.match(html, /Аккаунт создан/);
  assert.match(html, /role="status" class="success">Регистрация завершена/);
  assert.match(html, /Подтвердите email по ссылке из письма/);
  assert.match(html, /class="button" href="\/login">Перейти ко входу/);
  assert.match(html, /class="button secondary" href="\/verify-email">Подтверждение email/);
  assert.doesNotMatch(html, /<form|name="password"|backend|журнал|один час|SMTP/i);
});

test("verification uses the existing manual code constraints and accessible help", () => {
  const html = verifyView({ token: "a".repeat(32) });
  assert.match(html, /<h1 id="verify-email-title">Подтверждение email/);
  assert.match(html, /for="verify-email-token"/);
  assert.match(html, /<form[^>]*aria-labelledby="verify-email-title"/);
  assert.match(input(html, "token"), /required=""[^>]*minLength="32"[^>]*maxLength="128"[^>]*autoComplete="off"/);
  assert.match(input(html, "token"), /aria-describedby="verify-email-hint"/);
  assert.match(input(html, "token"), /value="a{32}"/);
  assert.match(html, /id="verify-email-hint"/);
  assert.match(html, /Подтвердить email/);
  assert.doesNotMatch(html, /backend|журнал|один час|SMTP|повторно отправ/i);
});

test("verification busy state preserves the code while disabling confirmation", () => {
  const html = verifyView({ busy: true, token: "b".repeat(32) });
  assert.match(html, /<form[^>]*aria-busy="true"/);
  assert.match(html, /<fieldset[^>]*disabled=""/);
  assert.match(html, /<button disabled="" type="submit">Подтверждаем…/);
  assert.match(input(html, "token"), /value="b{32}"/);
});

test("invalid or expired verification code has an associated accessible error", () => {
  const html = verifyView({ error: new ApiError(400, "invalid_token", "Ссылка недействительна или срок истёк.") });
  assert.match(input(html, "token"), /aria-invalid="true"/);
  assert.match(input(html, "token"), /aria-describedby="verify-email-hint verify-email-feedback"/);
  assert.match(html, /id="verify-email-feedback"><div role="alert"/);
  assert.match(html, /Ссылка недействительна или срок истёк/);
  const network = verifyView({ error: new ApiError(0, "network_error", "Повторите попытку.") });
  assert.match(network, /<form[^>]*aria-describedby="verify-email-feedback"/);
  assert.doesNotMatch(input(network, "token"), /aria-invalid/);
});

test("verification success hides the confirmation code and provides the login route", () => {
  const html = verifyView({ success: true, token: "private-verification-token" });
  assert.match(html, /role="status" class="success">Email подтверждён/);
  assert.match(html, /class="button" href="\/login">Перейти ко входу/);
  assert.doesNotMatch(html, /<form|<input|private-verification-token/);
});

function submitHandler(path: string, component: string, context: Record<string, unknown>) {
  const source = readFileSync(path, "utf8");
  const file = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const controller = file.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === component) as ts.FunctionDeclaration;
  const handler = controller.body!.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "submit")!;
  const script = ts.transpileModule(`${handler.getText(file)}\nsubmit`, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  return runInNewContext(script, context) as (event: { preventDefault: () => void; currentTarget: unknown }) => Promise<void>;
}

test("auth submit preserves POST payload, registration success and role-specific login redirect", async () => {
  for (const register of [true, false]) for (const role of ["CANDIDATE", "EMPLOYER"]) {
    const calls: { path: string; options: RequestInit }[] = [];
    const redirects: string[] = [];
    const busy: boolean[] = [];
    let success = false;
    let refreshed = 0;
    const values = { email: "demo@example.com", password: "private-password", role };
    const handler = submitHandler("src/components/auth-form.tsx", "AuthForm", {
      register,
      api: async (path: string, options: RequestInit) => { calls.push({ path, options: { ...options } }); return { role }; },
      FormData: class { get(key: keyof typeof values) { return values[key]; } },
      setBusy: (value: boolean) => busy.push(value), setError: () => {}, setSuccess: (value: boolean) => { success = value; },
      refresh: async () => { refreshed += 1; }, router: { push: (path: string) => redirects.push(path) },
    });
    await handler({ preventDefault: () => {}, currentTarget: {} });
    assert.deepEqual(calls, [{ path: register ? "/auth/register" : "/auth/login", options: {
      method: "POST", body: JSON.stringify({ email: values.email, password: values.password, ...(register ? { role } : {}) }),
    } }]);
    assert.deepEqual(busy, [true, false]);
    assert.equal(success, register);
    assert.equal(refreshed, register ? 0 : 1);
    assert.deepEqual(redirects, register ? [] : [role === "CANDIDATE" ? "/candidate" : "/employer"]);
  }
});

test("verification submit keeps token in POST body, clears it only after success and refreshes auth", async () => {
  for (const fails of [false, true]) {
    const calls: { path: string; options: RequestInit }[] = [];
    const busy: boolean[] = [];
    const errors: unknown[] = [];
    const error = new ApiError(400, "invalid_token", "Ссылка недействительна.");
    const original = "c".repeat(32);
    let token = original;
    let success = false;
    let refreshed = 0;
    const handler = submitHandler("src/app/verify-email/page.tsx", "VerifyEmail", {
      token: original,
      api: async (path: string, options: RequestInit) => { calls.push({ path, options: { ...options } }); if (fails) throw error; },
      setToken: (value: string) => { token = value; }, setSuccess: (value: boolean) => { success = value; },
      setBusy: (value: boolean) => busy.push(value), setError: (value: unknown) => errors.push(value),
      refresh: async () => { refreshed += 1; },
    });
    await handler({ preventDefault: () => {}, currentTarget: {} });
    assert.deepEqual(calls, [{ path: "/auth/verify-email", options: { method: "POST", body: JSON.stringify({ token: original }) } }]);
    assert.deepEqual(busy, [true, false]);
    assert.equal(token, fails ? original : "");
    assert.equal(success, !fails);
    assert.equal(refreshed, fails ? 0 : 1);
    assert.deepEqual(errors, fails ? [null, error] : [null]);
  }
});

test("verification fragment is removed on initialization without sending a request", () => {
  const path = "src/app/verify-email/page.tsx";
  const file = ts.createSourceFile(path, readFileSync(path, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const controller = file.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "VerifyEmail") as ts.FunctionDeclaration;
  const effect = controller.body!.statements.find((node) => ts.isExpressionStatement(node) && ts.isCallExpression(node.expression) && node.expression.expression.getText(file) === "useEffect") as ts.ExpressionStatement;
  const call = effect.expression as ts.CallExpression;
  const callback = call.arguments[0];
  const script = ts.transpileModule(`(${callback.getText(file)})()`, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  for (const hash of ["#token=" + "d".repeat(32), ""]) {
    let token = "";
    const historyCalls: unknown[][] = [];
    runInNewContext(script, {
      URLSearchParams,
      setToken: (value: string) => { token = value; },
      window: { location: { hash, pathname: "/verify-email" }, history: { replaceState: (...args: unknown[]) => historyCalls.push(args) } },
      api: () => { assert.fail("Initialization must not confirm the email"); },
    });
    assert.equal(token, hash ? "d".repeat(32) : "");
    assert.deepEqual(historyCalls, hash ? [[null, "", "/verify-email"]] : []);
  }
});
