export function LogoMark({ className = "size-8" }: { className?: string }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-lg bg-brand-600 text-white ${className}`}
      aria-hidden="true"
    >
      {/* A chat bubble with a tick: every lead answered. */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="size-[60%]"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        <path d="m9 10 2 2 4-4" />
      </svg>
    </span>
  );
}
