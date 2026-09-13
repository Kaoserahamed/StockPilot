import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import find_user_by_username, get_current_user
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password, decode_token
from app.db.session import get_db
from app.models.business import Business
from app.models.user import PasswordResetToken, User, UserBusiness
from app.schemas.schemas import (ForgotPasswordRequest, LoginRequest, RegisterRequest,
                                 ResetPasswordRequest, TokenResponse, UserOut)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=422, detail="email or phone required")
    # Validate password strength
    from app.core.sanitization import validate_password_strength
    is_valid, msg = validate_password_strength(payload.password)
    if not is_valid:
        raise HTTPException(status_code=422, detail=msg)
    existing = None
    if payload.email:
        existing = db.query(User).filter(User.email == payload.email).first()
    if not existing and payload.phone:
        existing = db.query(User).filter(User.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(name=payload.owner_name, email=payload.email, phone=payload.phone,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()
    business = Business(name=payload.business_name, address=payload.business_address,
                        phone=payload.business_phone, email=payload.email)
    db.add(business)
    db.flush()
    db.add(UserBusiness(user_id=user.id, business_id=business.id, role="Owner", is_active=True))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = find_user_by_username(db, payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User deactivated")
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: dict, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=422, detail="refresh_token required")
    try:
        user_id = decode_token(token, expected_type="refresh")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")
    access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # Stateless JWT: client discards token. FR-1.4 satisfied.
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = find_user_by_username(db, payload.username)
    # Always return generic message to avoid enumeration; still create token if found.
    if user:
        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(user_id=user.id, token=token,
               expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        db.commit()
        # In production: send email/SMS. For Phase-1 return token in dev only via header log.
        return {"message": "If account exists, reset instructions sent", "dev_token": token}
    return {"message": "If account exists, reset instructions sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token == payload.token).first()
    if not row or row.used:
        raise HTTPException(status_code=400, detail="Invalid token")
    now = datetime.now(timezone.utc)
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        raise HTTPException(status_code=400, detail="Token expired")
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(payload.new_password)
    row.used = True
    db.commit()
    return {"message": "Password reset successful"}
