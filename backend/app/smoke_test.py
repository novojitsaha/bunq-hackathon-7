"""
Live integration smoke test.

Run this once after you've put your ANTHROPIC_API_KEY in `.env` to confirm
the three live Claude touchpoints work on your machine. Takes ~30 seconds
and ~2 cents of API credit.

    cd backend
    python -m app.smoke_test
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def main() -> int:
    settings = get_settings()
    if not settings.anthropic_api_key:
        print("FAIL: ANTHROPIC_API_KEY not set in .env or environment.")
        return 1

    failures: list[str] = []

    with TestClient(app) as client:
        print("=== /api/health ===")
        r = client.get("/api/health")
        print(f"  {r.status_code}  {r.json()}")
        if r.status_code != 200:
            failures.append("health")

        print("\n=== Seed demo + create goal ===")
        client.post("/api/settings/seed-demo")
        client.post(
            "/api/goals",
            json={"metric": "OUTSIDE_SCHIJF_SPEND", "reduction_percent": 20, "start_mode": "demo-immediate"},
        )
        print("  ok")

        print("\n=== Voice receipt (live Claude) ===")
        t0 = time.time()
        r = client.post(
            "/api/receipts/voice",
            json={"transcript": "I just got a Whopper menu at Burger King for 9 euros."},
        )
        print(f"  {r.status_code} in {time.time()-t0:.1f}s")
        if r.status_code == 200:
            body = r.json()
            print(f"  merchant={body['merchant_name']}  items={len(body['items'])}")
        else:
            failures.append("voice")
            print(f"  body: {r.text[:300]}")

        print("\n=== Agent loop (live Claude) ===")
        t0 = time.time()
        r = client.post("/api/agent/advise")
        print(f"  {r.status_code} in {time.time()-t0:.1f}s")
        if r.status_code == 200:
            plan = r.json()
            print(
                f"  fallback={plan['fallback']}  tool_calls={plan['tool_calls']}"
                f"  risk={plan['risk_level']}  swaps={len(plan['swaps'])}"
                f"  actions={len(plan['actions'])}"
            )
            if plan["fallback"]:
                failures.append("agent (fell back to deterministic plan)")
        else:
            failures.append("agent")
            print(f"  body: {r.text[:300]}")

    if failures:
        print(f"\nFAILED: {', '.join(failures)}")
        return 2

    print("\nAll live Claude paths working. You're good for the demo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
