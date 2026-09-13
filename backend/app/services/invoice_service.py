from datetime import datetime
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.sales import InvoiceCounter


def next_invoice_no(db: Session, *, business_id: int) -> str:
    """FR-11.10/FR-13: unique invoice number per business.

    Uses Business.invoice_format template, e.g. 'INV-{yyyy}-{seq:04d}'.
    Supported placeholders: {yyyy}, {yy}, {mm}, {seq} / {seq:04d}.
    """
    biz = db.query(Business).filter(Business.id == business_id).first()
    fmt = "INV-{yyyy}-{seq:04d}"
    if biz is not None and biz.invoice_format:
        fmt = biz.invoice_format
    counter = db.query(InvoiceCounter).filter(InvoiceCounter.business_id == business_id).first()
    if not counter:
        counter = InvoiceCounter(business_id=business_id, last_seq=0)
        db.add(counter)
        db.flush()
    counter.last_seq = (counter.last_seq or 0) + 1
    db.flush()
    now = datetime.now()
    seq = counter.last_seq
    out = fmt.replace("{yyyy}", now.strftime("%Y")).replace("{yy}", now.strftime("%y")).replace("{mm}", now.strftime("%m"))
    # handle {seq} and {seq:0Nd} forms
    import re

    def _seq_repl(m):
        spec = m.group(1)
        if not spec:
            return str(seq)
        try:
            return ("{:" + spec + "}").format(seq)
        except Exception:
            return str(seq)

    out = re.sub(r"\{seq(?::([^}]+))?\}", _seq_repl, out)
    if "{seq" in out:  # unknown variant fallback
        out = out.replace("{seq}", str(seq))
    return out
