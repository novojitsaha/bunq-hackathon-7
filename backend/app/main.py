from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_bunq, routes_dashboard, routes_goals, routes_receipts, routes_settings, routes_transactions
from app.config import get_settings
from app.db import create_db_and_tables

settings = get_settings()

app = FastAPI(title="Bunq Bite Balance API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(routes_dashboard.router)
app.include_router(routes_receipts.router)
app.include_router(routes_goals.router)
app.include_router(routes_transactions.router)
app.include_router(routes_bunq.router)
app.include_router(routes_settings.router)

