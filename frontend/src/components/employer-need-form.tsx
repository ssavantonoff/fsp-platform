"use client";

import { validateNeedForm } from "@/employer-needs";
import type { NeedFormValues } from "@/employer-needs";
import { gradeLabels, specializationLabels } from "@/types";
import type { Grade, Skill, Specialization } from "@/types";

export interface NeedFormProps {
  values: NeedFormValues;
  skills: Skill[];
  busy: boolean;
  errors: Record<string, string>;
  onChange: (values: NeedFormValues) => void;
  onSubmit: () => void;
  submitLabel?: string;
}
export function EmployerNeedForm({ values, skills, busy, errors, onChange, onSubmit, submitLabel = "Сохранить" }: NeedFormProps) {
  const invalid = Object.keys(validateNeedForm(values)).length > 0;
  const change = <K extends keyof NeedFormValues>(key: K, value: NeedFormValues[K]) => onChange({ ...values, [key]: value });
  const fieldError = (key: string) => errors[key] ? <p id={`need-error-${key}`} role="alert" className="field-error">{errors[key]}</p> : null;
  const describedBy = (key: string) => errors[key] ? `need-error-${key}` : undefined;
  const groups = [
    {
      key: "must_have_skill_ids" as const,
      other: "nice_to_have_skill_ids" as const,
      label: "Обязательные навыки",
      className: "need-skills-required",
      hint: "Кандидат должен иметь все обязательные навыки, иначе он не попадёт в подбор."
    },
    {
      key: "nice_to_have_skill_ids" as const,
      other: "must_have_skill_ids" as const,
      label: "Желательные навыки",
      className: "need-skills-preferred",
      hint: "Желательные навыки влияют на Professional Fit, но их отсутствие не исключает кандидата из подбора."
    },
  ];
  return (
    <form className="workflow-form" onSubmit={(event) => {
      event.preventDefault();
      if (!busy && !invalid) onSubmit();
    }}>
      <fieldset disabled={busy}>
        <section className="workflow-form-section" aria-labelledby="need-section-main">
          <h2 id="need-section-main">Основная информация</h2>
          <label>Позиция
            <input
              name="position_title"
              required
              maxLength={200}
              placeholder="Backend-разработчик"
              value={values.position_title}
              onChange={(event) => change("position_title", event.target.value)}
              aria-describedby={describedBy("position_title")} />
          </label>
          {fieldError("position_title")}
          <label>Специализация
            <select
              name="specialization"
              value={values.specialization}
              onChange={(event) => change("specialization", event.target.value as Specialization)}>
              {Object.entries(specializationLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label>Описание потребности
            <textarea
              name="description"
              required
              value={values.description}
              onChange={(event) => change("description", event.target.value)}
              aria-describedby={describedBy("description")} />
          </label>
          {fieldError("description")}
        </section>
        <section className="workflow-form-section" aria-labelledby="need-section-qualification">
          <h2 id="need-section-qualification">Требования к квалификации</h2>
          <label>Требуемый уровень
            <select
              name="required_grade"
              value={values.required_grade}
              onChange={(event) => change("required_grade", event.target.value as Grade)}>
              {Object.entries(gradeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label>Целевой опыт, лет
            <input
              name="target_experience_years"
              type="number"
              min="0"
              step="0.5"
              value={values.target_experience_years}
              onChange={(event) => change("target_experience_years", event.target.value)}
              aria-describedby={["need-experience-hint", describedBy("target_experience_years")].filter(Boolean).join(" ")} />
          </label>
          <p id="need-experience-hint" className="hint">Если не указано, опыт не участвует в Professional Fit.</p>
          {fieldError("target_experience_years")}
        </section>
        <section className="workflow-form-section" aria-labelledby="need-section-skills">
          <h2 id="need-section-skills">Навыки</h2>
          <div className="need-skill-groups">
            {groups.map(({ key, other, label, hint, className }) => <div className="need-form-section" key={key}>
              <fieldset className={`skills ${className}`} aria-describedby={[`need-hint-${key}`, describedBy(key)].filter(Boolean).join(" ")}>
                <legend>{label}</legend>
                <p id={`need-hint-${key}`} className="hint">{hint}</p>
                {skills.map((skill) => <label className="checkbox" key={skill.id}>
                  <input
                    type="checkbox"
                    name={key}
                    disabled={values[other].includes(skill.id)}
                    value={skill.id}
                    checked={values[key].includes(skill.id)}
                    onChange={(event) => change(key, event.target.checked ? [...values[key], skill.id] : values[key].filter((id) => id !== skill.id))} />
                  {skill.name}
                </label>)}
              </fieldset>
              {fieldError(key)}
            </div>)}
          </div>
        </section>
        <section className="workflow-form-section" aria-labelledby="need-section-conditions">
          <h2 id="need-section-conditions">Условия работы</h2>
          <div className="columns">
            {(["salary_from", "salary_to"] as const).map((key) => <div key={key}>
              <label>{key === "salary_from" ? "Зарплата от" : "Зарплата до"} (RUB, до вычета налогов)
                <input
                  name={key}
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={values[key]}
                  onChange={(event) => change(key, event.target.value)}
                  aria-describedby={describedBy(key)} />
              </label>
              {fieldError(key)}
            </div>)}
          </div>
          <p className="hint">Суммы указываются в рублях.</p>
        </section>
        <section className="workflow-form-section" aria-labelledby="need-section-additional">
          <h2 id="need-section-additional">Дополнительная информация</h2>
          <label>Дополнительные требования
            <textarea
              name="additional_requirements"
              value={values.additional_requirements}
              onChange={(event) => change("additional_requirements", event.target.value)}
              aria-describedby="need-additional-hint" />
          </label>
          <p id="need-additional-hint" className="hint">Не влияет на Professional Fit и автоматическое ранжирование.</p>
        </section>
        <div className="actions">
          <button type="submit" disabled={busy || invalid}>{busy ? "Сохраняем…" : submitLabel}</button>
        </div>
      </fieldset>
    </form>
  );
}
