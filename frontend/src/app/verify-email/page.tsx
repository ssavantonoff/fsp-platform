"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/api";
import { useAuth } from "@/components/auth";
import { Feedback } from "@/components/feedback";

export default function VerifyEmail() {
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const { refresh } = useAuth();
  useEffect(() => {
    const parsed = new URLSearchParams(window.location.hash.slice(1)).get(
      "token",
    );
    if (parsed) {
      // Reading browser state once initializes the confirmation form.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setToken(parsed);
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, []);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api<void>("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setToken("");
      setSuccess(true);
      await refresh();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card narrow">
      <h1>Подтверждение email</h1>
      {success ? (
        <>
          <p role="status" className="success">
            Email подтверждён.
          </p>
          <Link href="/login">Перейти ко входу</Link>
        </>
      ) : (
        <>
          <p>
            Откройте ссылку из письма или вставьте токен. В локальной среде
            ссылка доступна в журнале backend. Ссылка действует один час при
            стандартных настройках.
          </p>
          <form onSubmit={submit}>
            <fieldset disabled={busy}>
              <label>
                Токен подтверждения
                <input
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                  minLength={32}
                  maxLength={128}
                  autoComplete="off"
                />
              </label>
              <Feedback error={error} />
              <button disabled={busy} type="submit">
                {busy ? "Подтверждаем…" : "Подтвердить"}
              </button>
            </fieldset>
          </form>
        </>
      )}
    </section>
  );
}
