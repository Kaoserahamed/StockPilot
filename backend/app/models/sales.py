from datetime import datetime
from sqlalchemy import (DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.transactions import Purchase, PurchaseItem


class Sale(Base):
    """FR-12 sales transaction + FR-13 invoice header (one invoice per sale)."""

    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("business_id", "invoice_no", name="uq_sale_business_invoice"),
        # FR-16/18/19: revenue & trend reads filter by (business, status, created_at).
        Index("ix_sale_biz_status_created", "business_id", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    tax_percent: Mapped[float] = mapped_column(Float, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    paid_amount: Mapped[float] = mapped_column(Float, default=0.0)
    payment_method: Mapped[str] = mapped_column(String(30), default="cash")
    payment_status: Mapped[str] = mapped_column(String(20), default="paid", index=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", index=True)
    refunded_amount: Mapped[float] = mapped_column(Float, default=0.0)
    sold_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        # COGS/top-products/forecast join through (sale_id) then aggregate (product_id).
        Index("ix_saleitem_sale_product", "sale_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    line_total: Mapped[float] = mapped_column(Float, default=0.0)
    returned_qty: Mapped[int] = mapped_column(Integer, default=0)


class SaleReturn(Base):
    """FR-14: return header linked to original sale."""

    __tablename__ = "sale_returns"
    __table_args__ = (
        Index("ix_return_biz_created", "business_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    refund_amount: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SaleReturnItem(Base):
    __tablename__ = "sale_return_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_item_id: Mapped[int] = mapped_column(ForeignKey("sale_items.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    refund: Mapped[float] = mapped_column(Float, default=0.0)


class InvoiceCounter(Base):
    """Per-business invoice sequence (no ALTER on businesses table)."""

    __tablename__ = "invoice_counters"

    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True)
    last_seq: Mapped[int] = mapped_column(Integer, default=0)
