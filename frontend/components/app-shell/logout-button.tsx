"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api-client";

export function LogoutButton({ className = "" }: { className?: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  async function logout() {
    setPending(true);
    setFailed(false);
    try {
      await apiPost("/api/auth/logout");
      router.replace("/login");
      router.refresh();
    } catch {
      setFailed(true);
      setPending(false);
    }
  }

  return (
    <Button
      variant="secondary"
      className={className}
      onClick={logout}
      disabled={pending}
      title={failed ? "Couldn't sign out. Please try again." : undefined}
    >
      {failed ? "Retry sign out" : pending ? "Signing out…" : "Sign out"}
    </Button>
  );
}
