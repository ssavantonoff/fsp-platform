"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/api";
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
  if (success)
    return (
      <section className="card">
        <h1>Аккаунт создан</h1>
        <p>
          Подтвердите email по ссылке из письма. Для локальной разработки ссылка
          выводится в журнал backend.
        </p>
        <div className="actions">
          <Link className="button" href="/login">
            Перейти ко входу
          </Link>
          <Link href="/verify-email">Подтверждение email</Link>
        </div>
      </section>
    );
  return (
    <section className="card narrow">
      <h1>{register ? "Регистрация" : "Вход"}</h1>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <label>
            Email
            <input
              name="email"
              type="email"
              required
              maxLength={254}
              autoComplete="email"
            />
          </label>
          <label>
            Пароль
            <input
              name="password"
              type="password"
              required
              minLength={register ? 10 : 1}
              maxLength={128}
              autoComplete={register ? "new-password" : "current-password"}
            />
          </label>
          {register && (
            <>
              <p className="hint">От 10 до 128 символов.</p>
              <label>
                Роль
                <select name="role" required>
                  <option value="CANDIDATE">Кандидат</option>
                  <option value="EMPLOYER">Работодатель</option>
                </select>
              </label>
              <p className="hint">Роль выбирается один раз при регистрации.</p>
            </>
          )}
          <Feedback error={error} />
          <button type="submit" disabled={busy}>
            {busy ? "Отправляем…" : register ? "Создать аккаунт" : "Войти"}
          </button>
        </fieldset>
      </form>
      <p>
        {register ? "Уже есть аккаунт?" : "Нет аккаунта?"}{" "}
        <Link href={register ? "/login" : "/register"}>
          {register ? "Войти" : "Зарегистрироваться"}
        </Link>
      </p>
    </section>
  );
}
