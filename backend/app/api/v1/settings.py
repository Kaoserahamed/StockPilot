from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.business import Business
from app.schemas.schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_out(biz: Business) -> SettingsOut:
    return SettingsOut(currency=biz.currency or "BDT", tax_rate=biz.tax_rate or 0.0,
                       invoice_format=biz.invoice_format or "INV-{yyyy}-{seq:04d}",
                       min_stock_default=biz.min_stock_default or 0,
                       business_name=biz.name, address=biz.address,
                       phone=biz.phone, email=biz.email)


@router.get("", response_model=SettingsOut)
def get_settings(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-28.1/28.2: read business configuration (currency, tax, invoice format...)."""
    biz = db.query(Business).filter(Business.id == ctx.business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    return _to_out(biz)


@router.patch("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, ctx: Context = Depends(get_current_context),
                    db: Session = Depends(get_db)):
    """FR-28.3: owners update settings; FR-28.4 applied at checkout/invoice time."""
    if ctx.role != "Owner":
        raise HTTPException(status_code=403, detail="Only Owner can update settings")
    biz = db.query(Business).filter(Business.id == ctx.business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    data = payload.model_dump(exclude_unset=True)
    if "business_name" in data:
        biz.name = data.pop("business_name") or biz.name
    for k, v in data.items():
        if v is not None:
            setattr(biz, k, v)
    db.commit()
    db.refresh(biz)
    return _to_out(biz)
