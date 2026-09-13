import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context, require_roles
from app.db.session import get_db
from app.models.finance import Expense
from app.models.sales import Sale, SaleItem
from app.models.product import Product
from app.models.transactions import Purchase, PurchaseItem
from app.services import finance_service as f

router = APIRouter(prefix="/reports", tags=["reports"])


def _csv(rows: list[dict], filename: str):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["empty"])
    w.writeheader()
    w.writerows(rows)
    data = buf.getvalue().encode()
    return StreamingResponse(io.BytesIO(data), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


def _xlsx(rows: list[dict], filename: str):
    """FR-23.7 Excel export via openpyxl."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "report"
    headers = list(rows[0].keys()) if rows else ["empty"]
    ws.append(headers)
    for r in rows:
        ws.append([r.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


def _maybe_export(rows: list[dict], fmt: str, basename: str):
    if fmt == "csv":
        return _csv(rows, basename + ".csv")
    if fmt in ("excel", "xlsx"):
        return _xlsx(rows, basename + ".xlsx")
    return None


def _report_pdf(title: str, summary: dict, rows: list[dict], filename: str):
    """FR-23.8: generic one-table PDF for any report."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 18 * mm
    c.setFont("Helvetica-Bold", 15)
    c.drawString(15 * mm, y, title)
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    for k, v in (summary or {}).items():
        if y < 20 * mm:
            c.showPage()
            y = h - 18 * mm
            c.setFont("Helvetica", 10)
        c.drawString(15 * mm, y, f"{k}: {v}")
        y -= 5.5 * mm
    y -= 3 * mm
    if rows:
        headers = list(rows[0].keys())[:5]
        c.setFont("Helvetica-Bold", 9)
        x = 15 * mm
        for hh in headers:
            c.drawString(x, y, str(hh)[:18])
            x += 34 * mm
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        for r in rows[:60]:
            if y < 20 * mm:
                c.showPage()
                y = h - 18 * mm
                c.setFont("Helvetica", 8)
            x = 15 * mm
            for hh in headers:
                c.drawString(x, y, str(r.get(hh))[:18])
                x += 34 * mm
            y -= 4.5 * mm
    c.showPage()
    c.save()
    return StreamingResponse(io.BytesIO(buf.getvalue()), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/sales")
def sales_report(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                 preset: str = Query("month"), date_from: datetime | None = None,
                 date_to: datetime | None = None, format: str = "json",
                 limit: int = Query(2000, ge=1, le=100000)):
    """FR-23.1/23.6/23.7/23.8 (+Excel/PDF): sales report."""
    if ctx.role not in ("Owner", "Manager"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month", date_from, date_to)
    rows = f.sales_in_range(db, ctx.business_id, start, end)[:limit]
    data = [{"id": s.id, "invoice_no": s.invoice_no, "customer_id": s.customer_id,
             "total": s.total_amount, "refunded": s.refunded_amount,
             "payment_method": s.payment_method, "status": s.status,
             "created_at": str(s.created_at)} for s in rows]
    summary = f.revenue_summary(db, ctx.business_id, start, end)
    exp = _maybe_export(data, format, "sales")
    if exp is not None:
        return exp
    if format == "pdf":
        return _report_pdf("Sales Report (%s)" % preset, summary, data, "sales.pdf")
    return {"rows": data, "summary": summary}


@router.get("/inventory")
def inventory_report(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                     format: str = "json", limit: int = Query(5000, ge=1, le=100000)):
    """FR-23.2/23.7/23.8: inventory report + CSV/Excel/PDF export."""
    avg = f.avg_costs(db, ctx.business_id)
    prods = db.query(Product).filter(Product.business_id == ctx.business_id
                                     ).order_by(Product.id.asc()).limit(limit).all()
    data = [{"id": p.id, "name": p.name, "sku": p.sku, "qty": p.quantity_on_hand,
             "avg_cost": round(avg.get(p.id, p.purchase_price or 0), 2),
             "selling_price": p.selling_price} for p in prods]
    summary = f.inventory_value(db, ctx.business_id)
    exp = _maybe_export(data, format, "inventory")
    if exp is not None:
        return exp
    if format == "pdf":
        return _report_pdf("Inventory Report", summary, data, "inventory.pdf")
    return {"rows": data, "summary": summary}


@router.get("/purchases")
def purchase_report(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                    preset: str = Query("month"), format: str = "json",
                    limit: int = Query(2000, ge=1, le=100000)):
    """FR-23.3/23.7/23.8: purchase report."""
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    q = db.query(Purchase).filter(Purchase.business_id == ctx.business_id)
    if start is not None:
        q = q.filter(Purchase.purchase_date >= start)
    if end is not None:
        q = q.filter(Purchase.purchase_date <= end)
    rows = q.order_by(Purchase.id.desc()).limit(limit).all()
    data = [{"id": p.id, "supplier_id": p.supplier_id, "total": p.total_amount,
             "paid": p.paid_amount, "payment_status": p.payment_status,
             "status": p.status, "date": str(p.purchase_date)} for p in rows]
    summary = {"orders": len(data), "total": round(sum(r["total"] or 0 for r in data), 2)}
    exp = _maybe_export(data, format, "purchases")
    if exp is not None:
        return exp
    if format == "pdf":
        return _report_pdf("Purchase Report (%s)" % preset, summary, data, "purchases.pdf")
    return {"rows": data, "summary": summary}


@router.get("/expenses")
def expense_report(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                   preset: str = Query("month"), format: str = "json",
                   limit: int = Query(2000, ge=1, le=100000)):
    """FR-23.4/23.7/23.8: expense report."""
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    q = db.query(Expense).filter(Expense.business_id == ctx.business_id)
    if start is not None:
        q = q.filter(Expense.expense_date >= start)
    if end is not None:
        q = q.filter(Expense.expense_date <= end)
    rows = q.order_by(Expense.id.desc()).limit(limit).all()
    data = [{"id": e.id, "category": e.category, "amount": e.amount,
             "payment_method": e.payment_method, "date": str(e.expense_date)} for e in rows]
    summary = f.expenses_total(db, ctx.business_id, start, end)
    exp = _maybe_export(data, format, "expenses")
    if exp is not None:
        return exp
    if format == "pdf":
        return _report_pdf("Expense Report (%s)" % preset, summary, data, "expenses.pdf")
    return {"rows": data, "summary": summary}


@router.get("/profit")
def profit_report(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                  preset: str = Query("month"), format: str = "json"):
    """FR-23.5/23.7/23.8: profit report."""
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    summary = f.profit_summary(db, ctx.business_id, start, end)
    data = [{"metric": k, "value": v} for k, v in summary.items()]
    exp = _maybe_export(data, format, "profit")
    if exp is not None:
        return exp
    if format == "pdf":
        return _report_pdf("Profit Report (%s)" % preset, summary, data, "profit.pdf")
    return summary


@router.get("/profit/pdf")
def profit_pdf(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
               preset: str = Query("month")):
    """FR-23.8: profit report as PDF download."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    s = f.profit_summary(db, ctx.business_id, start, end)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(15 * mm, 270 * mm, f"Profit Report ({preset})")
    c.setFont("Helvetica", 11)
    y = 258 * mm
    for k, v in s.items():
        c.drawString(15 * mm, y, f"{k}: {v}")
        y -= 7 * mm
    c.showPage()
    c.save()
    pdf = buf.getvalue()
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=profit.pdf"})
