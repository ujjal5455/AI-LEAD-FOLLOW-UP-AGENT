import { LogoMark } from "@/components/brand/logo";
import type { Session } from "@/types/api";

import { LogoutButton } from "./logout-button";
import { SidebarNav } from "./sidebar-nav";

export function AppShell({ session, children }: { session: Session; children: React.ReactNode }) {
  const { user, business } = session;

  return (
    <div className="flex min-h-full flex-1">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white md:sticky md:top-0 md:flex md:h-screen">
        <div className="flex h-16 items-center gap-2.5 px-5">
          <LogoMark className="size-8" />
          <span className="text-sm font-semibold tracking-tight">Lead Follow-Up Agent</span>
        </div>
        <SidebarNav />
        <div className="border-t border-slate-200 p-4">
          <p className="truncate text-sm font-medium text-slate-900">{business.name}</p>
          <p className="truncate text-xs text-slate-500">{user.email}</p>
          <LogoutButton className="mt-3 w-full" />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 md:hidden">
          <div className="flex min-w-0 items-center gap-2">
            <LogoMark className="size-7" />
            <span className="truncate text-sm font-semibold">{business.name}</span>
          </div>
          <LogoutButton />
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
