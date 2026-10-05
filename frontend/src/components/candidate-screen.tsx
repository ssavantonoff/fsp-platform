"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/api";
import { gradeLabels, specializationLabels } from "@/types";
import type { CandidateProfile, Grade, Skill, Specialization } from "@/types";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";

export function CandidateScreen({ edit = false }: { edit?: boolean }) {
  return (
    <RoleGate role="CANDIDATE">
      <CandidateContent edit={edit} />
    </RoleGate>
  );
}

function CandidateContent({ edit }: { edit: boolean }) {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const load = useCallback(
    () =>
      Promise.all([
        api<CandidateProfile>("/candidate/profile").catch((err) => {
          if (err instanceof ApiError && err.code === "profile_not_found")
            return null;
          throw err;
        }),
        api<Skill[]>("/skills"),
      ])
        .then(([existing, available]) => {
          setProfile(existing);
          setSkills(available);
        })
        .catch((err) => setError(err))
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
        <h1>Профиль кандидата</h1>
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
  if (edit)
    return (
      <CandidateEditor profile={profile} skills={skills} onSaved={setProfile} />
    );
  if (!profile)
    return (
      <section className="card">
        <h1>Профиль кандидата</h1>
        <p>Вы ещё не заполнили профиль.</p>
        <Link className="button" href="/candidate/edit">
          Создать профиль
        </Link>
      </section>
    );
  return (
    <section className="card">
      <h1>
        {profile.first_name} {profile.last_name}
      </h1>
      <dl>
        <dt>Специализация</dt>
        <dd>{specializationLabels[profile.specialization]}</dd>
        <dt>Заявленный уровень</dt>
        <dd>{gradeLabels[profile.declared_grade]}</dd>
        <dt>Подтверждённый уровень</dt>
        <dd>
          {profile.verified_grade
            ? gradeLabels[profile.verified_grade]
            : "не подтверждён"}
        </dd>
        <dt>Навыки</dt>
        <dd>{profile.skills.map((s) => s.name).join(", ") || "Не указаны"}</dd>
        <dt>Город</dt>
        <dd>{profile.city || "Не указан"}</dd>
        <dt>О себе</dt>
        <dd>{profile.about || "Не указано"}</dd>
        <dt>Опыт, лет</dt>
        <dd>{profile.years_of_experience ?? "Не указан"}</dd>
        <dt>FSP ID</dt>
        <dd>{profile.fsp_id || "Не указан"}</dd>
        <dt>Согласие на обработку данных</dt>
        <dd>{profile.personal_data_consent ? "Дано" : "Не дано"}</dd>
      </dl>
      <Link className="button" href="/candidate/edit">
        Редактировать профиль
      </Link>
    </section>
  );
}

function CandidateEditor({
  profile,
  skills,
  onSaved,
}: {
  profile: CandidateProfile | null;
  skills: Skill[];
  onSaved: (p: CandidateProfile) => void;
}) {
  const [selected, setSelected] = useState<string[]>(
    profile?.skills.map((s) => s.id) ?? [],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess("");
    const form = new FormData(event.currentTarget);
    const optional = (name: string) =>
      String(form.get(name) ?? "").trim() || null;
    const years = optional("years_of_experience");
    const body = {
      first_name: String(form.get("first_name") ?? "").trim(),
      last_name: String(form.get("last_name") ?? "").trim(),
      city: optional("city"),
      about: optional("about"),
      fsp_id: optional("fsp_id"),
      specialization: form.get("specialization"),
      declared_grade: form.get("declared_grade"),
      years_of_experience: years === null ? null : Number(years),
      personal_data_consent: form.get("personal_data_consent") === "on",
      skill_ids: selected,
    };
    try {
      const saved = await api<CandidateProfile>("/candidate/profile", {
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
        {profile ? "Редактирование профиля" : "Создание профиля кандидата"}
      </h1>
      <p className="hint">
        Подтверждённый уровень:{" "}
        {profile?.verified_grade
          ? gradeLabels[profile.verified_grade]
          : "не подтверждён"}
        .
      </p>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <div className="columns">
            <label>
              Имя
              <input
                name="first_name"
                required
                maxLength={100}
                defaultValue={profile?.first_name}
                autoComplete="given-name"
              />
            </label>
            <label>
              Фамилия
              <input
                name="last_name"
                required
                maxLength={100}
                defaultValue={profile?.last_name}
                autoComplete="family-name"
              />
            </label>
          </div>
          <label>
            Город
            <input
              name="city"
              maxLength={200}
              defaultValue={profile?.city ?? ""}
              autoComplete="address-level2"
            />
          </label>
          <label>
            О себе
            <textarea
              name="about"
              maxLength={5000}
              defaultValue={profile?.about ?? ""}
            />
          </label>
          <div className="columns">
            <label>
              Специализация
              <select
                name="specialization"
                defaultValue={profile?.specialization ?? "BACKEND"}
              >
                {Object.entries(specializationLabels).map(([key, label]) => (
                  <option key={key} value={key as Specialization}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Заявленный уровень
              <select
                name="declared_grade"
                defaultValue={profile?.declared_grade ?? "JUNIOR"}
              >
                {Object.entries(gradeLabels).map(([key, label]) => (
                  <option key={key} value={key as Grade}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <fieldset className="skills">
            <legend>Навыки</legend>
            {skills.length === 0 ? (
              <p>
                Справочник пока пуст. Заполните skills командой seed из README.
              </p>
            ) : (
              skills.map((skill) => (
                <label className="checkbox" key={skill.id}>
                  <input
                    type="checkbox"
                    checked={selected.includes(skill.id)}
                    onChange={(e) => {
                      setSuccess("");
                      setSelected(
                        e.target.checked
                          ? [...selected, skill.id]
                          : selected.filter((id) => id !== skill.id),
                      );
                    }}
                  />
                  {skill.name}
                </label>
              ))
            )}
          </fieldset>
          <label>
            Опыт работы, лет
            <input
              name="years_of_experience"
              type="number"
              min={0}
              max={80}
              step="0.1"
              defaultValue={profile?.years_of_experience ?? ""}
            />
          </label>
          <label>
            FSP ID
            <input
              name="fsp_id"
              maxLength={200}
              defaultValue={profile?.fsp_id ?? ""}
            />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              name="personal_data_consent"
              defaultChecked={profile?.personal_data_consent ?? false}
            />
            Даю согласие на обработку персональных данных
          </label>
          <Feedback error={error} success={success} />
          <div className="actions">
            <button type="submit" disabled={busy}>
              {busy ? "Сохраняем…" : "Сохранить профиль"}
            </button>
            <Link href="/candidate">Посмотреть профиль</Link>
          </div>
        </fieldset>
      </form>
    </section>
  );
}
