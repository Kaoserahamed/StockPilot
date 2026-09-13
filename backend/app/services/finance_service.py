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

from app.services.finance._missing import (  # noqa: F401, E402
    profit_summary,
    sales_trend,
    inventory_value,
    expenses_total,
    cogs_summary,
    avg_costs,
)
from app.services.finance._utils import (  # noqa: F401, E402
    _sale_range_filters,
    MAX_SALE_IDS,
    MAX_TREND_BUCKETS,
)

__all__ = [
    "parse_dt", "resolve_range", "REVENUE_STATUSES", "PRESETS",
    "revenue_summary", "sales_in_range", "revenue_trend",
    "expense_summary", "expense_breakdown",
    "top_products", "customer_stats", "supplier_stats",
    "profit_summary", "sales_trend", "inventory_value",
    "expenses_total", "cogs_summary", "avg_costs",
    "_sale_range_filters", "MAX_SALE_IDS", "MAX_TREND_BUCKETS",
]
