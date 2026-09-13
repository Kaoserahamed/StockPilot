"""Utility functions for finance services: date parsing, range resolution, memoization."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# FR-16.3: cancelled transactions excluded from revenue/profit math.
REVENUE_STATUSES = ("completed", "partial_returned", "returned")

PRESETS = ("today", "week", "month", "year", "custom", "all")

# Safety caps so one request can never pull an unbounded table into memory.
MAX_SALE_IDS = 20000
MAX_TREND_BUCKETS = 1500


def _memo_key(business_id: int, start, end) -> tuple:
    return (business_id, str(start), str(end))


def _memo_get(db: Session, fname: str, business_id: int, start, end):
    """Per-session memoization: heavy aggregates compute once per request."""
    cache = getattr(db, "_fin_cache", None)
    if cache is None:
        cache = {}
        setattr(db, "_fin_cache", cache)
    return cache.get((fname, _memo_key(business_id, start, end)))


def _memo_set(db: Session, fname: str, business_id: int, start, end, value):
    cache = getattr(db, "_fin_cache", None)
    if cache is None:
        cache = {}
        setattr(db, "_fin_cache", cache)
    cache[(fname, _memo_key(business_id, start, end))] = value
    return value


def parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def resolve_range(preset: str = "month", date_from=None, date_to=None):
    """FR-16.2/FR-18.5: daily/weekly/monthly/yearly/custom ranges.

    week/month/year are trailing (7/30/365 days); today is calendar day.
    Returns (start, end) naive datetimes; None means unbounded.
    """
    now = datetime.now()
    if preset == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), now
    if preset == "week":
        return now - timedelta(days=7), now
    if preset == "year":
        return now - timedelta(days=365), now
    if preset == "all":
        return None, None
    if preset == "custom":
        s, e = parse_dt(date_from), parse_dt(date_to)
        return s, e
    return now - timedelta(days=30), now  # default "month"


def _sale_range_filters(business_id: int, start, end):
    from app.models.sales import Sale
    flt = [Sale.business_id == business_id, Sale.status.in_(REVENUE_STATUSES)]
    if start is not None:
        flt.append(Sale.created_at >= start)
    if end is not None:
        flt.append(Sale.created_at <= end)
    return flt
