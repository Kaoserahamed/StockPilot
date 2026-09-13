from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.schemas.schemas import SubscriptionOut, SubscriptionUpdate
from app.services import subscription_service as subs

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("", response_model=SubscriptionOut)
def get_subscription(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-29.3/29.6: current plan + usage; visible to Owner/Manager."""
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return subs.subscription_status(db, ctx.business_id)


@router.patch("", response_model=SubscriptionOut)
def change_plan(payload: SubscriptionUpdate, ctx: Context = Depends(get_current_context),
                db: Session = Depends(get_db)):
    """Change plan (demo billing hook). Owner only."""
    if ctx.role != "Owner":
        raise HTTPException(status_code=403, detail="Only Owner can change plan")
    subs.set_plan(db, ctx.business_id, payload.plan)
    db.commit()
    return subs.subscription_status(db, ctx.business_id)
