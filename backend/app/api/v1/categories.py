from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_all(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.business_id == ctx.business_id).all()


@router.post("", response_model=CategoryOut, status_code=201)
def create(payload: CategoryCreate, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    c = Category(business_id=ctx.business_id, name=payload.name, description=payload.description)
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    db.refresh(c)
    return c


@router.patch("/{cat_id}", response_model=CategoryOut)
def update(cat_id: int, payload: CategoryUpdate, ctx: Context = Depends(get_current_context),
           db: Session = Depends(get_db)):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    c = db.query(Category).filter(Category.id == cat_id, Category.business_id == ctx.business_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    db.refresh(c)
    return c


@router.post("/{cat_id}/deactivate", response_model=CategoryOut)
def deactivate(cat_id: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    c = db.query(Category).filter(Category.id == cat_id, Category.business_id == ctx.business_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    c.is_active = False
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{cat_id}")
def delete(cat_id: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-4.4: prevent deletion when products exist unless reassigned."""
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    c = db.query(Category).filter(Category.id == cat_id, Category.business_id == ctx.business_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    count = db.query(Product).filter(Product.category_id == cat_id,
                                     Product.business_id == ctx.business_id).count()
    if count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {count} product(s) use this category. Reassign first.")
    db.delete(c)
    db.commit()
    return {"message": "Deleted"}
