import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

import type { Session } from "@/types/api";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
export const SESSION_COOKIE = "access_token";

/**
 * Ask the backend who is logged in, using the browser's session cookie.
 * The backend is the only authority on sessions: this never trusts the cookie
 * by itself. Returns null when there is no valid session.
 * `cache` makes repeated calls during one page render hit the backend once.
 */
export const getSession = cache(async (): Promise<Session | null> => {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;

  const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
    headers: { Cookie: `${SESSION_COOKIE}=${token}` },
    cache: "no-store",
  });
  if (response.status === 401) return null;
  if (!response.ok) {
    throw new Error(`Session check failed (HTTP ${response.status})`);
  }
  return (await response.json()) as Session;
});

/** For pages that require login: returns the session or sends the visitor to /login. */
export async function requireSession(): Promise<Session> {
  const session = await getSession();
  if (!session) redirect("/login");
  return session;
}
