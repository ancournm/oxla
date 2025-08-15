from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from app.config import settings
from app.models import get_db, Base, engine
from app.api import auth_router
from app.api.mail import router as mail_router
from app.api.metrics import router as metrics_router
from app.api.drive import router as drive_router
from app.middleware import PlanMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Oxlas Suite Backend API",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add plan middleware (optional - can be applied per route)
plan_middleware = PlanMiddleware()

# Auth middleware to set current user in request state
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for certain paths
    skip_paths = ["/docs", "/redoc", "/openapi.json", "/auth/register", "/auth/login"]
    
    if request.url.path in skip_paths:
        response = await call_next(request)
        return response
    
    # Get authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        response = await call_next(request)
        return response
    
    try:
        from app.utils import AuthManager
        from app.models import User
        
        # Verify token
        token = auth_header.split(" ")[1]
        payload = AuthManager.verify_token(token)
        email = payload.get("sub")
        
        # Get user from database
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == email).first()
        
        if user and user.is_active:
            # Set user in request state
            request.state.current_user = user
        
    except Exception:
        # If token is invalid, continue without setting user
        pass
    
    response = await call_next(request)
    return response

# Include API routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(mail_router, prefix="/mail", tags=["Email"])
app.include_router(metrics_router, prefix="/metrics", tags=["Monitoring"])
app.include_router(drive_router, prefix="/drive", tags=["Drive"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Oxlas Suite Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "oxlas-suite-backend"}

# Example protected route with plan requirements
@app.get("/api/protected")
async def protected_route(request: Request):
    """Example protected route"""
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = request.state.current_user
    return {
        "message": "Access granted",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "plan": user.plan.value
        }
    }

@app.get("/api/pro-feature")
async def pro_feature(request: Request):
    """Example route requiring Pro plan"""
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = request.state.current_user
    if user.plan.value not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403, 
            detail="This feature requires Pro plan or higher"
        )
    
    return {"message": "Pro feature accessed successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )