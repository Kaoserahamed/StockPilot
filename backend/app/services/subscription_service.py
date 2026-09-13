from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.saas import Subscription


PLANS: dict[str, dict] = {
    "free": {"product_limit": 100, "employee_limit": 5},
    "basic": {"product_limit": 1000, "employee_limit": 25},
    "pro": {"product_limit": 100000, "employee_limit": 1000},
}


def get_or_create_subscription(db: Session, business_id: int) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.business_id == business_id).first()
    if sub is None:
        sub = Subscription(business_id=business_id, plan="free", status="active",
                           product_limit=PLANS["free"]["product_limit"],
                           employee_limit=PLANS["free"]["employee_limit"])
        db.add(sub)
        db.flush()
    return sub


def set_plan(db: Session, business_id: int, plan: str) -> Subscription:
    sub = get_or_create_subscription(db, business_id)
    sub.plan = plan
    sub.product_limit = PLANS[plan]["product_limit"]
    sub.employee_limit = PLANS[plan]["employee_limit"]
    sub.status = "active"
    db.flush()
    return sub


def subscription_status(db: Session, business_id: int) -> dict:
    """FR-29.3/29.4/29.5: current plan, usage %, near/at limit flags."""
    from app.models.product import Product
    from app.models.user import UserBusiness
    sub = get_or_create_subscription(db, business_id)
    product_count = db.query(Product).filter(Product.business_id == business_id).count()
    employee_count = db.query(UserBusiness).filter(
        UserBusiness.business_id == business_id, UserBusiness.is_active.is_(True)).count()
    plim = max(1, sub.product_limit or 1)
    elim = max(1, sub.employee_limit or 1)
    p_pct = round(product_count / plim * 100, 1)
    e_pct = round(employee_count / elim * 100, 1)
    near = p_pct >= 80 or e_pct >= 80
    at = product_count >= (sub.product_limit or 0) or employee_count >= (sub.employee_limit or 0)
    msg = None
    if at:
        msg = "Plan limit reached. Upgrade your plan or remove unused records."
    elif near:
        msg = "Approaching plan limits (>=80% used)."
    return {"plan": sub.plan, "status": sub.status,
            "product_limit": sub.product_limit, "employee_limit": sub.employee_limit,
            "product_count": product_count, "employee_count": employee_count,
            "product_usage_pct": p_pct, "employee_usage_pct": e_pct,
            "near_limit": near, "at_limit": at, "message": msg}


def check_can_add_product(db: Session, business_id: int) -> None:
    from app.models.product import Product
    sub = get_or_create_subscription(db, business_id)
    count = db.query(Product).filter(Product.business_id == business_id).count()
    if count >= (sub.product_limit or 0):
        raise HTTPException(status_code=402,
                            detail=f"Product limit reached for '{sub.plan}' plan ({sub.product_limit}). Upgrade to add more.")


def check_can_add_employee(db: Session, business_id: int) -> None:
    from app.models.user import UserBusiness
    sub = get_or_create_subscription(db, business_id)
    count = db.query(UserBusiness).filter(
        UserBusiness.business_id == business_id, UserBusiness.is_active.is_(True)).count()
    if count >= (sub.employee_limit or 0):
        raise HTTPException(status_code=402,
                            detail=f"Employee limit reached for '{sub.plan}' plan ({sub.employee_limit}). Upgrade to add more.")
