"""Audit logging service for StockPilot backend.

Logs all significant business actions with user context, IP address,
and user agent for compliance and security auditing.
"""
from sqlalchemy.orm import Session
from app.models.inventory import AuditLog


def write_audit(db: Session, *, business_id: int, user_id: int | None,
                action: str, resource: str, resource_id: str | None = None,
                old_value: str | None = None, new_value: str | None = None,
                ip_address: str | None = None, user_agent: str | None = None) -> None:
    """Write an audit log entry.

    Args:
        db: Database session
        business_id: Business that owns the resource
        user_id: User who performed the action (None for system actions)
        action: Action type (e.g., 'sale.create', 'product.price_change')
        resource: Resource type (e.g., 'sale', 'product', 'user')
        resource_id: ID of the specific resource
        old_value: Previous value (for updates)
        new_value: New value (for updates)
        ip_address: Client IP address for security auditing
        user_agent: Client user agent for security auditing
    """
    # Truncate values to prevent DB bloat
    if old_value and len(str(old_value)) > 2000:
        old_value = str(old_value)[:2000] + "...(truncated)"
    if new_value and len(str(new_value)) > 2000:
        new_value = str(new_value)[:2000] + "...(truncated)"

    entry = AuditLog(
        business_id=business_id,
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(entry)
