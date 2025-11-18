from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Callable, Optional
from app.plans import PlanFeatures
from app.models import User

class PlanMiddleware:
    def __init__(self, required_plan: str = "free"):
        self.required_plan = required_plan
    
    async def __call__(self, request: Request, call_next: Callable):
        # Get current user from request state (set by auth middleware)
        current_user: Optional[User] = getattr(request.state, "current_user", None)
        
        if not current_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
        
        # Check if user has required plan level
        if not self._check_plan_access(current_user.plan.value):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": f"This feature requires {self.required_plan} plan or higher",
                    "current_plan": current_user.plan.value,
                    "required_plan": self.required_plan
                }
            )
        
        response = await call_next(request)
        return response
    
    def _check_plan_access(self, user_plan: str) -> bool:
        """Check if user's plan meets the required level"""
        plan_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
        required_level = plan_hierarchy.get(self.required_plan, 0)
        user_level = plan_hierarchy.get(user_plan, 0)
        
        return user_level >= required_level

def require_plan(required_plan: str = "free"):
    """Decorator to require specific plan level"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get current user
            current_user: Optional[User] = getattr(request.state, "current_user", None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check plan access
            middleware = PlanMiddleware(required_plan)
            if not middleware._check_plan_access(current_user.plan.value):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This feature requires {required_plan} plan or higher"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def check_feature_access(feature: str):
    """Decorator to check access to specific feature"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get current user
            current_user: Optional[User] = getattr(request.state, "current_user", None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check feature access
            if not PlanFeatures.check_feature_access(current_user.plan.value, feature):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature}' not available in {current_user.plan.value} plan"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator