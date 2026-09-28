"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { apiPost } from "@/lib/api-client";
import type { Session } from "@/types/api";

/**
 * Shared submit logic for the login and sign-up forms: post the form fields to the
 * backend, and on success go to the dashboard. The backend sets the session cookie
 * on its response, so there is no token for this code to store or handle.
 */
export function useAuthSubmit(endpoint: string, fields: readonly string[]) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = Object.fromEntries(fields.map((field) => [field, form.get(field)]));

    setSubmitting(true);
    setError(null);
    try {
      await apiPost<Session>(endpoint, body);
      router.replace("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setSubmitting(false);
    }
  }

  return { onSubmit, error, submitting };
}
