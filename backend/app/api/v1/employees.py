from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User, UserBusiness
from app.schemas.schemas import EmployeeCreate, EmployeeOut, EmployeeResetRequest, EmployeeRoleUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/employees", tags=["employees"])


def _owner(ctx: Context):
    if ctx.role != "Owner":
        raise HTTPException(status_code=403, detail="Only Owner allowed")


@router.get("", response_model=list[EmployeeOut])
def list_employees(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    rows = db.query(UserBusiness, User).join(User, User.id == UserBusiness.user_id).filter(
        UserBusiness.business_id == ctx.business_id).all()
    return [EmployeeOut(membership_id=m.id, user=u, role=m.role, is_active=m.is_active) for m, u in rows]


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(payload: EmployeeCreate, ctx: Context = Depends(get_current_context),
                    db: Session = Depends(get_db)):
    _owner(ctx)
    from app.services import subscription_service as _subs
    _subs.check_can_add_employee(db, ctx.business_id)
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already used")
    if payload.phone and db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=409, detail="Phone already used")
    user = User(name=payload.name, email=payload.email, phone=payload.phone,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()
    m = UserBusiness(user_id=user.id, business_id=ctx.business_id, role=payload.role, is_active=True)
    db.add(m)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="employee.create",
                resource="user", resource_id=str(user.id), new_value=payload.role)
    db.commit()
    db.refresh(user)
    db.refresh(m)
    return EmployeeOut(membership_id=m.id, user=user, role=m.role, is_active=m.is_active)


@router.post("/{membership_id}/deactivate", response_model=EmployeeOut)
def deactivate(membership_id: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    _owner(ctx)
    m = db.query(UserBusiness).filter(UserBusiness.id == membership_id,
                                      UserBusiness.business_id == ctx.business_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    m.is_active = False
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="employee.deactivate",
                resource="user", resource_id=str(m.user_id))
    db.commit()
    u = db.query(User).filter(User.id == m.user_id).first()
    return EmployeeOut(membership_id=m.id, user=u, role=m.role, is_active=m.is_active)


@router.post("/{membership_id}/activate", response_model=EmployeeOut)
def activate(membership_id: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    _owner(ctx)
    m = db.query(UserBusiness).filter(UserBusiness.id == membership_id,
                                      UserBusiness.business_id == ctx.business_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    m.is_active = True
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="employee.activate",
                resource="user", resource_id=str(m.user_id))
    db.commit()
    u = db.query(User).filter(User.id == m.user_id).first()
    return EmployeeOut(membership_id=m.id, user=u, role=m.role, is_active=m.is_active)


@router.patch("/{membership_id}/role", response_model=EmployeeOut)
def update_role(membership_id: int, payload: EmployeeRoleUpdate,
                ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-3.3/FR-26.2: owner can re-assign employee roles."""
    _owner(ctx)
    m = db.query(UserBusiness).filter(UserBusiness.id == membership_id,
                                      UserBusiness.business_id == ctx.business_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    old = m.role
    m.role = payload.role
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="employee.role_change",
                resource="user", resource_id=str(m.user_id),
                old_value=old, new_value=payload.role)
    db.commit()
    u = db.query(User).filter(User.id == m.user_id).first()
    return EmployeeOut(membership_id=m.id, user=u, role=m.role, is_active=m.is_active)


@router.post("/{membership_id}/reset-password", response_model=EmployeeOut)
def reset_password(membership_id: int, payload: EmployeeResetRequest,
                   ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-26.4: owner resets an employee's password (then shares it out-of-band)."""
    _owner(ctx)
    m = db.query(UserBusiness).filter(UserBusiness.id == membership_id,
                                      UserBusiness.business_id == ctx.business_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    u = db.query(User).filter(User.id == m.user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.hashed_password = hash_password(payload.new_password)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="employee.reset_password",
                resource="user", resource_id=str(u.id))
    db.commit()
    db.refresh(u)
    return EmployeeOut(membership_id=m.id, user=u, role=m.role, is_active=m.is_active)


@router.delete("/{membership_id}")
def remove(membership_id: int, ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    _owner(ctx)
    m = db.query(UserBusiness).filter(UserBusiness.id == membership_id,
                                      UserBusiness.business_id == ctx.business_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    if m.role == "Owner":
        raise HTTPException(status_code=400, detail="Cannot remove Owner membership")
    db.delete(m)
    write_audit(db, business_id=ctx.business_id, user_id=ctx.user.id, action="employee.remove",
                resource="user", resource_id=str(m.user_id))
    db.commit()
    return {"message": "Removed"}
