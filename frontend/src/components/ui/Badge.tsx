import type { HTMLAttributes } from "react";

import type { Classification } from "../../lib/types";
import { classificationLabel } from "../../lib/format";
import { cn } from "../../lib/utils";

const styles: Record<Classification, string> = {
  IN_SCHIJF: "bg-mint/15 text-green-800",
  DAGKEUZE: "bg-amber/20 text-amber-900",
  WEEKKEUZE: "bg-coral/15 text-red-800",
  UNKNOWN: "bg-berry/15 text-berry",
  NON_FOOD: "bg-ink/10 text-ink/70",
};

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold leading-none", className)}
      {...props}
    />
  );
}

export function ClassificationBadge({ value }: { value: Classification }) {
  return <Badge className={styles[value]}>{classificationLabel(value)}</Badge>;
}

