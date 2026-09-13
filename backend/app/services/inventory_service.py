from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.inventory import InventoryTransaction
from app.models.product import Product


def apply_stock_change(db: Session, *, business_id: int, product_id: int,
                       quantity_change: int, tx_type: str, reason: str,
                       user_id: int | None, related_id: str | None = None):
    """Single writer for quantity_on_hand. FR-8: all changes go through a transaction row."""
    if not reason:
        raise HTTPException(status_code=422, detail="Reason is required")
    if quantity_change == 0:
        raise HTTPException(status_code=422, detail="quantity_change cannot be zero")
    product = db.query(Product).filter(
        Product.id == product_id, Product.business_id == business_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    new_qty = (product.quantity_on_hand or 0) + quantity_change
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock: would go negative")
    product.quantity_on_hand = new_qty
    tx = InventoryTransaction(business_id=business_id, product_id=product.id,
                              quantity_change=quantity_change, tx_type=tx_type,
                              reason=reason, user_id=user_id, related_id=related_id)
    db.add(tx)
    db.flush()
    return product, tx
