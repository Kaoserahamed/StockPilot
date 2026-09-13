from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.party import Supplier
from app.models.product import Product
from app.models.transactions import Purchase, PurchaseItem
from app.schemas.schemas import PurchaseCreate, PurchaseItemOut, PurchaseOut, PurchasePayRequest
from app.services.audit import write_audit

router = APIRouter(prefix="/purchases", tags=["purchases"])


def _check_write(ctx: Context):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def _to_out(db: Session, p: Purchase) -> PurchaseOut:
    items = db.query(PurchaseItem).filter(PurchaseItem.purchase_id == p.id).all()
    pids = [i.product_id for i in items] or [0]
    names = {r.id: r.name for r in db.query(Product).filter(Product.id.in_(pids)).all()}
    sup = db.query(Supplier).filter(Supplier.id == p.supplier_id).first()
    return PurchaseOut(
        id=p.id, supplier_id=p.supplier_id, supplier_name=sup.company_name if sup else None,
        purchase_date=p.purchase_date, subtotal=p.subtotal, discount_amount=p.discount_amount,
        tax_amount=p.tax_amount, total_amount=p.total_amount, paid_amount=p.paid_amount,
        payment_status=p.payment_status, status=p.status, note=p.note,
        items=[PurchaseItemOut(id=i.id, product_id=i.product_id,
                               product_name=names.get(i.product_id),
                               quantity=i.quantity, unit_cost=i.unit_cost,
                               line_total=i.line_total) for i in items])


def _many_to_out(db: Session, rows: list[Purchase]) -> list[PurchaseOut]:
    """Batch converter: fixed ~4 queries regardless of list size."""
    if not rows:
        return []
    pids = [p.id for p in rows] or [0]
    items = db.query(PurchaseItem).filter(PurchaseItem.purchase_id.in_(pids)).order_by(
        PurchaseItem.purchase_id, PurchaseItem.id).all()
    prod_ids = list({i.product_id for i in items}) or [0]
    names = {r.id: r.name for r in db.query(Product).filter(Product.id.in_(prod_ids)).all()}
    sup_ids = [p.supplier_id for p in rows] or [0]
    sups = {s.id: s for s in db.query(Supplier).filter(Supplier.id.in_(sup_ids)).all()}
    by_p: dict[int, list[PurchaseItem]] = {}
    for i in items:
        by_p.setdefault(i.purchase_id, []).append(i)
    out = []
    for p in rows:
        sup = sups.get(p.supplier_id)
        pitems = by_p.get(p.id, [])
        out.append(PurchaseOut(
            id=p.id, supplier_id=p.supplier_id,
            supplier_name=sup.company_name if sup else None,
            purchase_date=p.purchase_date, subtotal=p.subtotal,
            discount_amount=p.discount_amount, tax_amount=p.tax_amount,
            total_amount=p.total_amount, paid_amount=p.paid_amount,
            payment_status=p.payment_status, status=p.status, note=p.note,
            items=[PurchaseItemOut(id=i.id, product_id=i.product_id,
                                   product_name=names.get(i.product_id),
                                   quantity=i.quantity, unit_cost=i.unit_cost,
                                   line_total=i.line_total) for i in pitems]))
    return out


@router.get("", response_model=list[PurchaseOut])
def list_all(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
             supplier_id: int | None = None, limit: int = Query(50, ge=1, le=200)):
    q = db.query(Purchase).filter(Purchase.business_id == ctx.business_id)
    if supplier_id:
        q = q.filter(Purchase.supplier_id == supplier_id)
    rows = q.order_by(Purchase.id.desc()).limit(limit).all()
    return _many_to_out(db, rows)


@router.post("/{pid}/pay", response_model=PurchaseOut)
def pay(pid: int, payload: PurchasePayRequest, ctx: Context = Depends(get_current_context),
        db: Session = Depends(get_db)):
    """FR-10.8: record payment against a purchase, update supplier balance."""
    _check_write(ctx)
    p = db.query(Purchase).filter(Purchase.id == pid,
                                  Purchase.business_id == ctx.business_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    if p.status == "cancelled":
        raise HTTPException(status_code=400, detail="Purchase is cancelled")
    remaining = (p.total_amount or 0) - (p.paid_amount or 0)
    if payload.amount > remaining + 1e-9:
        raise HTTPException(status_code=422, detail=f"Exceeds remaining {remaining:.2f}")
    p.paid_amount = (p.paid_amount or 0) + payload.amount
    p.payment_status = "paid" if p.paid_amount >= p.total_amount - 1e-9 else "partial"
    sup = db.query(Supplier).filter(Supplier.id == p.supplier_id).first()
    if sup:
        sup.outstanding_balance = max(0, (sup.outstanding_balance or 0) - payload.amount)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="purchase.pay", resource="purchase", resource_id=str(p.id),
                new_value=str(p.paid_amount))
    db.commit()
    db.refresh(p)
    return _to_out(db, p)


@router.post("/{pid}/cancel", response_model=PurchaseOut)
def cancel(pid: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """Cancel a purchase: reverse added stock, restore supplier balance."""
    _check_write(ctx)
    p = db.query(Purchase).filter(Purchase.id == pid,
                                  Purchase.business_id == ctx.business_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    if p.status == "cancelled":
        return _to_out(db, p)
    from app.models.inventory import InventoryTransaction
    items = db.query(PurchaseItem).filter(PurchaseItem.purchase_id == p.id).all()
    for i in items:
        prod = db.query(Product).filter(Product.id == i.product_id).first()
        if (prod.quantity_on_hand or 0) < i.quantity:
            raise HTTPException(status_code=400,
                                detail=f"Insufficient stock to cancel ({prod.name})")
    for i in items:
        prod = db.query(Product).filter(Product.id == i.product_id).first()
        prod.quantity_on_hand -= i.quantity
        db.add(InventoryTransaction(business_id=ctx.business_id, product_id=prod.id,
                                    quantity_change=-i.quantity, tx_type="purchase",
                                    reason=f"purchase #{p.id} cancelled",
                                    user_id=ctx.user.id, related_id=f"purchase:{p.id}"))
    sup = db.query(Supplier).filter(Supplier.id == p.supplier_id).first()
    if sup:
        unpaid = (p.total_amount or 0) - (p.paid_amount or 0)
        sup.outstanding_balance = max(0, (sup.outstanding_balance or 0) - unpaid)
    p.status = "cancelled"
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="purchase.cancel", resource="purchase", resource_id=str(p.id))
    db.commit()
    db.refresh(p)
    return _to_out(db, p)



@router.post("", response_model=PurchaseOut, status_code=201)
def create(payload: PurchaseCreate, ctx: Context = Depends(get_current_context),
           db: Session = Depends(get_db)):
    """FR-10: multi-item purchase. Totals auto-calculated, stock up on confirm."""
    _check_write(ctx)
    sup = db.query(Supplier).filter(Supplier.id == payload.supplier_id,
                                    Supplier.business_id == ctx.business_id).first()
    if not sup:
        raise HTTPException(status_code=400, detail="Invalid supplier")
    pids = [i.product_id for i in payload.items]
    products = {p.id: p for p in db.query(Product).filter(
        Product.id.in_(pids), Product.business_id == ctx.business_id).all()}
    if len(products) != len(set(pids)):
        raise HTTPException(status_code=400, detail="Invalid product in items")
    subtotal = sum(i.quantity * i.unit_cost for i in payload.items)
    total = subtotal - (payload.discount_amount or 0) + (payload.tax_amount or 0)
    if total < 0:
        raise HTTPException(status_code=422, detail="Total cannot be negative")
    paid = payload.paid_amount or 0
    if paid < 0 or paid > total:
        raise HTTPException(status_code=422, detail="paid_amount must be 0..total")
    pay_status = "unpaid" if paid == 0 else ("paid" if paid >= total else "partial")
    pur = Purchase(business_id=ctx.business_id, supplier_id=sup.id,
                   purchase_date=datetime.now(timezone.utc),
                   subtotal=subtotal, discount_amount=payload.discount_amount or 0,
                   tax_amount=payload.tax_amount or 0, total_amount=total,
                   paid_amount=paid, payment_status=pay_status,
                   status="confirmed", note=payload.note, created_by=ctx.user.id)
    db.add(pur)
    db.flush()
    from app.models.inventory import InventoryTransaction
    for i in payload.items:
        line = i.quantity * i.unit_cost
        db.add(PurchaseItem(purchase_id=pur.id, product_id=i.product_id,
                            quantity=i.quantity, unit_cost=i.unit_cost, line_total=line))
        prod = products[i.product_id]
        prod.quantity_on_hand = (prod.quantity_on_hand or 0) + i.quantity
        db.add(InventoryTransaction(business_id=ctx.business_id, product_id=prod.id,
                                    quantity_change=i.quantity, tx_type="purchase",
                                    reason=f"purchase #{pur.id}", user_id=ctx.user.id,
                                    related_id=f"purchase:{pur.id}"))
    sup.outstanding_balance = (sup.outstanding_balance or 0) + (total - paid)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="purchase.create", resource="purchase", resource_id=str(pur.id),
                new_value=str(total))
    db.commit()
    db.refresh(pur)
    return _to_out(db, pur)


@router.get("/{pid}", response_model=PurchaseOut)
def get_one(pid: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    p = db.query(Purchase).filter(Purchase.id == pid,
                                  Purchase.business_id == ctx.business_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_out(db, p)
