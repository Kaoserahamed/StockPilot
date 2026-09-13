"""Finance service package — split from monolithic finance_service.py.

Modules:
    _utils      — date parsing, range resolution, memoization helpers
    _revenue    — revenue summary, sales-in-range, trend aggregation
    _expenses   — expense totals and breakdowns
    _analytics  — top products, customer stats, supplier stats
"""
from app.services.finance._utils import parse_dt, resolve_range, REVENUE_STATUSES, PRESETS
from app.services.finance._revenue import revenue_summary, sales_in_range, revenue_trend
from app.services.finance._expenses import expense_summary, expense_breakdown
from app.services.finance._analytics import top_products, customer_stats, supplier_stats

__all__ = [
    "parse_dt", "resolve_range", "REVENUE_STATUSES", "PRESETS",
    "revenue_summary", "sales_in_range", "revenue_trend",
    "expense_summary", "expense_breakdown",
    "top_products", "customer_stats", "supplier_stats",
]
