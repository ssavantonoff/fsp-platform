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

type AnswerSaves = Record<
  string,
  { option: string; state: "saving" | "saved" | "error"; error?: unknown }
>;

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
  const [saves, setSaves] = useState<AnswerSaves>({});
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
  return <AssessmentAttemptView
    attempt={attempt}
    left={left}
    loading={loading}
    error={error}
    index={index}
    saves={saves}
    saving={saving}
    finishing={finishing}
    confirm={confirm}
    onRetry={() => {
      setLoading(true);
      void load();
    }}
    onFinish={() => void finish()}
    onSave={(questionId, optionId) => void save(questionId, optionId)}
    onIndexChange={setIndex}
    onConfirmChange={setConfirm} />;
}

export function AssessmentAttemptView({ attempt, left, loading, error, index, saves, saving, finishing, confirm, onRetry, onFinish, onSave, onIndexChange, onConfirmChange }: {
  attempt: Attempt | null;
  left: number;
  loading: boolean;
  error: unknown;
  index: number;
  saves: AnswerSaves;
  saving: boolean;
  finishing: boolean;
  confirm: boolean;
  onRetry: () => void;
  onFinish: () => void;
  onSave: (questionId: string, optionId: string) => void;
  onIndexChange: (index: number) => void;
  onConfirmChange: (confirm: boolean) => void;
}) {
  if (loading) return <p className="assessment-loading" role="status">Загрузка теста…</p>;
  if (!attempt)
    return (
      <section className="card assessment-screen">
        <h1>Тестирование</h1>
        <Feedback error={error} />
        <button onClick={onRetry}>
          Повторить
        </button>
        <p>
          <Link className="button secondary" href="/candidate/assessment">Выбор уровня</Link>
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
  const answered = attempt.questions.length - unanswered;
  return (
    <section className="card assessment-screen assessment-question-screen">
      <div className="assessment-top">
        <div>
          <p className="eyebrow">Assessment</p>
          <h1>Вопрос {index + 1} / {attempt.questions.length}</h1>
        </div>
        <div className="assessment-timer">
          <span>Осталось времени</span>
          <strong role="timer" aria-label="Осталось времени" aria-live="off">{timerLabel(left)}</strong>
        </div>
      </div>
      <div className="assessment-progress">
        <p>Ответы сохранены: <strong>{answered} из {attempt.questions.length}</strong></p>
        <progress value={answered} max={attempt.questions.length} aria-label="Сохранённые ответы" />
      </div>
      {left === 0 && (
        <p className="notice">
          Время вышло. Завершаем тест по сохранённым ответам.
        </p>
      )}
      <Feedback error={error} />
      {Boolean(error) && (
        <button disabled={finishing} onClick={onFinish}>
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
        onSelect={(option) => onSave(question.attempt_question_id, option)}
      />
      <p className="assessment-save" data-state={state?.state ?? (question.selected_option_id ? "saved" : "unanswered")} role="status">
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
            onClick={() => onSave(question.attempt_question_id, state.option)}
          >
            Повторить сохранение
          </button>
        </>
      )}
      <div className="actions assessment-controls">
        <button
          className="secondary"
          disabled={index === 0 || finishing}
          onClick={() => onIndexChange(index - 1)}
        >
          Назад
        </button>
        {index < attempt.questions.length - 1 ? (
          <button
            className="secondary"
            disabled={finishing}
            onClick={() => onIndexChange(index + 1)}
          >
            Далее
          </button>
        ) : (
          <button disabled={blocked} onClick={() => onConfirmChange(true)}>
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
            onClick={() => onIndexChange(position)}
          >
            {position + 1}
            {q.selected_option_id && <span className="question-saved-marker" aria-hidden="true"> ✓</span>}
          </button>
        ))}
      </nav>
      <p className="hint">
        Галочка — ответ сохранён. Выделенный номер — текущий вопрос.
        Таймер продолжает идти при закрытии страницы.
      </p>
      {confirm && (
        <div
          className="notice assessment-confirm"
          role="region"
          aria-label="Подтверждение завершения"
        >
          <h2>Завершить тест?</h2>
          {unanswered > 0 && <p>Вопросов без ответа: {unanswered}.</p>}
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
              onClick={() => onConfirmChange(false)}
            >
              Вернуться к вопросам
            </button>
            <button disabled={blocked} onClick={onFinish}>
              {finishing ? "Завершаем…" : "Завершить тест"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
