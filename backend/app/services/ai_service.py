"""FR-30..FR-37 Phase 5 AI: deterministic analytics + optional Gemini wrapper."""
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy.orm import Session

from app.services import finance_service as f


def _business_snapshot(db: Session, business_id: int, preset: str = "month") -> dict:
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    profit = f.profit_summary(db, business_id, start, end)
    trend = f.sales_trend(db, business_id, start, end)
    top = f.top_products(db, business_id, start, end, limit=5)
    customers = f.customer_stats(db, business_id, start, end, limit=5)
    suppliers = f.supplier_stats(db, business_id, start, end)
    inv = f.inventory_value(db, business_id)
    return {"preset": preset, "profit": profit, "trend": trend,
            "top_products": top, "customers": customers,
            "suppliers": suppliers, "inventory": inv}


def _rule_answer(question: str, snap: dict) -> str:
    q = question.lower()
    p = snap["profit"]
    if any(k in q for k in ("low stock", "running low", "out of stock", "reorder", "inventory")):
        inv = snap["inventory"]
        msg = (f"Inventory: {inv['units']} units across {inv['skus']} SKUs "
               f"(cost value {inv['cost_value']}, retail {inv['retail_value']}).")
        if snap["top_products"]:
            t = snap["top_products"][0]
            msg += (f" Fastest mover: {t['product_name']} ({t['quantity']} sold). "
                    "Verify its on-hand quantity against min-stock and reorder if below.")
        return msg
    if "customer" in q:
        if not snap["customers"]:
            return "No customer-tagged sales in this period."
        c = snap["customers"][0]
        return (f"Top customer: {c['customer_name']} spent {c['spent']} "
                f"across {c['orders']} order(s).")
    if "supplier" in q or "purchase" in q:
        if not snap["suppliers"]:
            return "No purchases recorded in this period."
        s = snap["suppliers"][0]
        return (f"Top supplier: {s['supplier_name']} supplied {s['purchased']} "
                f"({s['orders']} order(s), outstanding {s['outstanding']}).")
    if "expense" in q or "largest" in q:
        return (f"Total expenses: {p['total_expenses']}. Gross profit {p['gross_profit']}, "
                "net profit {np}. Check the expenses report by category.".format(np=p["net_profit"]))
    if "profit" in q or "loss" in q or "decrease" in q or "why" in q:
        return (f"Revenue (net) {p['net_revenue']} from {p['orders']} order(s); "
                f"COGS {p['cogs']}; expenses {p['total_expenses']} => gross {p['gross_profit']}, "
                f"net {p['net_profit']}. Compare trend buckets with the prior period.")
    if "sold" in q or "most" in q or "best" in q or "top product" in q:
        if not snap["top_products"]:
            return "No product sales in this period."
        t = snap["top_products"][0]
        return (f"Best seller: {t['product_name']} - {t['quantity']} unit(s), "
                f"revenue {t['revenue']}, est. profit {t['profit']}.")
    return (f"Sales: {p['orders']} order(s), gross revenue {p['gross_revenue']}, "
            f"refunded {p['refunded']}, net revenue {p['net_revenue']}. "
            f"Gross profit {p['gross_profit']}, net profit {p['net_profit']}.")


def maybe_polish_with_gemini(question: str, draft: str, snap: dict) -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return draft
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=key)
        model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
        resp = model.generate_content(
            "You are a concise POS business assistant. Answer ONLY from the data. "
            "Keep it under 150 words.\n"
            f"Question: {question}\nData: {snap}\nDraft: {draft}")
        text = (getattr(resp, "text", "") or "").strip()
        return text or draft
    except Exception:
        return draft


def answer_question(db: Session, business_id: int, question: str, preset: str = "month"):
    snap = _business_snapshot(db, business_id, preset)
    draft = _rule_answer(question, snap)
    return maybe_polish_with_gemini(question, draft, snap), snap
