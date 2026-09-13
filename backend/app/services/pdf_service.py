import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def build_invoice_pdf(data: dict) -> bytes:
    """FR-13.5: printable/downloadable PDF invoice (ReportLab)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 20 * mm

    biz = data.get("business") or {}
    c.setFont("Helvetica-Bold", 16)
    c.drawString(15 * mm, y, str(biz.get("name") or "Invoice"))
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    for line in [biz.get("address"), biz.get("phone"), biz.get("email")]:
        if line:
            c.drawString(15 * mm, y, str(line))
            y -= 4.5 * mm
    y -= 2 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, y, f"Invoice {data.get('invoice_no')}")
    c.setFont("Helvetica", 9)
    c.drawRightString(w - 15 * mm, y, str(data.get("created_at") or ""))
    y -= 5 * mm
    cust = data.get("customer") or {}
    if cust.get("name"):
        c.drawString(15 * mm, y, f"Bill to: {cust.get('name')} {cust.get('phone') or ''}")
        y -= 5 * mm
    y -= 2 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(15 * mm, y, "Item")
    c.drawRightString(130 * mm, y, "Qty")
    c.drawRightString(150 * mm, y, "Price")
    c.drawRightString(185 * mm, y, "Total")
    y -= 5 * mm
    c.line(15 * mm, y, w - 15 * mm, y)
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    for it in data.get("items", []):
        if y < 30 * mm:
            c.showPage()
            y = h - 20 * mm
            c.setFont("Helvetica", 9)
        c.drawString(15 * mm, y, str(it.get("product_name"))[:45])
        c.drawRightString(130 * mm, y, str(it.get("quantity")))
        c.drawRightString(150 * mm, y, f"{float(it.get('unit_price') or 0):.2f}")
        c.drawRightString(185 * mm, y, f"{float(it.get('line_total') or 0):.2f}")
        y -= 5 * mm
    y -= 3 * mm
    c.line(15 * mm, y, w - 15 * mm, y)
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    for label, val in [("Subtotal", data.get("subtotal")), ("Discount", data.get("discount_amount")),
                       (f"Tax ({data.get('tax_percent') or 0}%)", data.get("tax_amount")),
                       ("Total", data.get("total_amount")), ("Paid", data.get("paid_amount"))]:
        c.drawRightString(150 * mm, y, str(label) + ":")
        c.drawRightString(185 * mm, y, f"{float(val or 0):.2f}")
        y -= 5.5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(15 * mm, 15 * mm, f"Payment: {data.get('payment_method')} ({data.get('payment_status')})")
    c.drawRightString(w - 15 * mm, 15 * mm, "Thank you for your business!")
    c.showPage()
    c.save()
    return buf.getvalue()
