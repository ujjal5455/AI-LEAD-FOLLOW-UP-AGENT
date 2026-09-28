import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { LoginForm } from "@/components/auth/login-form";
import { getSession } from "@/lib/session";

export const metadata: Metadata = { title: "Log in" };

export default async function LoginPage() {
  if (await getSession()) redirect("/dashboard");

  return (
    <>
      <h1 className="text-lg font-semibold text-slate-900">Log in</h1>
      <p className="mt-1 text-sm text-slate-600">Welcome back. See what your leads are up to.</p>
      <LoginForm />
      <p className="mt-6 text-center text-sm text-slate-600">
        New here?{" "}
        <Link href="/register" className="font-medium text-brand-700 hover:text-brand-800">
          Create an account
        </Link>
      </p>
    </>
  );
}
