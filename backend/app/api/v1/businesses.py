from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
import os
import uuid
from app.core.deps import Context, get_current_context
from app.core.config import settings
from app.db.session import get_db
from app.models.business import Business
from app.models.user import UserBusiness
from app.schemas.schemas import BusinessCreate, BusinessOut, BusinessUpdate

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("/me", response_model=BusinessOut)
def get_my_business(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    biz = db.query(Business).filter(Business.id == ctx.business_id).first()
    return biz


@router.post("", response_model=BusinessOut, status_code=201)
def create_business(payload: BusinessCreate, ctx: Context = Depends(get_current_context),
                    db: Session = Depends(get_db)):
    """FR-2.1 / FR-24: authenticated owner can create an additional business profile."""
    if ctx.role != "Owner":
        raise HTTPException(status_code=403, detail="Only Owner can create a business")
    biz = Business(name=payload.name, address=payload.address, phone=payload.phone,
                   email=payload.email, currency=payload.currency or "BDT",
                   tax_rate=payload.tax_rate or 0.0)
    db.add(biz)
    db.flush()
    db.add(UserBusiness(user_id=ctx.user.id, business_id=biz.id, role="Owner", is_active=True))
    db.commit()
    db.refresh(biz)
    return biz


@router.patch("/me", response_model=BusinessOut)
def update_my_business(payload: BusinessUpdate, ctx: Context = Depends(get_current_context),
                       db: Session = Depends(get_db)):
    if ctx.role != "Owner":
        raise HTTPException(status_code=403, detail="Only Owner can update business")
    biz = db.query(Business).filter(Business.id == ctx.business_id).first()
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(biz, k, v)
    db.commit()
    db.refresh(biz)
    return biz


@router.post("/me/logo", response_model=BusinessOut)
def upload_logo(file: UploadFile = File(...), ctx: Context = Depends(get_current_context),
                db: Session = Depends(get_db)):
    """FR-2.2: store business logo. Local filesystem initially."""
    if ctx.role != "Owner":
        raise HTTPException(status_code=403, detail="Only Owner can update business")
    biz = db.query(Business).filter(Business.id == ctx.business_id).first()
    dest_dir = os.path.join(settings.upload_dir, "logos")
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1][:10]
    fname = f"biz_{biz.id}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(dest_dir, fname)
    with open(path, "wb") as f:
        f.write(file.file.read())
    biz.logo_path = path
    db.commit()
    db.refresh(biz)
    return biz

