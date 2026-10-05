import Link from "next/link";

export default function Home() {
  return (
    <section className="card">
      <h1>FSP Platform</h1>
      <p>
        Создайте аккаунт кандидата или работодателя и заполните свой профиль.
      </p>
      <div className="actions">
        <Link href="/register" className="button">
          Регистрация
        </Link>
        <Link href="/login">Войти</Link>
      </div>
    </section>
  );
}
