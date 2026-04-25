import type { Classification } from "./types";

export function eur(value: number | null | undefined) {
  return new Intl.NumberFormat("en-NL", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value ?? 0);
}

export function kcal(value: number | null | undefined) {
  return `${Math.round(value ?? 0).toLocaleString("en-NL")} kcal`;
}

export function pct(value: number | null | undefined) {
  return `${Math.round((value ?? 0) * 100)}%`;
}

export function dateLabel(value: string | null | undefined) {
  if (!value) return "No date";
  return new Intl.DateTimeFormat("en-NL", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
}

export function classificationLabel(value: Classification) {
  switch (value) {
    case "IN_SCHIJF":
      return "Schijf";
    case "DAGKEUZE":
      return "Dagkeuze";
    case "WEEKKEUZE":
      return "Weekkeuze";
    case "NON_FOOD":
      return "Non-food";
    default:
      return "Check";
  }
}

