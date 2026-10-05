"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/api";
import type { EmployerProfile } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";

export function EmployerScreen({ edit = false }: { edit?: boolean }) {
  return (
    <RoleGate role="EMPLOYER">
      <EmployerContent edit={edit} />
    </RoleGate>
  );
}

function EmployerContent({ edit }: { edit: boolean }) {
  const [profile, setProfile] = useState<EmployerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const load = useCallback(
    () =>
      api<EmployerProfile>("/employer/profile")
        .then((existing) => setProfile(existing))
        .catch((err) => {
          if (err instanceof ApiError && err.code === "profile_not_found")
            setProfile(null);
          else setError(err);
        })
        .finally(() => setLoading(false)),
    [],
  );
  useEffect(() => {
    void load();
  }, [load]);
  if (loading) return <p role="status">Загрузка профиля…</p>;
  if (error)
    return (
      <section className="card">
        <h1>Профиль работодателя</h1>
        <Feedback error={error} />
        <button
          onClick={() => {
            setLoading(true);
            setError(null);
            void load();
          }}
        >
          Повторить
        </button>
      </section>
    );
  if (edit) return <EmployerEditor profile={profile} onSaved={setProfile} />;
  if (!profile)
    return (
      <section className="card">
        <h1>Профиль работодателя</h1>
        <p>Вы ещё не заполнили профиль компании.</p>
        <Link className="button" href="/employer/edit">
          Создать профиль
        </Link>
      </section>
    );
  return (
    <section className="card">
      <h1>{profile.company_name}</h1>
      <dl>
        <dt>Описание компании</dt>
        <dd>{profile.company_description || "Не указано"}</dd>
        <dt>Сайт</dt>
        <dd>
          {profile.website ? (
            <a href={profile.website} target="_blank" rel="noopener noreferrer">
              {profile.website}
            </a>
          ) : (
            "Не указан"
          )}
        </dd>
        <dt>Контактное лицо</dt>
        <dd>{profile.contact_person_name}</dd>
      </dl>
      <Link className="button" href="/employer/edit">
        Редактировать профиль
      </Link>
    </section>
  );
}

function EmployerEditor({
  profile,
  onSaved,
}: {
  profile: EmployerProfile | null;
  onSaved: (p: EmployerProfile) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess("");
    const form = new FormData(event.currentTarget);
    const body = {
      company_name: String(form.get("company_name") ?? "").trim(),
      company_description:
        String(form.get("company_description") ?? "").trim() || null,
      website: String(form.get("website") ?? "").trim() || null,
      contact_person_name: String(form.get("contact_person_name") ?? "").trim(),
    };
    try {
      const saved = await api<EmployerProfile>("/employer/profile", {
        method: profile ? "PUT" : "POST",
        body: JSON.stringify(body),
      });
      onSaved(saved);
      setSuccess("Профиль сохранён.");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card">
      <h1>
        {profile ? "Редактирование компании" : "Создание профиля компании"}
      </h1>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <label>
            Название компании
            <input
              name="company_name"
              required
              maxLength={200}
              defaultValue={profile?.company_name}
              autoComplete="organization"
            />
          </label>
          <label>
            Описание компании
            <textarea
              name="company_description"
              maxLength={5000}
              defaultValue={profile?.company_description ?? ""}
            />
          </label>
          <label>
            Сайт компании
            <input
              name="website"
              type="url"
              maxLength={2048}
              placeholder="https://example.com"
              defaultValue={profile?.website ?? ""}
            />
          </label>
          <label>
            Контактное лицо
            <input
              name="contact_person_name"
              required
              maxLength={200}
              defaultValue={profile?.contact_person_name}
              autoComplete="name"
            />
          </label>
          <Feedback error={error} success={success} />
          <div className="actions">
            <button type="submit" disabled={busy}>
              {busy ? "Сохраняем…" : "Сохранить профиль"}
            </button>
            <Link href="/employer">Посмотреть профиль</Link>
          </div>
        </fieldset>
      </form>
    </section>
  );
}
