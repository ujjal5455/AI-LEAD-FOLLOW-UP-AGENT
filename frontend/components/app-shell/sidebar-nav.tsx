"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = { label: string; href?: string };

// Sections arrive milestone by milestone. Ones without a page yet are shown but disabled.
const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/dashboard" },
  { label: "Leads" },
  { label: "Conversations" },
  { label: "Follow-ups" },
  { label: "Simulator" },
  { label: "Settings" },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Main" className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
      {NAV_ITEMS.map((item) => {
        if (!item.href) {
          return (
            <span
              key={item.label}
              aria-disabled="true"
              className="flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium text-slate-400"
            >
              {item.label}
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                Soon
              </span>
            </span>
          );
        }
        const active = pathname === item.href;
        return (
          <Link
            key={item.label}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              active ? "bg-brand-50 text-brand-700" : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
