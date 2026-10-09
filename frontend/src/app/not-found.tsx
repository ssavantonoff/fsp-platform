import Link from "next/link";
export default function NotFound() {
  return (
    <section className="card narrow auth-screen">
      <h1>Страница не найдена</h1>
      <p>Проверьте адрес или вернитесь на главную страницу.</p>
      <Link href="/" className="button secondary">На главную</Link>
    </section>
  );
}
