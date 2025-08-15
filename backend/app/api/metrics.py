from fastapi import APIRouter, Response
from app.tasks.monitoring_tasks import get_prometheus_metrics, get_queue_metrics
from app.middleware import get_email_usage_stats
from app.models import get_db, User
from app.utils import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    try:
        metrics = get_prometheus_metrics()
        return Response(content=metrics, media_type="text/plain")
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        return Response(content="# Error generating metrics", media_type="text/plain")

@router.get("/queue-metrics")
async def get_queue_metrics_endpoint():
    """Get queue metrics"""
    try:
        metrics = get_queue_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get queue metrics: {str(e)}")
        return {"queue_length": 0, "timestamp": "error"}

@router.get("/usage-stats/{user_id}")
async def get_usage_stats(user_id: int):
    """Get email usage statistics for a user"""
    try:
        stats = get_email_usage_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get usage stats: {str(e)}")
        return {"error": "Internal error"}

@router.get("/system-stats")
async def get_system_stats():
    """Get system-wide statistics"""
    try:
        db = next(get_db())
        
        # User statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        
        # Plan distribution
        free_users = db.query(User).filter(User.plan == "free").count()
        pro_users = db.query(User).filter(User.plan == "pro").count()
        enterprise_users = db.query(User).filter(User.plan == "enterprise").count()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "plan_distribution": {
                    "free": free_users,
                    "pro": pro_users,
                    "enterprise": enterprise_users
                }
            },
            "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {str(e)}")
        return {"error": "Internal error"}