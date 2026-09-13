from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.inventory import InventoryTransaction, PriceAdjustment
from app.models.product import Product
from app.schemas.schemas import (AdjustRequest, InventoryTxOut, PriceAdjustRequest,
                                 PriceAdjustmentOut)
from app.services.audit import write_audit
from app.services.inventory_service import apply_stock_change

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/overview")
def overview(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
             category_id: int | None = None, status: str | None = None,
             stock: str | None = Query(default=None, description="low|out|ok"),
             limit: int = Query(500, ge=1, le=5000), offset: int = Query(0, ge=0)):
    """FR-9.4/9.5: overview + filter by category, status, stock condition."""
    q = db.query(Product).filter(Product.business_id == ctx.business_id)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if status == "active":
        q = q.filter(Product.is_active.is_(True))
    elif status == "inactive":
        q = q.filter(Product.is_active.is_(False))
    rows = q.order_by(Product.id.desc()).offset(offset).limit(limit).all()
    out = []
    for p in rows:
        qty = p.quantity_on_hand or 0
        cond = "ok"
        if qty <= 0:
            cond = "out"
        elif qty < (p.min_stock or 0):
            cond = "low"
        if stock and stock != cond:
            continue
        out.append({"id": p.id, "name": p.name, "sku": p.sku, "category_id": p.category_id,
                    "quantity": qty, "min_stock": p.min_stock, "condition": cond,
                    "is_active": p.is_active, "selling_price": p.selling_price,
                    "purchase_price": p.purchase_price})
    return out


@router.get("/low-stock")
def low_stock(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    rows = db.query(Product).filter(Product.business_id == ctx.business_id).all()
    return [{"id": p.id, "name": p.name, "quantity": p.quantity_on_hand, "min_stock": p.min_stock}
            for p in rows if (p.quantity_on_hand or 0) < (p.min_stock or 0) and (p.quantity_on_hand or 0) > 0]


@router.get("/out-of-stock")
def out_of_stock(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    rows = db.query(Product).filter(Product.business_id == ctx.business_id).all()
    return [{"id": p.id, "name": p.name, "quantity": p.quantity_on_hand}
            for p in rows if (p.quantity_on_hand or 0) <= 0]


@router.get("/transactions", response_model=list[InventoryTxOut])
def transactions(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                 product_id: int | None = None):
    q = db.query(InventoryTransaction).filter(InventoryTransaction.business_id == ctx.business_id)
    if product_id:
        q = q.filter(InventoryTransaction.product_id == product_id)
    return q.order_by(InventoryTransaction.id.desc()).limit(200).all()


@router.post("/adjust", response_model=InventoryTxOut, status_code=201)
def adjust(payload: AdjustRequest, ctx: Context = Depends(get_current_context),
           db: Session = Depends(get_db)):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    product, tx = apply_stock_change(db, business_id=ctx.business_id, product_id=payload.product_id,
                                     quantity_change=payload.quantity_change, tx_type="adjustment",
                                     reason=payload.reason, user_id=ctx.user.id)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="inventory.adjust",
                resource="product", resource_id=str(product.id),
                new_value=str(payload.quantity_change))
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/adjust-price", response_model=PriceAdjustmentOut, status_code=201)
def adjust_price(payload: PriceAdjustRequest, ctx: Context = Depends(get_current_context),
                 db: Session = Depends(get_db)):
    """Price adjustment (selling / purchase price) with reason + audit + history row."""
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    product = db.query(Product).filter(
        Product.id == payload.product_id,
        Product.business_id == ctx.business_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.new_selling_price is None and payload.new_purchase_price is None:
        raise HTTPException(status_code=422, detail="Provide new_selling_price and/or new_purchase_price")
    old_sell = float(product.selling_price or 0)
    old_cost = float(product.purchase_price or 0)
    new_sell = payload.new_selling_price if payload.new_selling_price is not None else old_sell
    new_cost = payload.new_purchase_price if payload.new_purchase_price is not None else old_cost
    if new_sell == old_sell and new_cost == old_cost:
        raise HTTPException(status_code=422, detail="Prices are unchanged")
    product.selling_price = new_sell
    product.purchase_price = new_cost
    row = PriceAdjustment(business_id=ctx.business_id, product_id=product.id,
                          old_selling_price=old_sell, new_selling_price=new_sell,
                          old_purchase_price=old_cost, new_purchase_price=new_cost,
                          reason=payload.reason, user_id=ctx.user.id)
    db.add(row)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="product.price_change", resource="product", resource_id=str(product.id),
                old_value=f"sell {old_sell} / cost {old_cost}",
                new_value=f"sell {new_sell} / cost {new_cost}")
    db.commit()
    db.refresh(row)
    return row


@router.get("/price-adjustments", response_model=list[PriceAdjustmentOut])
def list_price_adjustments(ctx: Context = Depends(get_current_context),
                           db: Session = Depends(get_db),
                           product_id: int | None = None,
                           limit: int = Query(100, ge=1, le=500)):
    """Recent price adjustments (optionally filtered by product)."""
    q = db.query(PriceAdjustment).filter(PriceAdjustment.business_id == ctx.business_id)
    if product_id:
        q = q.filter(PriceAdjustment.product_id == product_id)
    return q.order_by(PriceAdjustment.id.desc()).limit(limit).all()
