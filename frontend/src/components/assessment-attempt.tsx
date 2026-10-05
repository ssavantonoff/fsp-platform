"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/api";
import {
  applySavedAttempt,
  loadAttempt,
  saveAssessmentAnswer,
  secondsRemaining,
  submitAssessment,
  timerLabel,
} from "@/assessment";
import type { Attempt, ServerClock } from "@/assessment";
import { RoleGate } from "./auth";
import { Feedback } from "./feedback";
import { AssessmentQuestion } from "./assessment-question";
import { AssessmentResult } from "./assessment-result";

export function AssessmentAttemptScreen({ id }: { id: string }) {
  return (
    <RoleGate role="CANDIDATE">
      <AttemptContent id={id} />
    </RoleGate>
  );
}
function AttemptContent({ id }: { id: string }) {
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [clock, setClock] = useState<ServerClock | null>(null);
  const [left, setLeft] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [index, setIndex] = useState(0);
  const [saving, setSaving] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [saves, setSaves] = useState<
    Record<
      string,
      { option: string; state: "saving" | "saved" | "error"; error?: unknown }
    >
  >({});
  const timeoutRequested = useRef(false);
  const load = useCallback(
    () =>
      loadAttempt(id)
        .then((value) => {
          setAttempt(value.attempt);
          setClock(value.clock);
          setLeft(secondsRemaining(value.clock, performance.now()));
          setError(null);
        })
        .catch(setError)
        .finally(() => setLoading(false)),
    [id],
  );
  useEffect(() => {
    void load();
  }, [load]);
  const finish = useCallback(async () => {
    setFinishing(true);
    setError(null);
    try {
      setAttempt(await submitAssessment(id));
      setConfirm(false);
    } catch (err) {
      setError(err);
    } finally {
      setFinishing(false);
    }
  }, [id]);
  useEffect(() => {
    if (!clock || attempt?.status !== "IN_PROGRESS") return;
    const tick = () => {
      const remaining = secondsRemaining(clock, performance.now());
      setLeft(remaining);
      if (remaining === 0 && !timeoutRequested.current) {
        timeoutRequested.current = true;
        void finish();
      }
    };
    const timer = window.setInterval(tick, 250);
    tick();
    return () => window.clearInterval(timer);
  }, [clock, attempt?.status, finish]);
  async function save(questionId: string, optionId: string) {
    setSaving(true);
    setSaves((previous) => ({
      ...previous,
      [questionId]: { option: optionId, state: "saving" },
    }));
    try {
      const saved = await saveAssessmentAnswer(id, questionId, optionId);
      setAttempt((current) => applySavedAttempt(current, saved));
      setSaves((previous) => ({
        ...previous,
        [questionId]: { option: optionId, state: "saved" },
      }));
    } catch (err) {
      setSaves((previous) => ({
        ...previous,
        [questionId]: { option: optionId, state: "error", error: err },
      }));
      if (err instanceof ApiError && err.code === "assessment_finished")
        void load();
    } finally {
      setSaving(false);
    }
  }
  if (loading) return <p role="status">Загрузка теста…</p>;
  if (!attempt)
    return (
      <section className="card">
        <h1>Тестирование</h1>
        <Feedback error={error} />
        <button
          onClick={() => {
            setLoading(true);
            void load();
          }}
        >
          Повторить
        </button>
        <p>
          <Link href="/candidate/assessment">Выбор уровня</Link>
        </p>
      </section>
    );
  if (attempt.status !== "IN_PROGRESS")
    return (
      <AssessmentResult attempt={attempt} verification={attempt.verification} />
    );
  const question = attempt.questions[index];
  const state = saves[question.attempt_question_id];
  const unanswered = attempt.questions.filter(
    (q) => !q.selected_option_id,
  ).length;
  const unsaved = Object.values(saves).some((value) => value.state === "error");
  const blocked = saving || finishing || left === 0;
  return (
    <section className="card">
      <div className="assessment-top">
        <h1>
          Вопрос {index + 1} / {attempt.questions.length}
        </h1>
        <p
          className="assessment-timer"
          role="timer"
          aria-label="Осталось времени"
        >
          {timerLabel(left)}
        </p>
      </div>
      {left === 0 && (
        <p className="notice">
          Время вышло. Завершаем тест по сохранённым ответам.
        </p>
      )}
      <Feedback error={error} />
      {Boolean(error) && (
        <button disabled={finishing} onClick={() => void finish()}>
          Повторить завершение
        </button>
      )}
      <AssessmentQuestion
        question={question}
        selected={
          state?.state === "error" || state?.state === "saving"
            ? state.option
            : question.selected_option_id
        }
        disabled={blocked}
        onSelect={(option) => void save(question.attempt_question_id, option)}
      />
      <p role="status">
        {state?.state === "saving"
          ? "Сохраняем…"
          : state?.state === "error"
            ? "Не удалось сохранить"
            : question.selected_option_id
              ? "Ответ сохранён"
              : "Ответ пока не выбран"}
      </p>
      {state?.state === "error" && (
        <>
          <Feedback error={state.error} />
          <button
            className="secondary"
            disabled={blocked}
            onClick={() =>
              void save(question.attempt_question_id, state.option)
            }
          >
            Повторить сохранение
          </button>
        </>
      )}
      <div className="actions assessment-controls">
        <button
          className="secondary"
          disabled={index === 0 || finishing}
          onClick={() => setIndex(index - 1)}
        >
          Назад
        </button>
        {index < attempt.questions.length - 1 ? (
          <button
            className="secondary"
            disabled={finishing}
            onClick={() => setIndex(index + 1)}
          >
            Далее
          </button>
        ) : (
          <button disabled={blocked} onClick={() => setConfirm(true)}>
            Завершить тест
          </button>
        )}
      </div>
      <nav className="question-navigator" aria-label="Навигация по вопросам">
        {attempt.questions.map((q, position) => (
          <button
            key={q.attempt_question_id}
            className={`question-number ${position === index ? "current" : q.selected_option_id ? "answered" : "unanswered"}`}
            aria-current={position === index ? "step" : undefined}
            aria-label={`Вопрос ${position + 1}, ${q.selected_option_id ? "ответ сохранён" : "без ответа"}`}
            disabled={finishing}
            onClick={() => setIndex(position)}
          >
            {position + 1}
          </button>
        ))}
      </nav>
      <p className="hint">
        Синий — текущий вопрос; зелёный — ответ сохранён; белый — без ответа.
        Таймер продолжает идти при закрытии страницы.
      </p>
      {confirm && (
        <div
          className="notice"
          role="region"
          aria-label="Подтверждение завершения"
        >
          <h2>Завершить тест?</h2>
          {unanswered > 0 && <p>У вас {unanswered} вопросов без ответа.</p>}
          {unsaved && (
            <p>
              Есть несохранённые изменения. В результат войдут только ответы,
              сохранённые на сервере.
            </p>
          )}
          <p>После завершения изменить ответы нельзя.</p>
          <div className="actions">
            <button
              className="secondary"
              disabled={finishing}
              onClick={() => setConfirm(false)}
            >
              Вернуться к вопросам
            </button>
            <button disabled={blocked} onClick={() => void finish()}>
              {finishing ? "Завершаем…" : "Завершить тест"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
