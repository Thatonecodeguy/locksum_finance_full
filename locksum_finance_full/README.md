## AI Insights & Coaching

The backend exposes two endpoints to help customers manage their finances:

- `POST /ai/insights?days=30`
  - Body (optional):
    - `{"monthly_savings_target": 300}` – used to compare budgets vs. savings goals.
  - Returns:
    - `stats` – totals, per-category spend, averages, peak day.
    - `advice` – summary lines, warnings, suggested actions, and per-category budget comparison.
    - `safe_to_spend` – rough daily amount user can spend for the rest of the month.

- `POST /ai/debt-plan`
  - Body:
    - `{"total_debt": 5000, "monthly_extra": 250, "risk": "medium"}` (risk = low|medium|high)
  - Returns:
    - Rough estimate of months to pay off based on extra payment and risk preference.

These are rule-based so they require no external AI API keys and are safe to run anywhere.
