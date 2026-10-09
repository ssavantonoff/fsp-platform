"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/api";
import type { Page } from "@/employer-needs";
import { Feedback } from "./feedback";

export function useInvitationPage<T extends { id: string }>(fetchPage: (offset: number) => Promise<Page<T>>) {
  const [page, setPage] = useState<Page<T> | null>(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const pending = useRef(false);
  const generation = useRef(0);
  const mounted = useRef(true);
  const load = useCallback(() => {
    const request = ++generation.current;
    return fetchPage(offset).then((result) => {
      if (request === generation.current) { setPage(result); setError(null); }
    }).catch((err: unknown) => {
      if (request === generation.current) { setError(err); setPage(null); }
    }).finally(() => {
      if (request === generation.current) setLoading(false);
    });
  }, [fetchPage, offset]);
  useEffect(() => {
    mounted.current = true;
    const requests = generation;
    void load();
    return () => { mounted.current = false; requests.current++; };
  }, [load]);
  function retry() { setLoading(true); setError(null); void load(); }
  function changePage(next: number) {
    if (pending.current) return;
    generation.current++;
    setLoading(true); setError(null); setActionError(null); setSuccess(""); setPage(null); setOffset(next);
  }
  async function mutate(id: string, operation: () => Promise<T>, feedback: string): Promise<boolean> {
    if (pending.current) return false;
    pending.current = true;
    const request = ++generation.current;
    setBusyId(id); setActionError(null); setSuccess("");
    try {
      const saved = await operation();
      if (request !== generation.current) return false;
      setPage((current) => current ? { ...current, items: current.items.map((item) => item.id === saved.id ? saved : item) } : current);
      setSuccess(feedback);
      return true;
    } catch (err) {
      if (request !== generation.current) return false;
      setActionError(err);
      if (err instanceof ApiError && err.code === "invitation_state_conflict") {
        // Keep the conflict visible; a fresh GET determines the winning state.
        setLoading(true);
        await load();
      }
      return false;
    } finally {
      pending.current = false;
      if (mounted.current) setBusyId(null);
    }
  }
  return { page: page?.offset === offset ? page : null, offset, loading, error, actionError, success, busyId, retry, changePage, mutate };
}
export function InvitationListState({ loading, error, empty, onRetry }: {
  loading: boolean; error: unknown; empty: boolean; onRetry: () => void;
}) {
  if (loading) return <section className="card workflow-list-state"><p role="status">Загрузка приглашений…</p></section>;
  if (error != null) return <section className="card workflow-list-state"><Feedback error={error} /><button onClick={onRetry}>Повторить</button></section>;
  return empty ? <section className="card workflow-list-state"><p>Приглашений пока нет.</p></section> : null;
}
export function InvitationPagination({ page, loading, busy, onPageChange }: {
  page: Page<{ id: string }> | null; loading: boolean; busy: boolean; onPageChange: (offset: number) => void;
}) {
  if (!page) return null;
  return <div className="actions need-pagination" aria-label="Страницы приглашений">
    <button className="secondary" disabled={loading || busy || page.offset <= 0} onClick={() => onPageChange(Math.max(0, page.offset - page.limit))}>Назад</button>
    <span>Всего: {page.total}</span>
    <button className="secondary" disabled={loading || busy || page.offset + page.items.length >= page.total} onClick={() => onPageChange(page.offset + page.limit)}>Далее</button>
  </div>;
}
