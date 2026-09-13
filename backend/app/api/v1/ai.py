from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.saas import AIRecommendation
from app.schemas.schemas import (AIChatRequest, AIChatResponse, AIRecommendationOut,
                                  AIRecommendationUpdate, AISummaryRequest)
from app.services import ai_service, ai2_service, ai3_service
from app.services import finance_service as f

router = APIRouter(prefix="/ai", tags=["ai"])


def _save(db: Session, business_id: int, kind: str, title: str, body: str) -> AIRecommendation:
    rec = AIRecommendation(business_id=business_id, kind=kind, title=title, body=body)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def _check(ctx: Context):
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.post("/chat", response_model=AIChatResponse)
def chat(payload: AIChatRequest, ctx: Context = Depends(get_current_context),
         db: Session = Depends(get_db)):
    """FR-30 + FR-31: natural-language business Q&A over live business data."""
    _check(ctx)
    answer, snap = ai_service.answer_question(db, ctx.business_id, payload.question)
    rid = None
    if payload.save:
        rid = _save(db, ctx.business_id, "chat", payload.question[:200], answer).id
    return AIChatResponse(answer=answer, data=snap, recommendation_id=rid)


@router.get("/insights")
def insights(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
             preset: str = Query("month"), save: bool = False):
    """FR-32: auto business insights from sales/expense/demand data."""
    _check(ctx)
    out = ai2_service.business_insights(db, ctx.business_id, preset)
    if save:
        body = "; ".join(i["title"] for i in out["insights"])
        _save(db, ctx.business_id, "insight", "Insights %s" % preset, body)
    return out


@router.get("/forecast")
def forecast(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
             product_id: int | None = None, days: int = Query(30, ge=1, le=365)):
    """FR-33: predicted demand per product + history-derived rate."""
    _check(ctx)
    return ai2_service.forecast_demand(db, ctx.business_id, product_id, days)


@router.get("/reorder-recommendations")
def reorder(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
            days: int = Query(30, ge=1, le=365)):
    """FR-34: reorder quantities from stock + velocity + min-stock + forecast."""
    _check(ctx)
    return ai3_service.reorder_recommendations(db, ctx.business_id, days)


@router.get("/anomalies")
def anomalies(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-35: unusual sales patterns with supporting info."""
    _check(ctx)
    return ai3_service.detect_anomalies(db, ctx.business_id)


@router.post("/summarize")
def summarize(payload: AISummaryRequest, ctx: Context = Depends(get_current_context),
              db: Session = Depends(get_db)):
    """FR-36: NL summary of a sales/expense/inventory/profit report."""
    _check(ctx)
    preset = payload.preset if payload.preset in f.PRESETS else "month"
    start, end = f.resolve_range(preset)
    if payload.kind == "profit":
        data = f.profit_summary(db, ctx.business_id, start, end)
    elif payload.kind == "sales":
        data = {"summary": f.revenue_summary(db, ctx.business_id, start, end)}
    elif payload.kind == "expenses":
        rows = db.query(__import__("app.models.finance", fromlist=["Expense"]).Expense).filter(
            __import__("app.models.finance", fromlist=["Expense"]).Expense.business_id
            == ctx.business_id).all()
        data = {"summary": f.expenses_total(db, ctx.business_id, start, end),
                "rows": [{"id": e.id} for e in rows]}
    else:
        data = {"summary": f.inventory_value(db, ctx.business_id)}
    summary = ai3_service.summarize_report(payload.kind, data)
    rec = _save(db, ctx.business_id, "summary", "%s summary %s" % (payload.kind, preset), summary)
    return {"kind": payload.kind, "preset": preset, "summary": summary,
            "data": data, "recommendation_id": rec.id}


@router.get("/recommendations", response_model=list[AIRecommendationOut])
def list_recs(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-37.3: review previous AI recommendations."""
    _check(ctx)
    return db.query(AIRecommendation).filter(
        AIRecommendation.business_id == ctx.business_id).order_by(
        AIRecommendation.id.desc()).limit(200).all()


@router.patch("/recommendations/{rid}", response_model=AIRecommendationOut)
def update_rec(rid: int, payload: AIRecommendationUpdate,
               ctx: Context = Depends(get_current_context), db: Session = Depends(get_db)):
    """FR-37.5: mark recommendations reviewed / acted upon."""
    _check(ctx)
    rec = db.query(AIRecommendation).filter(
        AIRecommendation.id == rid, AIRecommendation.business_id == ctx.business_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            setattr(rec, k, v)
    db.commit()
    db.refresh(rec)
    return rec
