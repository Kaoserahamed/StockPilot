from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.finance import Expense
from app.schemas.schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/expenses", tags=["expenses"])

ALLOWED = {"rent", "salary", "electricity", "transport", "maintenance", "miscellaneous", "other"}


def _check(ctx: Context):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("", response_model=list[ExpenseOut])
def list_all(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
             category: str | None = None,
             date_from: datetime | None = None, date_to: datetime | None = None):
    """FR-15.5: expense history with optional category/date filters."""
    q = db.query(Expense).filter(Expense.business_id == ctx.business_id)
    if category:
        q = q.filter(Expense.category == category.lower())
    if date_from:
        q = q.filter(Expense.expense_date >= date_from)
    if date_to:
        q = q.filter(Expense.expense_date <= date_to)
    return q.order_by(Expense.id.desc()).limit(500).all()


@router.post("", response_model=ExpenseOut, status_code=201)
def create(payload: ExpenseCreate, ctx: Context = Depends(get_current_context),
           db: Session = Depends(get_db)):
    """FR-15.1/15.2/15.3: create expense record."""
    _check(ctx)
    cat = payload.category.strip().lower()
    if cat not in ALLOWED:
        raise HTTPException(status_code=422, detail=f"category must be one of {sorted(ALLOWED)}")
    e = Expense(business_id=ctx.business_id, category=cat, amount=payload.amount,
                description=payload.description,
                expense_date=payload.expense_date or datetime.now(timezone.utc),
                payment_method=(payload.payment_method or "cash").lower(),
                created_by=ctx.user.id)
    db.add(e)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="expense.create", resource="expense", resource_id=None,
                new_value=str(payload.amount))
    db.commit()
    db.refresh(e)
    return e


@router.patch("/{eid}", response_model=ExpenseOut)
def update(eid: int, payload: ExpenseUpdate, ctx: Context = Depends(get_current_context),
           db: Session = Depends(get_db)):
    """FR-15.4: update expense."""
    _check(ctx)
    e = db.query(Expense).filter(Expense.id == eid,
                                 Expense.business_id == ctx.business_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    if "category" in data and data["category"] is not None:
        cat = data["category"].strip().lower()
        if cat not in ALLOWED:
            raise HTTPException(status_code=422, detail="Invalid category")
        e.category = cat
    for k in ("amount", "description", "expense_date", "payment_method"):
        if data.get(k) is not None:
            setattr(e, k, data[k].lower() if k == "payment_method" and data[k] else data[k])
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="expense.update", resource="expense", resource_id=str(eid))
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{eid}", status_code=204)
def remove(eid: int, ctx: Context = Depends(get_current_context),
           db: Session = Depends(get_db)):
    """FR-15.4: remove expense."""
    _check(ctx)
    e = db.query(Expense).filter(Expense.id == eid,
                                 Expense.business_id == ctx.business_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(e)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id,
                action="expense.delete", resource="expense", resource_id=str(eid))
    db.commit()
    return None
