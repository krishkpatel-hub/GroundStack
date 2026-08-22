export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <svg
        aria-hidden
        className="h-6 w-6 shrink-0 text-[var(--accent)]"
        viewBox="0 0 24 24"
        fill="none"
      >
        <path
          d="M5 7.5h11.5l2.5 2.5H7.5L5 7.5Z"
          stroke="currentColor"
          strokeWidth="1.8"
        />
        <path
          d="M5 12h12.5l1.5 1.5H6.5L5 12Z"
          stroke="currentColor"
          strokeWidth="1.8"
        />
        <path
          d="M5 16.5h14"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="square"
        />
      </svg>
      {!compact && (
        <div>
          <div className="text-[1rem] font-semibold leading-5 tracking-normal">
            GroundStack
          </div>
          <div className="mt-0.5 text-xs leading-4 text-[var(--graphite)]">
            Knowledge workspace
          </div>
        </div>
      )}
    </div>
  );
}
