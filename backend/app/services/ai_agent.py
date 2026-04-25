"""
ai_agent.py
===========

The "agent" that answers the multimodal-AI-that-*acts* requirement of the
hackathon brief. Given the user's current dashboard state, Claude:

  1. inspects the data using read-only tools (`get_outside_schijf_summary`,
     `get_top_offenders`, `get_goal_status`, `list_recent_food_transactions`),
  2. reasons about whether the user is on track or drifting,
  3. produces a concrete plan: a personalised tip, a cheaper-and-healthier
     swap suggestion, and (when the goal is at risk) a proposed money move
     into a "Schijf Buffer" savings sub-account on bunq.

The plan is returned as structured data the frontend can render. Money never
moves automatically — actions are *proposed*; the user clicks "Confirm" in
the UI to actually execute.

The bunq side-effect tools (e.g. `propose_savings_transfer`) write to a small
in-DB queue (the `AgentAction` table) rather than calling bunq directly. The
queue is then consumed by `routes_agent.py:execute_action`, which is the only
place that touches the bunq SDK and is gated on `BUNQ_LIVE_WRITE=true`.

That separation matters because:
  - Claude decides the strategy. The user authorises the side effect.
  - Tool-use latency is hidden behind a "I'll prepare a plan…" spinner; the
    actual money move (if any) happens on a separate explicit click.

The pattern is the standard Anthropic agent loop documented at
https://docs.claude.com/en/docs/build-with-claude/tool-use — request →
look at tool_use blocks → run tools → feed tool_result blocks back → repeat
until stop_reason="end_turn".
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, date
from typing import Any

import anthropic
from sqlmodel import Session, select

from app.config import Settings, get_settings
from app.models import (
    Classification,
    Goal,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
    Transaction,
)
from app.services.metrics import (
    elapsed_days_in_month,
    mtd_splits,
    top_merchants_by_outside_spend,
    top_outside_items,
    unmatched_food_transactions,
)
from app.services.goals import active_goal

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plan shape — what we hand back to the API caller
# ---------------------------------------------------------------------------

@dataclass
class ProposedAction:
    """A concrete action the user can confirm with one click."""

    kind: str  # 'savings_transfer' | 'spending_alert' | 'swap_suggestion'
    title: str
    description: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPlan:
    summary: str
    risk_level: str  # on_track | watch | over_target
    headline_number: str
    tip: str
    swaps: list[dict[str, Any]] = field(default_factory=list)
    actions: list[ProposedAction] = field(default_factory=list)
    reasoning: str = ""  # human-readable trace for the demo
    tool_calls: int = 0
    fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "risk_level": self.risk_level,
            "headline_number": self.headline_number,
            "tip": self.tip,
            "swaps": self.swaps,
            "actions": [
                {"kind": a.kind, "title": a.title, "description": a.description, "payload": a.payload}
                for a in self.actions
            ],
            "reasoning": self.reasoning,
            "tool_calls": self.tool_calls,
            "fallback": self.fallback,
        }


# ---------------------------------------------------------------------------
# Read-only inspection tools (Claude calls these to understand context)
# ---------------------------------------------------------------------------

def _build_read_tools(session: Session) -> list[dict[str, Any]]:
    """The schema list passed to Claude. Implementations live in _dispatch."""
    return [
        {
            "name": "get_outside_schijf_summary",
            "description": (
                "Get the user's month-to-date totals for calories and spend, broken "
                "down by Schijf van Vijf classification (in_schijf, dagkeuze, "
                "weekkeuze). Outside-Schijf = dagkeuze + weekkeuze."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_goal_status",
            "description": (
                "Get the user's currently active reduction goal (target value, "
                "current value, percent of budget used). Returns null if no "
                "active goal."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_top_offenders",
            "description": (
                "Get the highest-cost or highest-calorie items in the "
                "outside-Schijf category, plus the merchants where the user "
                "spends the most outside Schijf."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "sort_by": {
                        "type": "string",
                        "enum": ["calories_total", "total_price"],
                        "default": "total_price",
                        "description": "Which dimension to sort items by.",
                    },
                    "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "list_unmatched_food_transactions",
            "description": (
                "List recent bunq food/restaurant transactions that don't yet "
                "have a matched receipt — these are gaps in the user's data."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "propose_savings_transfer",
            "description": (
                "Propose moving money from the main account to a 'Schijf "
                "Buffer' savings sub-account. Use ONLY when the user is on "
                "track to exceed their reduction goal — to commit savings "
                "they would otherwise have spent on outside-Schijf items. "
                "This does NOT move money; it queues a proposal the user "
                "must confirm in the UI."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "amount_eur": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 200,
                        "description": "Amount to transfer in EUR. Keep it small (€5–€50) and proportional to the gap.",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "One short sentence the user will see explaining why.",
                    },
                },
                "required": ["amount_eur", "rationale"],
                "additionalProperties": False,
            },
        },
        {
            "name": "propose_swap",
            "description": (
                "Suggest a concrete healthier-and-cheaper swap for one of the "
                "user's most-bought outside-Schijf items. Provide the original "
                "item, the suggested alternative, and the projected weekly/monthly "
                "calorie + spend delta."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "from_item": {"type": "string", "description": "Original outside-Schijf item, e.g. 'Red Bull'."},
                    "to_item": {"type": "string", "description": "Suggested swap, e.g. 'Lipton Ice Tea Zero'."},
                    "rationale": {"type": "string", "description": "One sentence — why this swap."},
                    "monthly_eur_saved": {"type": "number", "minimum": 0},
                    "monthly_kcal_saved": {"type": "number", "minimum": 0},
                },
                "required": ["from_item", "to_item", "rationale"],
                "additionalProperties": False,
            },
        },
        {
            "name": "finalize_plan",
            "description": (
                "Submit the final advisory plan — your reasoning and "
                "user-facing summary. Call this exactly once at the end after "
                "you have inspected the data and decided on any swaps or "
                "transfers. After this tool you should stop."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Two short sentences of context for the user, in plain English. Avoid medical or financial advice phrasing.",
                    },
                    "headline_number": {
                        "type": "string",
                        "description": "One memorable number, e.g. '€18.50 Outside Schijf this month' or '63% of weekly budget used'.",
                    },
                    "tip": {
                        "type": "string",
                        "description": "One concrete actionable tip, max 20 words.",
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["on_track", "watch", "over_target"],
                    },
                },
                "required": ["summary", "headline_number", "tip", "risk_level"],
                "additionalProperties": False,
            },
        },
    ]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def _dispatch_tool(
    session: Session,
    tool_name: str,
    tool_input: dict[str, Any],
    plan: AgentPlan,
) -> Any:
    """Execute a tool by name. Read-only tools return data; side-effect tools
    append a ProposedAction to the plan (the user confirms in the UI)."""

    if tool_name == "get_outside_schijf_summary":
        today = datetime.now(UTC).date()
        cal, spend = mtd_splits(session, today)
        elapsed = elapsed_days_in_month(today)
        return {
            "month": today.strftime("%Y-%m"),
            "elapsed_days": elapsed,
            "calories": {
                "in_schijf": cal.in_schijf,
                "outside_schijf": cal.outside_schijf,
                "total": cal.total,
            },
            "spend_eur": {
                "in_schijf": spend.in_schijf,
                "outside_schijf": spend.outside_schijf,
                "total": spend.total,
            },
            "avg_daily_kcal": round(cal.total / elapsed, 1) if elapsed else 0.0,
        }

    if tool_name == "get_goal_status":
        goal = active_goal(session)
        if goal is None:
            return {"active_goal": None}
        today = datetime.now(UTC).date()
        cal, spend = mtd_splits(session, today)
        if goal.metric == "OUTSIDE_SCHIJF_SPEND":
            current = spend.outside_schijf
        else:
            current = cal.outside_schijf
        used_pct = round(current / goal.target_value, 3) if goal.target_value else 0.0
        return {
            "active_goal": {
                "metric": goal.metric.value if hasattr(goal.metric, "value") else str(goal.metric),
                "reduction_percent": goal.reduction_percent,
                "baseline": goal.baseline_value,
                "target": goal.target_value,
                "current": round(current, 2),
                "budget_used_pct": used_pct,
            }
        }

    if tool_name == "get_top_offenders":
        sort_by = tool_input.get("sort_by", "total_price")
        limit = int(tool_input.get("limit", 5))
        items = top_outside_items(session, sort_by, limit)
        merchants = top_merchants_by_outside_spend(session, limit)
        return {
            "items": [
                {
                    "name": it.normalized_name or it.raw_name,
                    "calories": it.calories_total,
                    "price_eur": it.total_price,
                    "classification": it.classification.value if hasattr(it.classification, "value") else str(it.classification),
                    "confidence": round(it.confidence, 2),
                }
                for it in items
            ],
            "merchants": merchants,
        }

    if tool_name == "list_unmatched_food_transactions":
        txs = unmatched_food_transactions(session, limit=5)
        return [
            {
                "merchant": t.merchant_name,
                "amount_eur": abs(t.amount),
                "date": t.payment_date.isoformat() if t.payment_date else None,
                "category": t.merchant_category.value if hasattr(t.merchant_category, "value") else str(t.merchant_category),
            }
            for t in txs
        ]

    if tool_name == "propose_savings_transfer":
        amount = float(tool_input["amount_eur"])
        rationale = str(tool_input["rationale"])
        plan.actions.append(ProposedAction(
            kind="savings_transfer",
            title=f"Move €{amount:.2f} into your Schijf Buffer",
            description=rationale,
            payload={"amount_eur": amount, "currency": "EUR", "to_account": "Schijf Buffer"},
        ))
        return {"queued": True, "amount_eur": amount}

    if tool_name == "propose_swap":
        plan.swaps.append({
            "from": tool_input["from_item"],
            "to": tool_input["to_item"],
            "rationale": tool_input["rationale"],
            "monthly_eur_saved": float(tool_input.get("monthly_eur_saved") or 0),
            "monthly_kcal_saved": float(tool_input.get("monthly_kcal_saved") or 0),
        })
        return {"queued": True}

    if tool_name == "finalize_plan":
        plan.summary = tool_input["summary"]
        plan.headline_number = tool_input["headline_number"]
        plan.tip = tool_input["tip"]
        plan.risk_level = tool_input["risk_level"]
        return {"finalized": True}

    raise ValueError(f"Unknown tool: {tool_name}")


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM = """You are the financial-and-nutrition coach inside Bunq Bite Balance.

Your job: look at the user's month-to-date food spending and Schijf van Vijf
breakdown, then produce a short, concrete advisory plan.

The Schijf van Vijf is the official Dutch dietary framework:
  - "in_schijf"  = staple healthy basics (whole grains, vegetables, fruit, dairy)
  - "dagkeuze"   = daily-treat tier (small allowance per day)
  - "weekkeuze"  = weekly-treat tier (occasional treats and fast food)
  - Outside Schijf = dagkeuze + weekkeuze (anything not in the staple tier)

How to work:
  1. Call inspection tools first to learn the user's situation.
  2. If the user is over-budget or trending that way, call propose_swap with a
     specific cheaper-and-healthier swap based on the actual top offender items.
  3. If the user is at risk of blowing the goal (>=75% used, with month not over),
     also call propose_savings_transfer for a small amount (€5–€25) — this is
     a behavioural commitment device, not a punishment.
  4. Finally call finalize_plan with a summary, headline number, tip, and
     risk level.

Tone: warm, low-stakes, supportive. NOT clinical, NOT moralising. Treat
"weekkeuze" items as fine in moderation — your job is to make trade-offs
visible, not to scold. Use the user's own data, never invent numbers.

When proposing a swap, be specific: the actual brand/product they bought
versus a concrete alternative. e.g. "Red Bull 250ml → Lipton Ice Tea Zero".

Hard rules:
  - Call exactly one finalize_plan and stop.
  - Don't propose savings transfers >€50 — these are behavioural nudges, not
    serious money moves.
  - Don't fabricate transactions or items. If the data is empty, say so in
    the summary and suggest scanning a receipt."""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

class AdvisorAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def live_enabled(self) -> bool:
        return bool(self.settings.anthropic_api_key)

    async def advise(self, session: Session, *, max_iters: int = 8) -> AgentPlan:
        """
        Run a tool-use loop with Claude until it calls finalize_plan or we hit
        max_iters. Always returns an AgentPlan — falls back to a static plan
        if no API key or any error occurs.
        """
        plan = AgentPlan(
            summary="",
            risk_level="on_track",
            headline_number="",
            tip="",
        )

        if not self.live_enabled():
            return self._fallback_plan(session, plan, reason="No ANTHROPIC_API_KEY")

        try:
            return await self._run_loop(session, plan, max_iters=max_iters)
        except Exception as exc:  # noqa: BLE001
            log.warning("Agent loop failed, falling back to deterministic plan: %s", exc)
            return self._fallback_plan(session, plan, reason=f"{type(exc).__name__}: {exc}")

    async def _run_loop(self, session: Session, plan: AgentPlan, *, max_iters: int) -> AgentPlan:
        client = anthropic.AsyncAnthropic(
            api_key=self.settings.anthropic_api_key,
            timeout=self.settings.anthropic_request_timeout_seconds,
        )
        tools = _build_read_tools(session)
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    "Generate today's advisory plan for the user. Inspect their "
                    "month-to-date data, look for top offenders, and propose at "
                    "most one swap and at most one savings transfer if the goal "
                    "is at risk. Then call finalize_plan and stop."
                ),
            }
        ]

        reasoning_chunks: list[str] = []

        for iteration in range(max_iters):
            response = await client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=2000,
                system=_SYSTEM,
                tools=tools,
                messages=messages,
            )

            # Capture any free-text reasoning Claude emitted alongside tool_use.
            for block in response.content:
                if getattr(block, "type", None) == "text" and block.text:
                    reasoning_chunks.append(block.text.strip())

            # Stop conditions.
            if response.stop_reason == "end_turn" and not any(
                getattr(b, "type", None) == "tool_use" for b in response.content
            ):
                break

            # Run all tool_use blocks in this turn and append a tool_result for each.
            assistant_blocks = [
                {"type": b.type, **({"text": b.text} if b.type == "text" else {}),
                 **({"id": b.id, "name": b.name, "input": b.input} if b.type == "tool_use" else {})}
                for b in response.content
            ]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_results: list[dict[str, Any]] = []
            stop_after = False
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                plan.tool_calls += 1
                try:
                    result = _dispatch_tool(session, block.name, block.input, plan)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    })
                    if block.name == "finalize_plan":
                        stop_after = True
                except Exception as exc:  # noqa: BLE001
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {type(exc).__name__}: {exc}",
                        "is_error": True,
                    })

            if not tool_results:
                break

            messages.append({"role": "user", "content": tool_results})

            if stop_after:
                break

        plan.reasoning = "\n\n".join(reasoning_chunks).strip()

        # If Claude never called finalize_plan, we still need a minimal plan.
        if not plan.summary:
            return self._fallback_plan(session, plan, reason="Agent did not call finalize_plan")

        return plan

    # ------------------------------------------------------------------
    # Deterministic fallback (offline mode / failure mode)
    # ------------------------------------------------------------------

    def _fallback_plan(self, session: Session, plan: AgentPlan, *, reason: str) -> AgentPlan:
        today = datetime.now(UTC).date()
        cal, spend = mtd_splits(session, today)
        goal = active_goal(session)

        risk = "on_track"
        used_pct: float | None = None
        if goal:
            current = spend.outside_schijf if goal.metric == "OUTSIDE_SCHIJF_SPEND" else cal.outside_schijf
            used_pct = current / goal.target_value if goal.target_value else 0.0
            if used_pct >= 1:
                risk = "over_target"
            elif used_pct >= 0.75:
                risk = "watch"

        if spend.outside_schijf > 0:
            headline = f"€{spend.outside_schijf:.2f} Outside Schijf this month"
        else:
            headline = "No Outside-Schijf spend tracked yet"

        if used_pct is not None and used_pct >= 0.75:
            tip = "Try one Schijf swap on your next supermarket trip — small wins compound."
        elif spend.outside_schijf > 0:
            tip = "Review the top Outside-Schijf item before your next shop."
        else:
            tip = "Scan a recent receipt to see your Schijf split."

        plan.summary = (
            f"Selected receipt items make €{spend.outside_schijf:.2f} of your month-to-date food spend "
            f"land outside the Schijf van Vijf. Editable estimate."
        )
        plan.headline_number = headline
        plan.tip = tip
        plan.risk_level = risk
        plan.fallback = True
        plan.reasoning = f"Fallback plan used: {reason}"
        return plan
