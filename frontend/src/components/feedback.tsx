import { ApiError, errorMessage } from "@/api";

const labels: Record<string, string> = {
  email: "Email",
  password: "Пароль",
  role: "Роль",
  first_name: "Имя",
  last_name: "Фамилия",
  city: "Город",
  about: "О себе",
  specialization: "Специализация",
  declared_grade: "Заявленный уровень",
  years_of_experience: "Опыт",
  fsp_id: "FSP ID",
  personal_data_consent: "Согласие",
  skill_ids: "Навыки",
  company_name: "Компания",
  company_description: "Описание",
  website: "Сайт",
  contact_person_name: "Контактное лицо",
};
export function Feedback({
  error,
  success,
}: {
  error?: unknown;
  success?: string;
}) {
  return (
    <>
      {error != null && (
        <div role="alert" className="error">
          <p>{errorMessage(error)}</p>
          {error instanceof ApiError && error.fields.length > 0 && (
            <ul>
              {error.fields.map((field, i) => (
                <li key={i}>
                  {labels[field.field] ?? field.field}: {field.message}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {success && (
        <p role="status" className="success">
          {success}
        </p>
      )}
    </>
  );
}
