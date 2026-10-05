"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <section className="card" role="alert">
      <h1>Не удалось открыть страницу</h1>
      <p>Повторите попытку.</p>
      <button onClick={reset}>Повторить</button>
    </section>
  );
}
