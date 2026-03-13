"""Billing API routes — Plans, subscriptions, invoices, usage."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user

router = APIRouter()

PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "credits_monthly": 50,
        "features": ["All modules (limited)", "Watermarked exports", "Community support", "5 projects"],
        "limits": {"max_projects": 5, "max_storage_mb": 500, "max_team_members": 1},
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 29,
        "price_yearly": 290,
        "credits_monthly": 2000,
        "features": ["All modules (full)", "No watermark", "Priority support", "Unlimited projects", "API access", "Custom brand kit"],
        "limits": {"max_projects": -1, "max_storage_mb": 50000, "max_team_members": 1},
    },
    "team": {
        "name": "Team",
        "price_monthly": 79,
        "price_yearly": 790,
        "credits_monthly": 10000,
        "features": ["Everything in Pro", "Team collaboration", "Shared assets", "Admin dashboard", "Workflow automation", "Priority rendering"],
        "limits": {"max_projects": -1, "max_storage_mb": 200000, "max_team_members": 10},
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 0,  # Custom pricing
        "price_yearly": 0,
        "credits_monthly": -1,  # Unlimited
        "features": ["Everything in Team", "SSO/SAML", "SLA guarantee", "Dedicated account manager", "White-label option", "Custom integrations", "On-premise deployment"],
        "limits": {"max_projects": -1, "max_storage_mb": -1, "max_team_members": -1},
    },
}

# Simulated invoices storage
invoices_db: dict[str, list] = {}


class SubscriptionRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"  # monthly or yearly


class CreditPurchase(BaseModel):
    amount: int  # number of credits to buy


@router.get("/plans")
async def get_plans():
    return {"plans": PLANS}


@router.get("/current")
async def get_current_subscription(user: dict = Depends(get_current_user)):
    plan = user.get("plan", "free")
    plan_details = PLANS.get(plan, PLANS["free"])
    return {
        "plan": plan,
        "plan_details": plan_details,
        "status": "active",
        "next_billing_date": "2026-04-13",
        "credits_remaining": 50 if plan == "free" else 2000,
    }


@router.post("/subscribe")
async def subscribe(req: SubscriptionRequest, user: dict = Depends(get_current_user)):
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Plan '{req.plan}' not found")
    if req.plan == "enterprise":
        return {"message": "Please contact sales@ominou.studio for enterprise pricing", "action": "contact_sales"}

    plan = PLANS[req.plan]
    price = plan["price_yearly"] if req.billing_cycle == "yearly" else plan["price_monthly"]

    return {
        "success": True,
        "subscription_id": f"sub_{uuid.uuid4().hex[:8]}",
        "plan": req.plan,
        "billing_cycle": req.billing_cycle,
        "price": price,
        "credits_added": plan["credits_monthly"],
        "message": f"Subscribed to {plan['name']} plan",
        "checkout_url": f"https://checkout.stripe.com/pay/ominou_{req.plan}",
    }


@router.post("/buy-credits")
async def buy_credits(req: CreditPurchase, user: dict = Depends(get_current_user)):
    price_per_credit = 0.05  # $0.05 per credit
    total = round(req.amount * price_per_credit, 2)
    return {
        "success": True,
        "credits_purchased": req.amount,
        "total_price": total,
        "checkout_url": f"https://checkout.stripe.com/pay/credits_{req.amount}",
    }


@router.get("/usage")
async def get_usage(user: dict = Depends(get_current_user)):
    return {
        "period": "2026-03",
        "credits_used": 23,
        "credits_remaining": 27,
        "breakdown": {
            "voice": {"tts": 5, "clone": 1, "dub": 0},
            "design": {"generate": 4, "remove_bg": 2, "template": 3},
            "code": {"generate": 3, "deploy": 0},
            "writer": {"blog": 2, "copy": 1, "social": 2},
            "music": {"generate": 0, "sfx": 0},
            "workflow": {"runs": 0},
        },
    }


@router.get("/invoices")
async def get_invoices(user: dict = Depends(get_current_user)):
    user_invoices = invoices_db.get(str(user["id"]), [])
    if not user_invoices:
        # Return sample invoice
        return {
            "invoices": [
                {
                    "id": "inv_sample01",
                    "date": "2026-03-01",
                    "amount": 29.00,
                    "status": "paid",
                    "description": "Pro Plan — March 2026",
                    "pdf_url": "/invoices/inv_sample01.pdf",
                },
            ]
        }
    return {"invoices": user_invoices}


@router.post("/cancel")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    return {
        "message": "Subscription cancelled. You'll retain access until end of current billing period.",
        "access_until": "2026-04-13",
        "plan_after": "free",
    }
