"""Finance service - backward-compatible re-export from finance subpackage.

This module now delegates to smaller, focused modules under app/services/finance/.
New code should import directly from app.services.finance.
Existing imports from app.services.finance_service continue to work.
"""
# Re-export everything from the new subpackage
from app.services.finance import (  # noqa: F401
    parse_dt,
    resolve_range,
    REVENUE_STATUSES,
    PRESETS,
    revenue_summary,
    sales_in_range,
    revenue_trend,
    expense_summary,
    expense_breakdown,
    top_products,
    customer_stats,
    supplier_stats,
)

__all__ = [
    "parse_dt", "resolve_range", "REVENUE_STATUSES", "PRESETS",
    "revenue_summary", "sales_in_range", "revenue_trend",
    "expense_summary", "expense_breakdown",
    "top_products", "customer_stats", "supplier_stats",
]
