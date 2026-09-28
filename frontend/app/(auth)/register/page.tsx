import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { RegisterForm } from "@/components/auth/register-form";
import { getSession } from "@/lib/session";

export const metadata: Metadata = { title: "Create account" };

export default async function RegisterPage() {
  if (await getSession()) redirect("/dashboard");

  return (
    <>
      <h1 className="text-lg font-semibold text-slate-900">Create your account</h1>
      <p className="mt-1 text-sm text-slate-600">
        Set up your business and start capturing leads.
      </p>
      <RegisterForm />
      <p className="mt-6 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-brand-700 hover:text-brand-800">
          Log in
        </Link>
      </p>
    </>
  );
}
