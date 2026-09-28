import { AppShell } from "@/components/app-shell/app-shell";
import { requireSession } from "@/lib/session";

// Every page in the "(dashboard)" group requires login. Visitors without a valid
// session are redirected to /login before anything renders. The backend still
// checks the session on every API call; this redirect is for a smooth experience,
// not the security boundary.
export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();
  return <AppShell session={session}>{children}</AppShell>;
}
