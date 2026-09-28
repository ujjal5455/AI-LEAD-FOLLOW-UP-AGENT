"use client"; // Error boundaries must be Client Components

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function Error({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 py-16 text-center">
      <h1 className="text-lg font-semibold">Something went wrong</h1>
      <p className="mt-2 max-w-md text-sm text-slate-600">
        This page couldn&apos;t be loaded. If you&apos;re running the app locally, check that
        the backend is running on port 8000.
      </p>
      <Button className="mt-6" variant="secondary" onClick={() => retry()}>
        Try again
      </Button>
    </main>
  );
}
