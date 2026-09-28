"use client";

import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { TextField } from "@/components/ui/text-field";

import { useAuthSubmit } from "./use-auth-submit";

export function RegisterForm() {
  const { onSubmit, error, submitting } = useAuthSubmit("/api/auth/register", [
    "full_name",
    "business_name",
    "email",
    "password",
  ]);

  return (
    <form onSubmit={onSubmit} className="mt-6 space-y-4">
      <FormError message={error} />
      <TextField label="Your name" name="full_name" autoComplete="name" required maxLength={120} />
      <TextField
        label="Business name"
        name="business_name"
        autoComplete="organization"
        placeholder="e.g. ABC Interiors"
        required
        maxLength={200}
      />
      <TextField label="Work email" name="email" type="email" autoComplete="email" required />
      <TextField
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        hint="At least 8 characters."
        required
        minLength={8}
        maxLength={128}
      />
      <Button type="submit" className="w-full" disabled={submitting}>
        {submitting ? "Creating your account…" : "Create account"}
      </Button>
    </form>
  );
}
