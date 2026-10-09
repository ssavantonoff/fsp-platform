"use client";

import Link from "next/link";
import { ApiError } from "@/api";
import { Feedback } from "./feedback";

export function VerifyEmailView({ token, busy, success, error, onTokenChange, onSubmit }: {
  token: string;
  busy: boolean;
  success: boolean;
  error: unknown;
  onTokenChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}) {
  const invalid = error instanceof ApiError && (error.code === "invalid_token" || error.fields.some((field) => field.field === "token"));
  return (
    <section className={`card narrow auth-screen${success ? " auth-success" : ""}`}>
      <div className="auth-heading">
        <span className="eyebrow">Аккаунт ФСП</span>
        <h1 id="verify-email-title">Подтверждение email</h1>
      </div>
      {success ? (
        <>
          <Feedback success="Email подтверждён." />
          <div className="actions"><Link className="button" href="/login">Перейти ко входу</Link></div>
        </>
      ) : (
        <>
          <p>Откройте ссылку из письма, чтобы подтвердить email.</p>
          <form className="auth-form" onSubmit={onSubmit} aria-labelledby="verify-email-title" aria-describedby={error != null ? "verify-email-feedback" : undefined} aria-busy={busy}>
            <fieldset className="auth-fields" disabled={busy}>
              <label htmlFor="verify-email-token">
                Код из ссылки подтверждения
                <input
                  id="verify-email-token"
                  name="token"
                  value={token}
                  onChange={(event) => onTokenChange(event.target.value)}
                  required
                  minLength={32}
                  maxLength={128}
                  autoComplete="off"
                  aria-invalid={invalid || undefined}
                  aria-describedby={["verify-email-hint", invalid ? "verify-email-feedback" : null].filter(Boolean).join(" ")}
                />
              </label>
              <p id="verify-email-hint" className="hint">Если поле не заполнилось автоматически, вставьте код подтверждения из ссылки в письме.</p>
              {error != null && <div id="verify-email-feedback"><Feedback error={error} /></div>}
              <button disabled={busy} type="submit">
                {busy ? "Подтверждаем…" : "Подтвердить email"}
              </button>
            </fieldset>
          </form>
        </>
      )}
    </section>
  );
}
