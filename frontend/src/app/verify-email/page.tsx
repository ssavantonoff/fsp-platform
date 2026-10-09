"use client";

import { useEffect, useState } from "react";
import { api } from "@/api";
import { useAuth } from "@/components/auth";
import { VerifyEmailView } from "@/components/verify-email-form";

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
  return <VerifyEmailView token={token} busy={busy} success={success} error={error} onTokenChange={setToken} onSubmit={submit} />;
}
