import type { Metadata } from "next";

import { requireSession } from "@/lib/session";

export const metadata: Metadata = { title: "Overview" };

type SetupStep = { title: string; description: string; done: boolean };

export default async function DashboardPage() {
  const { user, business } = await requireSession();
  const firstName = user.full_name?.split(" ")[0];

  const steps: SetupStep[] = [
    {
      title: "Create your account",
      description: `Signed in as ${user.email}.`,
      done: true,
    },
    {
      title: "Add your business",
      description: `${business.name} is set up.`,
      done: true,
    },
    {
      title: "Describe what you sell",
      description:
        "Services, service area, pricing and hours, so the assistant answers from facts, never guesses.",
      done: false,
    },
    {
      title: "Try a test conversation",
      description: "Message your assistant as if you were a customer and watch it qualify you.",
      done: false,
    },
    {
      title: "Connect WhatsApp",
      description: "Let the assistant reply to real customers the moment they message.",
      done: false,
    },
  ];
  const completed = steps.filter((step) => step.done).length;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome{firstName ? `, ${firstName}` : ""}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {business.name} · Times shown in {business.timezone}
        </p>
      </header>

      <section
        aria-labelledby="setup-heading"
        className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
      >
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="setup-heading" className="text-base font-semibold">
            Get your assistant ready
          </h2>
          <p className="text-sm text-slate-500">
            {completed} of {steps.length} done
          </p>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-600"
            style={{ width: `${(completed / steps.length) * 100}%` }}
          />
        </div>

        <ol className="mt-6 space-y-5">
          {steps.map((step, index) => (
            <li key={step.title} className="flex gap-3">
              <StepMarker done={step.done} number={index + 1} />
              <div className="min-w-0">
                <p
                  className={`text-sm font-medium ${step.done ? "text-slate-500" : "text-slate-900"}`}
                >
                  {step.title}
                  {step.done && <span className="sr-only"> (done)</span>}
                </p>
                <p className="mt-0.5 text-sm text-slate-500">{step.description}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function StepMarker({ done, number }: { done: boolean; number: number }) {
  if (done) {
    return (
      <span
        aria-hidden="true"
        className="flex size-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="size-3.5">
          <path
            fillRule="evenodd"
            d="M16.7 5.3a1 1 0 0 1 0 1.4l-8 8a1 1 0 0 1-1.4 0l-4-4a1 1 0 1 1 1.4-1.4L8 12.58l7.3-7.3a1 1 0 0 1 1.4 0Z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    );
  }
  return (
    <span
      aria-hidden="true"
      className="flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-medium text-slate-500 ring-1 ring-slate-300"
    >
      {number}
    </span>
  );
}
