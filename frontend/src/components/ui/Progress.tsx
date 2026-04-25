import { cn } from "../../lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 overflow-hidden rounded-full bg-ink/10", className)}>
      <div className="h-full rounded-full bg-mint transition-all" style={{ width: `${width}%` }} />
    </div>
  );
}

