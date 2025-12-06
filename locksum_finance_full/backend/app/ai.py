from __future__ import annotations
import datetime as dt
from typing import List, Dict, Literal, Optional
from sqlalchemy.orm import Session
from . import models

RiskLevel = Literal["low", "medium", "high"]

def summarize_spending(db: Session, user_id: int, days: int = 30) -> Dict:
    """Compute core stats for the last N days."""
    since = dt.date.today() - dt.timedelta(days=days)
    txns: List[models.Transaction] = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id, models.Transaction.date >= since)
        .all()
    )

    total = 0.0
    by_cat: Dict[str, float] = {}
    by_day: Dict[dt.date, float] = {}

    for t in txns:
        amt = float(t.amount)
        total += amt
        by_cat[t.category] = by_cat.get(t.category, 0.0) + amt
        by_day[t.date] = by_day.get(t.date, 0.0) + amt

    budgets: List[models.Budget] = (
        db.query(models.Budget)
        .filter(models.Budget.user_id == user_id)
        .all()
    )
    budget_map = {b.category: float(b.limit_amount) for b in budgets}

    avg_per_day = total / days if days else 0.0
    peak_day = max(by_day.items(), key=lambda kv: kv[1]) if by_day else None

    return {
        "days": days,
        "total_spent": round(total, 2),
        "avg_per_day": round(avg_per_day, 2),
        "spend_by_category": {k: round(v, 2) for k, v in by_cat.items()},
        "budgets": budget_map,
        "transaction_count": len(txns),
        "peak_day": peak_day[0].isoformat() if peak_day else None,
        "peak_day_amount": round(peak_day[1], 2) if peak_day else 0.0,
    }


def _compare_to_budgets(by_cat: Dict[str, float], budgets: Dict[str, float]) -> Dict:
    by_cat_vs_budget = []
    for cat, spent in by_cat.items():
        limit = budgets.get(cat)
        entry = {"category": cat, "spent": spent, "limit": limit, "pct_of_budget": None}
        if limit and limit > 0:
            entry["pct_of_budget"] = round((spent / limit) * 100, 1)
        by_cat_vs_budget.append(entry)
    return {"by_category": by_cat_vs_budget}


def _detect_anomalies(by_cat: Dict[str, float], budgets: Dict[str, float]) -> List[str]:
    messages: List[str] = []
    for cat, spent in by_cat.items():
        limit = budgets.get(cat)
        if not limit:
            # large category without a budget
            if spent >= 100:  # threshold
                messages.append(
                    f"High spend in '{cat}' (${spent:.2f}) but no budget set. "
                    "Consider creating a budget here."
                )
        else:
            pct = spent / limit
            if pct >= 1.5:
                messages.append(
                    f"Severe overspend in '{cat}' (${spent:.2f} vs ${limit:.2f}, {pct*100:.0f}% of budget)."
                )
            elif pct >= 1.1:
                messages.append(
                    f"You're over budget in '{cat}' (${spent:.2f} vs ${limit:.2f}, {pct*100:.0f}% of budget)."
                )
            elif 0.9 <= pct < 1.1:
                messages.append(
                    f"'{cat}' is right at the edge of your budget ({pct*100:.0f}% used)."
                )
    return messages


def _safe_to_spend(stats: Dict, month_days_total: Optional[int] = None) -> Dict:
    """Rough safe-to-spend calculation for the rest of the month."""
    today = dt.date.today()
    if month_days_total is None:
        # assume current month
        next_month = today.replace(day=28) + dt.timedelta(days=4)
        last_day = (next_month - dt.timedelta(days=next_month.day)).day
        month_days_total = last_day

    days_elapsed = min(stats["days"], today.day)
    days_left = max(month_days_total - days_elapsed, 0)
    total_budget = sum(stats["budgets"].values()) if stats["budgets"] else 0.0
    spent = stats["total_spent"]
    remaining = max(total_budget - spent, 0.0)

    per_day = remaining / days_left if days_left > 0 and remaining > 0 else 0.0

    return {
        "month_days_total": month_days_total,
        "days_elapsed": days_elapsed,
        "days_left": days_left,
        "budget_total": round(total_budget, 2),
        "spent_so_far": round(spent, 2),
        "remaining_budget": round(remaining, 2),
        "suggested_safe_per_day": round(per_day, 2),
    }


def _debt_payoff_plan(total_debt: float, monthly_extra: float, risk: RiskLevel) -> Dict:
    """Very simple payoff planner: estimate months to payoff based on extra payment."""
    if total_debt <= 0 or monthly_extra <= 0:
        return {
            "total_debt": total_debt,
            "monthly_extra": monthly_extra,
            "estimated_months": None,
            "style": risk,
            "note": "Provide a positive total_debt and monthly_extra to get a payoff estimate.",
        }

    # Risk tweaks how aggressive we assume you want to be (simple scalar on monthly_extra)
    factor = {"low": 0.8, "medium": 1.0, "high": 1.2}[risk]
    effective_payment = monthly_extra * factor
    months = total_debt / effective_payment
    return {
        "total_debt": round(total_debt, 2),
        "monthly_extra": round(monthly_extra, 2),
        "effective_payment": round(effective_payment, 2),
        "estimated_months": round(months, 1),
        "style": risk,
        "note": (
            "This is a rough estimate. Real payoff time will depend on interest rates and fees."
        ),
    }


def generate_text_advice(stats: Dict, goals: Optional[Dict] = None) -> Dict:
    """Rule-based 'AI' that converts stats + optional goals into advice."""
    days = stats["days"]
    total = stats["total_spent"]
    by_cat = stats["spend_by_category"]
    budgets = stats["budgets"]
    tx_count = stats["transaction_count"]

    insights: List[str] = []
    warnings: List[str] = []
    actions: List[str] = []

    per_day = stats.get("avg_per_day", 0.0)
    peak_day = stats.get("peak_day")
    peak_amt = stats.get("peak_day_amount", 0.0)

    # Overall spend
    insights.append(
        f"You spent about ${total:.2f} in the last {days} days (~${per_day:.2f} per day)."
    )
    if peak_day:
        insights.append(
            f"Your highest spending day was {peak_day} with about ${peak_amt:.2f}."
        )

    if tx_count == 0:
        warnings.append(
            "I didn't see any transactions for this period. "
            "Make sure your bank connections are syncing correctly."
        )
        actions.append(
            "Connect at least one bank or card and import transactions so I can analyze your spending."
        )
        return {"summary": insights, "warnings": warnings, "suggested_actions": actions}

    # Budget comparisons & anomalies
    cmp = _compare_to_budgets(by_cat, budgets)
    anomalies = _detect_anomalies(by_cat, budgets)
    warnings.extend(anomalies)

    # Missing core budgets
    core_cats = ["Rent", "Housing", "Groceries", "Utilities", "Savings"]
    missing = [c for c in core_cats if c not in budgets]
    if missing:
        actions.append(
            "You don't have budgets for some important areas: "
            + ", ".join(missing)
            + ". Add budgets so I can help you stay on track."
        )

    # Simple savings/progress toward goals (if provided)
    if goals:
        monthly_savings_target = goals.get("monthly_savings_target")
        if monthly_savings_target:
            # pretend savings is difference between total budget and total spend
            budget_total = sum(budgets.values()) if budgets else 0.0
            inferred_savings = max(budget_total - total, 0.0)
            if inferred_savings >= monthly_savings_target:
                insights.append(
                    f"Based on your budgets vs. spending, you're on track to save "
                    f"around ${inferred_savings:.2f} this month (target: ${monthly_savings_target:.2f})."
                )
            else:
                warnings.append(
                    f"You're currently behind your savings target of ${monthly_savings_target:.2f} "
                    f"this month. Consider trimming some flexible categories."
                )

    # Generic savings suggestion
    if total > 0:
        target_savings = total * 0.10
        actions.append(
            f"If possible, try to move around ${target_savings:.2f} from this period into "
            "savings or debt payoff."
        )

    return {
        "summary": insights,
        "warnings": warnings,
        "suggested_actions": actions,
        "categories": cmp["by_category"],
    }


def build_ai_insights(
    db: Session,
    user_id: int,
    days: int = 30,
    goals: Optional[Dict] = None,
) -> Dict:
    stats = summarize_spending(db, user_id, days=days)
    advice = generate_text_advice(stats, goals=goals)
    safe = _safe_to_spend(stats)
    return {
        "stats": stats,
        "advice": advice,
        "safe_to_spend": safe,
    }


def build_debt_plan(
    total_debt: float,
    monthly_extra: float,
    risk: RiskLevel = "medium",
) -> Dict:
    return _debt_payoff_plan(total_debt, monthly_extra, risk)
