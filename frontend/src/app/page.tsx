import Link from "next/link";

export default function Home() {
  return (
    <section className="card narrow auth-screen">
      <h1>Платформа ФСП</h1>
      <p>
        Создайте аккаунт кандидата или работодателя и заполните свой профиль.
      </p>
      <div className="actions">
        <Link href="/register" className="button">
          Регистрация
        </Link>
        <Link href="/login" className="button secondary">Войти</Link>
      </div>
    </section>
  );
}
