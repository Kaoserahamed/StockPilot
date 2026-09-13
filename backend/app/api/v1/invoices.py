from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.business import Business
from app.models.party import Customer
from app.models.product import Product
from app.models.sales import Sale, SaleItem
from app.services.pdf_service import build_invoice_pdf
import io

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _payload(db: Session, s: Sale) -> dict:
    biz = db.query(Business).filter(Business.id == s.business_id).first()
    cust = db.query(Customer).filter(Customer.id == s.customer_id).first() if s.customer_id else None
    items = db.query(SaleItem).filter(SaleItem.sale_id == s.id).all()
    pids = [i.product_id for i in items] or [0]
    names = {p.id: p.name for p in db.query(Product).filter(Product.id.in_(pids)).all()}
    return {
        "business": {"name": biz.name if biz else "", "address": biz.address if biz else "",
                     "phone": biz.phone if biz else "", "email": biz.email if biz else ""},
        "invoice_no": s.invoice_no, "created_at": str(s.created_at),
        "customer": {"name": cust.name if cust else None, "phone": cust.phone if cust else None},
        "items": [{"product_name": names.get(i.product_id), "quantity": i.quantity,
                   "unit_price": i.unit_price, "line_total": i.line_total} for i in items],
        "subtotal": s.subtotal, "discount_amount": s.discount_amount,
        "tax_percent": s.tax_percent, "tax_amount": s.tax_amount,
        "total_amount": s.total_amount, "paid_amount": s.paid_amount,
        "payment_method": s.payment_method, "payment_status": s.payment_status,
    }


@router.get("/{sale_id}", response_model=None)
def view_invoice(sale_id: int, ctx: Context = Depends(get_current_context),
                 db: Session = Depends(get_db)):
    """FR-13.3/13.4: view invoice JSON (frontend prints it)."""
    s = db.query(Sale).filter(Sale.id == sale_id,
                              Sale.business_id == ctx.business_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    return _payload(db, s)


@router.get("/{sale_id}/pdf")
def download_pdf(sale_id: int, ctx: Context = Depends(get_current_context),
                 db: Session = Depends(get_db)):
    """FR-13.5: invoice download in PDF format."""
    s = db.query(Sale).filter(Sale.id == sale_id,
                              Sale.business_id == ctx.business_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    pdf = build_invoice_pdf(_payload(db, s))
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={s.invoice_no}.pdf"})
