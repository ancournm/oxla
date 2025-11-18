import os
from datetime import datetime, timedelta
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import redis

from app.celery_app import celery_app
from app.models import get_db, User, UserUsage
from app.utils import get_logger

logger = get_logger(__name__)

# Prometheus metrics
EMAILS_SENT_COUNTER = Counter('oxlas_emails_sent_total', 'Total emails sent', ['plan', 'status'])
EMAILS_RECEIVED_COUNTER = Counter('oxlas_emails_received_total', 'Total emails received', ['plan'])
ACTIVE_USERS_GAUGE = Gauge('oxlas_active_users', 'Number of active users')
QUEUE_LATENCY_HISTOGRAM = Histogram('oxlas_queue_latency_seconds', 'Task queue latency')
FAILED_JOBS_COUNTER = Counter('oxlas_failed_jobs_total', 'Total failed jobs', ['task_type'])

# Redis client for rate limiting
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', '6379')),
    db=2,  # Use DB 2 for rate limiting
    decode_responses=True
)

@celery_app.task
def reset_monthly_usage() -> Dict[str, Any]:
    """Reset monthly usage counters for all users"""
    try:
        db = next(get_db())
        
        # Get current month
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Reset usage for all users
        users = db.query(User).all()
        reset_count = 0
        
        for user in users:
            # Check if usage record exists for current month
            usage = db.query(UserUsage).filter(
                UserUsage.user_id == user.id,
                UserUsage.month == current_month
            ).first()
            
            if usage:
                usage.emails_sent = 0
                usage.emails_received = 0
                reset_count += 1
        
        db.commit()
        
        logger.info(f"Reset monthly usage for {reset_count} users")
        
        return {
            "success": True,
            "message": f"Reset monthly usage for {reset_count} users",
            "reset_count": reset_count
        }
        
    except Exception as e:
        logger.error(f"Failed to reset monthly usage: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to reset monthly usage: {str(e)}"
        }

@celery_app.task
def cleanup_old_logs() -> Dict[str, Any]:
    """Clean up old log files"""
    try:
        import shutil
        from pathlib import Path
        
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {"success": True, "message": "No logs directory found"}
        
        # Remove logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        removed_count = 0
        
        for log_file in logs_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                removed_count += 1
        
        logger.info(f"Cleaned up {removed_count} old log files")
        
        return {
            "success": True,
            "message": f"Cleaned up {removed_count} old log files",
            "removed_count": removed_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to cleanup old logs: {str(e)}"
        }

@celery_app.task
def update_metrics() -> Dict[str, Any]:
    """Update Prometheus metrics"""
    try:
        db = next(get_db())
        
        # Update active users gauge
        active_users = db.query(User).filter(User.is_active == True).count()
        ACTIVE_USERS_GAUGE.set(active_users)
        
        # Get email statistics by plan
        from app.models import Email, EmailStatus
        
        plans = ["free", "pro", "enterprise"]
        for plan in plans:
            # Sent emails
            sent_count = db.query(Email).join(User).filter(
                User.plan == plan,
                Email.status == EmailStatus.SENT,
                Email.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            EMAILS_SENT_COUNTER.labels(plan=plan, status="sent").inc(sent_count)
            
            # Failed emails
            failed_count = db.query(Email).join(User).filter(
                User.plan == plan,
                Email.status == EmailStatus.FAILED,
                Email.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            EMAILS_SENT_COUNTER.labels(plan=plan, status="failed").inc(failed_count)
        
        logger.info("Metrics updated successfully")
        
        return {
            "success": True,
            "message": "Metrics updated successfully",
            "active_users": active_users
        }
        
    except Exception as e:
        logger.error(f"Failed to update metrics: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to update metrics: {str(e)}"
        }

def check_rate_limit(user_id: int, action: str = "email") -> bool:
    """Check if user has exceeded rate limit"""
    try:
        # Get user's plan
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Get rate limits by plan
        rate_limits = {
            "free": {"email": 5},      # 5 emails per minute
            "pro": {"email": 20},      # 20 emails per minute
            "enterprise": {"email": 100}  # 100 emails per minute
        }
        
        limit = rate_limits.get(user.plan.value, rate_limits["free"])
        limit_key = f"rate_limit:{user_id}:{action}"
        
        # Check current count
        current_count = redis_client.get(limit_key)
        if current_count is None:
            redis_client.setex(limit_key, 60, 1)  # 1 minute window
            return True
        
        current_count = int(current_count)
        if current_count >= limit:
            return False
        
        # Increment count
        redis_client.incr(limit_key)
        return True
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {str(e)}")
        return True  # Allow on error

def get_queue_metrics() -> Dict[str, Any]:
    """Get queue metrics for monitoring"""
    try:
        from celery.events.state import State
        from celery.events import EventReceiver
        import socket
        
        # Connect to Redis to get queue stats
        queue_length = redis_client.llen("celery")
        
        return {
            "queue_length": queue_length,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue metrics: {str(e)}")
        return {"queue_length": 0, "timestamp": datetime.utcnow().isoformat()}

def get_prometheus_metrics() -> str:
    """Get Prometheus metrics in text format"""
    try:
        return generate_latest().decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {str(e)}")
        return ""