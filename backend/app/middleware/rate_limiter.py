from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Callable, Optional
from app.tasks.monitoring_tasks import check_rate_limit
from app.plans import PlanFeatures
from app.models import get_db, UserUsage, User
from datetime import datetime
from app.utils import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware:
    def __init__(self, action: str = "email"):
        self.action = action
    
    async def __call__(self, request: Request, call_next: Callable):
        # Get current user from request state (set by auth middleware)
        from app.models import User
        current_user: Optional[User] = getattr(request.state, "current_user", None)
        
        if not current_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
        
        # Check rate limit
        if not check_rate_limit(current_user.id, self.action):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded for {self.action}",
                    "current_plan": current_user.plan.value,
                    "retry_after": 60
                }
            )
        
        # Check monthly usage limit
        db = next(get_db())
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = db.query(UserUsage).filter(
            UserUsage.user_id == current_user.id,
            UserUsage.month == current_month
        ).first()
        
        if usage:
            if not PlanFeatures.check_email_monthly_limit(current_user.plan.value, usage.emails_sent):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Monthly email limit exceeded",
                        "current_plan": current_user.plan.value,
                        "emails_sent": usage.emails_sent,
                        "limit": PlanFeatures.get_plan_features(current_user.plan.value)["max_emails_per_month"]
                    }
                )
        
        response = await call_next(request)
        return response

def check_email_limits(user_id: int) -> dict:
    """Check both rate and monthly limits for email sending"""
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"allowed": False, "reason": "User not found"}
        
        # Check rate limit
        if not check_rate_limit(user_id, "email"):
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "retry_after": 60
            }
        
        # Check monthly usage limit
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == current_month
        ).first()
        
        emails_sent = usage.emails_sent if usage else 0
        
        if not PlanFeatures.check_email_monthly_limit(user.plan.value, emails_sent):
            plan_features = PlanFeatures.get_plan_features(user.plan.value)
            return {
                "allowed": False,
                "reason": "monthly_limit_exceeded",
                "emails_sent": emails_sent,
                "limit": plan_features["max_emails_per_month"]
            }
        
        return {
            "allowed": True,
            "emails_sent": emails_sent,
            "remaining": PlanFeatures.get_plan_features(user.plan.value)["max_emails_per_month"] - emails_sent
        }
        
    except Exception as e:
        logger.error(f"Error checking email limits: {str(e)}")
        return {"allowed": False, "reason": "internal_error"}

def get_email_usage_stats(user_id: int) -> dict:
    """Get email usage statistics for a user"""
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"error": "User not found"}
        
        # Get current month usage
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == current_month
        ).first()
        
        emails_sent = usage.emails_sent if usage else 0
        emails_received = usage.emails_received if usage else 0
        
        # Get plan limits
        plan_features = PlanFeatures.get_plan_features(user.plan.value)
        max_emails_per_month = plan_features["max_emails_per_month"]
        
        return {
            "user_id": user_id,
            "plan": user.plan.value,
            "current_month": current_month,
            "emails_sent": emails_sent,
            "emails_received": emails_received,
            "max_emails_per_month": max_emails_per_month,
            "remaining_emails": max_emails_per_month - emails_sent if max_emails_per_month != "unlimited" else "unlimited",
            "usage_percentage": (emails_sent / max_emails_per_month * 100) if max_emails_per_month != "unlimited" else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting email usage stats: {str(e)}")
        return {"error": "Internal error"}