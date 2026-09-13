"""Consistent pagination response format for all list endpoints.

Usage:
    from app.core.pagination import paginated_response

    @router.get("/items")
    def list_items(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        query = db.query(Item).filter(Item.business_id == business_id)
        return paginated_response(query, limit, offset)
"""
from fastapi import Query
from sqlalchemy.orm import Query as SAQuery
from app.core.config import settings


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def paginated_response(query: SAQuery, limit: int, offset: int) -> dict:
    """Return a paginated response with metadata.

    Args:
        query: SQLAlchemy query (already filtered)
        limit: Number of items per page (capped at MAX_PAGE_SIZE)
        offset: Number of items to skip

    Returns:
        dict with items, total, limit, offset, has_more
    """
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {
        "items": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
            "next_offset": offset + limit if (offset + limit) < total else None,
        },
    }
