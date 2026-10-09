"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/api";
import type { User } from "@/types";
import { useAuth } from "./auth";
import { Feedback } from "./feedback";

export function AuthForm({ register = false }: { register?: boolean }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState(false);
  const router = useRouter();
  const { refresh } = useAuth();
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const body = {
      email: form.get("email"),
      password: form.get("password"),
      ...(register ? { role: form.get("role") } : {}),
    };
    try {
      const user = await api<User>(
        register ? "/auth/register" : "/auth/login",
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      );
      if (register) setSuccess(true);
      else {
        await refresh();
        router.push(user.role === "CANDIDATE" ? "/candidate" : "/employer");
      }
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return <AuthFormView register={register} busy={busy} error={error} success={success} onSubmit={submit} />;
}

export function AuthFormView({ register, busy, error, success, onSubmit }: {
  register: boolean;
  busy: boolean;
  error: unknown;
  success: boolean;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}) {
  const invalid = (field: string) => error instanceof ApiError && error.fields.some((item) => item.field === field);
  const describedBy = (field: string, hint?: string) => [hint, invalid(field) ? "auth-feedback" : null].filter(Boolean).join(" ") || undefined;
  if (success)
    return (
      <section className="card narrow auth-screen auth-success">
        <div className="auth-heading">
          <span className="eyebrow">Регистрация</span>
          <h1>Аккаунт создан</h1>
        </div>
        <Feedback success="Регистрация завершена." />
        <p>Подтвердите email по ссылке из письма.</p>
        <div className="actions">
          <Link className="button" href="/login">
            Перейти ко входу
          </Link>
          <Link className="button secondary" href="/verify-email">Подтверждение email</Link>
        </div>
      </section>
    );
  return (
    <section className="card narrow auth-screen">
      <div className="auth-heading">
        <span className="eyebrow">Платформа ФСП</span>
        <h1 id="auth-title">{register ? "Регистрация" : "Вход"}</h1>
        <p>{register ? "Создайте аккаунт кандидата или работодателя." : "Войдите, чтобы продолжить работу с платформой."}</p>
      </div>
      <form className="auth-form" onSubmit={onSubmit} aria-labelledby="auth-title" aria-describedby={error != null ? "auth-feedback" : undefined} aria-busy={busy}>
        <fieldset className="auth-fields" disabled={busy}>
          <label htmlFor="auth-email">
            Email
            <input
              id="auth-email"
              name="email"
              type="email"
              required
              maxLength={254}
              autoComplete="email"
              aria-invalid={invalid("email") || undefined}
              aria-describedby={describedBy("email", "auth-email-hint")}
            />
          </label>
          <p id="auth-email-hint" className="hint">{register ? "На этот адрес придёт ссылка для подтверждения email." : "Email, указанный при регистрации."}</p>
          <label htmlFor="auth-password">
            Пароль
            <input
              id="auth-password"
              name="password"
              type="password"
              required
              minLength={register ? 10 : 1}
              maxLength={128}
              autoComplete={register ? "new-password" : "current-password"}
              aria-invalid={invalid("password") || undefined}
              aria-describedby={describedBy("password", register ? "auth-password-hint" : undefined)}
            />
          </label>
          {register && (
            <>
              <p id="auth-password-hint" className="hint">От 10 до 128 символов.</p>
              <label htmlFor="auth-role">
                Тип аккаунта
                <select id="auth-role" name="role" required aria-invalid={invalid("role") || undefined} aria-describedby={describedBy("role", "auth-role-hint")}>
                  <option value="CANDIDATE">Кандидат</option>
                  <option value="EMPLOYER">Работодатель</option>
                </select>
              </label>
              <p id="auth-role-hint" className="hint">Тип аккаунта выбирается один раз при регистрации.</p>
            </>
          )}
          {error != null && <div id="auth-feedback"><Feedback error={error} /></div>}
          <button type="submit" disabled={busy}>
            {busy ? "Отправляем…" : register ? "Создать аккаунт" : "Войти"}
          </button>
        </fieldset>
      </form>
      <p className="auth-footer">
        {register ? "Уже есть аккаунт?" : "Нет аккаунта?"}{" "}
        <Link href={register ? "/login" : "/register"}>
          {register ? "Войти" : "Зарегистрироваться"}
        </Link>
      </p>
    </section>
  );
}
