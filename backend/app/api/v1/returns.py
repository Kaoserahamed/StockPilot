from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.inventory import InventoryTransaction
from app.models.party import Customer
from app.models.product import Product
from app.models.sales import Sale, SaleItem, SaleReturn, SaleReturnItem
from app.schemas.schemas import ReturnCreate, ReturnOut
from app.services.audit import write_audit

router = APIRouter(prefix="/returns", tags=["returns"])


@router.post("", response_model=ReturnOut, status_code=201)
def create_return(payload: ReturnCreate, ctx: Context = Depends(get_current_context),
                  db: Session = Depends(get_db)):
    """FR-14: full/partial return -> stock up + financial adjustment + audit."""
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    sale = db.query(Sale).filter(Sale.id == payload.sale_id,
                                 Sale.business_id == ctx.business_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.status == "cancelled":
        raise HTTPException(status_code=400, detail="Sale is cancelled")
    items = {i.id: i for i in db.query(SaleItem).filter(
        SaleItem.sale_id == sale.id).all()}
    refund = 0.0
    lines = []
    for r in payload.items:
        si = items.get(r.sale_item_id)
        if not si:
            raise HTTPException(status_code=400, detail=f"Bad sale_item {r.sale_item_id}")
        avail = si.quantity - (si.returned_qty or 0)
        if r.quantity > avail:
            raise HTTPException(status_code=400,
                                detail=f"Only {avail} returnable for item {si.id}")
        unit_refund = (si.line_total / si.quantity) if si.quantity else 0
        refund += unit_refund * r.quantity
        lines.append((si, r.quantity, unit_refund * r.quantity))
    refund = round(refund, 2)
    ret = SaleReturn(business_id=ctx.business_id, sale_id=sale.id,
                     reason=payload.reason, refund_amount=refund, created_by=ctx.user.id)
    db.add(ret)
    db.flush()
    for si, qty, ref in lines:
        si.returned_qty = (si.returned_qty or 0) + qty
        prod = db.query(Product).filter(Product.id == si.product_id).first()
        prod.quantity_on_hand = (prod.quantity_on_hand or 0) + qty
        db.add(SaleReturnItem(return_id=ret.id, sale_item_id=si.id,
                              product_id=si.product_id, quantity=qty, refund=round(ref, 2)))
        db.add(InventoryTransaction(business_id=ctx.business_id, product_id=prod.id,
                                    quantity_change=qty, tx_type="return",
                                    reason=payload.reason, user_id=ctx.user.id,
                                    related_id=f"return:{ret.id}"))
    sale.refunded_amount = (sale.refunded_amount or 0) + refund
    total_returned = sum(i.returned_qty or 0 for i in items.values())
    total_qty = sum(i.quantity for i in items.values())
    sale.status = "returned" if total_returned >= total_qty else "partial_returned"
    if sale.customer_id:  # FR-14.6 adjust customer balance
        cust = db.query(Customer).filter(Customer.id == sale.customer_id).first()
        if cust:
            cust.outstanding_balance = max(0, (cust.outstanding_balance or 0) - refund)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="sale.return", resource="sale", resource_id=str(sale.id),
                new_value=str(refund))
    db.commit()
    db.refresh(ret)
    return ReturnOut(id=ret.id, sale_id=ret.sale_id, reason=ret.reason,
                     refund_amount=ret.refund_amount, created_at=ret.created_at)


@router.get("", response_model=list[ReturnOut])
def list_returns(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    rows = db.query(SaleReturn).filter(
        SaleReturn.business_id == ctx.business_id).order_by(SaleReturn.id.desc()).limit(200).all()
    return [ReturnOut(id=r.id, sale_id=r.sale_id, reason=r.reason,
                      refund_amount=r.refund_amount, created_at=r.created_at) for r in rows]
