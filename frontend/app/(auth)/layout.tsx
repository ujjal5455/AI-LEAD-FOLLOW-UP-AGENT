import { LogoMark } from "@/components/brand/logo";

// Shared frame for the login and sign-up pages. "(auth)" is a route group: the
// folder name organizes files without appearing in the URL.
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <LogoMark className="size-10" />
          <p className="mt-4 text-sm font-semibold tracking-tight text-slate-900">
            AI Lead Follow-Up Agent
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Reply to every lead in seconds, qualify them automatically, and never miss a
            follow-up.
          </p>
        </div>
        <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
          {children}
        </div>
      </div>
    </main>
  );
}
