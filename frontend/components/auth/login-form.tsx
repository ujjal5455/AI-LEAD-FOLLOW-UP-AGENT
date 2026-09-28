"use client";

import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { TextField } from "@/components/ui/text-field";

import { useAuthSubmit } from "./use-auth-submit";

export function LoginForm() {
  const { onSubmit, error, submitting } = useAuthSubmit("/api/auth/login", [
    "email",
    "password",
  ]);

  return (
    <form onSubmit={onSubmit} className="mt-6 space-y-4">
      <FormError message={error} />
      <TextField label="Email" name="email" type="email" autoComplete="email" required />
      <TextField
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        required
      />
      <Button type="submit" className="w-full" disabled={submitting}>
        {submitting ? "Logging in…" : "Log in"}
      </Button>
    </form>
  );
}
