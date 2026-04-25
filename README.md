# Bunq Bite Balance

Hackathon MVP for linking bunq food payments with receipt-level multimodal extraction, nutrition enrichment, Schijf-style classification, monthly analytics, and reduction goals.

## What Is Implemented

- FastAPI backend with SQLite persistence, SQLModel tables, demo seed/reset, dashboard/monthly metrics, receipt review/confirm flow, goals, transactions, bunq webhook shape, and fixture-safe OpenAI/Open Food Facts service boundaries.
- React/Vite frontend with dashboard, scan/upload, receipt review, instant summary, monthly summary, goals, transactions, and settings pages.
- Offline demo mode by default. Upload filenames containing `junk`, `ah`, or `albert` use the Albert Heijn fixture; filenames containing `fast`, `burger`, or `king` use the fast-food fixture; other names use the Lidl healthy fixture.

## Start Backend

```powershell
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000/api/health`.

## Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

The app is available at `http://127.0.0.1:5173`.

## Demo Flow

1. Open Settings and click `Seed demo`.
2. Open Dashboard to see monthly calories/spend, bunq-like transactions, and purchases.
3. Open Scan and upload any image/PDF. Name it `junk-receipt.jpg`, `fast-food.jpg`, or any other name to choose the fixture.
4. Review line items, deselect an item, and confirm.
5. Open Monthly and Goals to show top Outside-Schijf contributors and a reduction goal.

## Verification

```powershell
cd backend
uv run pytest

cd ..\frontend
npm run build
```

## Live Integration Notes

- OpenAI live receipt extraction is enabled only when `OPENAI_API_KEY` and `OPENAI_MODEL_RECEIPT` are set.
- Open Food Facts live search is enabled only when `OPEN_FOOD_FACTS_LIVE=true`; requests use `OPEN_FOOD_FACTS_USER_AGENT`.
- bunq sync currently seeds deterministic demo transactions when `BUNQ_API_KEY` is absent. The wrapper and webhook endpoint are in place for adapting the hackathon toolkit.

