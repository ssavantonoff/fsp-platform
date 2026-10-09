"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { api, ApiError, errorMessage } from "@/api";
import { needsNavigationVisible } from "@/employer-needs";
import type { Role, User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
}
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const refresh = useCallback(
    () =>
      api<User>("/auth/me")
        .then((current) => {
          setUser(current);
          setError("");
        })
        .catch((err) => {
          setUser(null);
          setError(
            err instanceof ApiError && err.status === 401
              ? ""
              : errorMessage(err),
          );
        })
        .finally(() => setLoading(false)),
    [],
  );
  useEffect(() => {
    void refresh();
  }, [refresh]);
  return (
    <AuthContext.Provider value={{ user, loading, error, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("AuthProvider is missing");
  return auth;
}

export function Header() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function logout() {
    setBusy(true);
    setError("");
    try {
      await api<void>("/auth/logout", { method: "POST" });
      await refresh();
      router.push("/login");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <header className="site-header">
      <nav aria-label="Основная навигация">
        <Link href="/" className="brand" aria-label="ФСП — платформа ИТ-подбора">
          <Image className="brand-full" src="/brand/fsp-full-dark.svg" width={1232} height={154} alt="Федерация спортивного программирования России" priority />
          <Image className="brand-compact" src="/brand/fsp-compact-dark.svg" width={599} height={202} alt="" aria-hidden="true" priority />
          <span className="brand-caption">Платформа ИТ-подбора</span>
        </Link>
        <div className="nav-links">
          {!loading &&
            (user ? (
              <>
                <Link
                  href={user.role === "CANDIDATE" ? "/candidate" : "/employer"}
                  aria-current={pathname === "/candidate" || pathname === "/candidate/edit" || pathname === "/employer" || pathname === "/employer/edit" ? "page" : undefined}
                >
                  Мой профиль
                </Link>
                {needsNavigationVisible(user.role) && (
                  <Link href="/employer/needs" aria-current={pathname.startsWith("/employer/needs") ? "page" : undefined}>Потребности</Link>
                )}
                {user.role === "CANDIDATE" && <Link href="/candidate/invitations" aria-current={pathname === "/candidate/invitations" ? "page" : undefined}>Приглашения от работодателей</Link>}
                <button className="secondary" disabled={busy} onClick={logout}>
                  {busy ? "Выходим…" : "Выйти"}
                </button>
              </>
            ) : (
              <>
                <Link href="/login" aria-current={pathname === "/login" ? "page" : undefined}>Вход</Link>
                <Link href="/register" aria-current={pathname === "/register" ? "page" : undefined}>Регистрация</Link>
              </>
            ))}
        </div>
      </nav>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </header>
  );
}

export function RoleGate({
  role,
  children,
}: {
  role: Role;
  children: React.ReactNode;
}) {
  const { user, loading, error, refresh } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && !error) {
      if (!user) router.replace("/login");
      else if (user.role !== role)
        router.replace(user.role === "CANDIDATE" ? "/candidate" : "/employer");
    }
  }, [user, loading, error, role, router]);
  if (loading) return <p role="status">Загрузка аккаунта…</p>;
  if (error)
    return (
      <div role="alert">
        <p className="error">{error}</p>
        <button onClick={() => void refresh()}>Повторить</button>
      </div>
    );
  if (!user || user.role !== role) return <p role="status">Переходим…</p>;
  return (
    <>
      {!user.email_verified && (
        <aside className="notice">
          Email пока не подтверждён. Откройте ссылку из письма. В локальной
          среде ссылка находится в журнале backend.{" "}
          <Link href="/verify-email">Подтверждение email</Link>
        </aside>
      )}
      {children}
    </>
  );
}
