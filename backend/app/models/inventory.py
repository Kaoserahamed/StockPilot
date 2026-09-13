from datetime import datetime
from sqlalchemy import (DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        func)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class InventoryTransaction(Base):
    """FR-8.7/8.8: product, quantity, type, user, timestamp, related transaction."""

    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    tx_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    related_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PriceAdjustment(Base):
    """Product price change history (selling / purchase price adjustments).

    Companion to InventoryTransaction: quantities are tracked there, prices here.
    Every price adjustment stores old -> new values plus the reason and user.
    """

    __tablename__ = "price_adjustments"
    __table_args__ = (
        Index("ix_price_adj_biz_created", "business_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    old_selling_price: Mapped[float] = mapped_column(Float, default=0.0)
    new_selling_price: Mapped[float] = mapped_column(Float, default=0.0)
    old_purchase_price: Mapped[float] = mapped_column(Float, default=0.0)
    new_purchase_price: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AuditLog(Base):
    """FR-27 stub: price changes, adjustments, employee changes. Append-only."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_biz_action_created", "business_id", "action", "created_at"),
        Index("ix_audit_biz_resource", "business_id", "resource", "resource_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
