import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
import aiofiles

from celery import current_task
from app.celery_app import celery_app
from app.models import get_db, User, Mailbox, Alias, Email, EmailAttachment, EmailStatus
from app.utils import get_logger
from app.config import settings

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(
    self,
    user_id: int,
    recipient: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[list] = None,
    email_id: Optional[int] = None
) -> Dict[str, Any]:
    """Send email asynchronously"""
    try:
        logger.info(f"Starting email send task for user {user_id} to {recipient}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check usage limits
        if not check_email_usage_limit(user_id, db):
            raise ValueError(f"Email usage limit exceeded for user {user_id}")
        
        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = user.email
        message["To"] = recipient
        
        # Add text body
        text_part = MIMEText(body_text, "plain")
        message.attach(text_part)
        
        # Add HTML body if provided
        if body_html:
            html_part = MIMEText(body_html, "html")
            message.attach(html_part)
        
        # Add attachments if provided
        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {os.path.basename(attachment_path)}"
                        )
                        message.attach(part)
        
        # Send email via SMTP
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        async def send_async():
            async with aiosmtplib.SMTP(
                hostname=smtp_host,
                port=smtp_port,
                use_tls=smtp_use_tls
            ) as smtp:
                if smtp_user and smtp_password:
                    await smtp.login(smtp_user, smtp_password)
                
                await smtp.send_message(message)
        
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(send_async())
        finally:
            loop.close()
        
        # Update email status in database
        if email_id:
            email = db.query(Email).filter(Email.id == email_id).first()
            if email:
                email.status = EmailStatus.SENT
                email.received_at = datetime.utcnow()
                db.commit()
        
        # Update usage tracking
        update_email_usage(user_id, db)
        
        logger.info(f"Email sent successfully from {user.email} to {recipient}")
        
        return {
            "success": True,
            "message": "Email sent successfully",
            "task_id": current_task.request.id,
            "user_id": user_id,
            "recipient": recipient
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        
        # Update email status to failed
        if email_id:
            try:
                db = next(get_db())
                email = db.query(Email).filter(Email.id == email_id).first()
                if email:
                    email.status = EmailStatus.FAILED
                    email.received_at = datetime.utcnow()
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update email status: {db_error}")
        
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
async def receive_email_task(self, user_id: int) -> Dict[str, Any]:
    """Receive emails asynchronously"""
    try:
        logger.info(f"Starting email receive task for user {user_id}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Simulate email receiving (in real implementation, this would connect to IMAP)
        # For now, we'll just return existing emails from database
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get user's inbox
        inbox = db.query(Mailbox).filter(
            Mailbox.user_id == user_id,
            Mailbox.name == "Inbox"
        ).first()
        
        if not inbox:
            inbox = Mailbox(
                user_id=user_id,
                name="Inbox",
                email_address=user.email
            )
            db.add(inbox)
            db.commit()
        
        # Get existing emails from database
        emails = db.query(Email).filter(
            Email.user_id == user_id,
            Email.mailbox_id == inbox.id
        ).order_by(Email.received_at.desc()).all()
        
        result = []
        for email in emails:
            email_data = {
                "id": email.id,
                "sender": email.sender,
                "recipient": email.recipient,
                "subject": email.subject,
                "body_text": email.body_text,
                "status": email.status.value,
                "is_read": email.is_read,
                "is_spam": email.is_spam,
                "created_at": email.created_at.isoformat(),
                "received_at": email.received_at.isoformat() if email.received_at else None,
                "attachments": []
            }
            
            # Get attachments
            for attachment in email.attachments:
                email_data["attachments"].append({
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "file_size": attachment.file_size,
                    "content_type": attachment.content_type
                })
            
            result.append(email_data)
        
        logger.info(f"Received {len(emails)} emails for user {user_id}")
        
        return {
            "success": True,
            "message": f"Received {len(emails)} emails",
            "task_id": current_task.request.id,
            "user_id": user_id,
            "email_count": len(emails)
        }
        
    except Exception as e:
        logger.error(f"Failed to receive emails: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def cleanup_expired_tokens() -> Dict[str, Any]:
    """Clean up expired email verification and password reset tokens"""
    try:
        db = next(get_db())
        from app.models import EmailVerificationToken, PasswordResetToken
        
        now = datetime.utcnow()
        
        # Clean up expired email verification tokens
        expired_email_tokens = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < now
        ).all()
        
        for token in expired_email_tokens:
            db.delete(token)
        
        # Clean up expired password reset tokens
        expired_password_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < now
        ).all()
        
        for token in expired_password_tokens:
            db.delete(token)
        
        db.commit()
        
        logger.info(f"Cleaned up {len(expired_email_tokens)} email tokens and {len(expired_password_tokens)} password tokens")
        
        return {
            "success": True,
            "message": f"Cleaned up {len(expired_email_tokens)} email tokens and {len(expired_password_tokens)} password tokens"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to cleanup tokens: {str(e)}"
        }

def check_email_usage_limit(user_id: int, db) -> bool:
    """Check if user has exceeded email usage limit"""
    from app.models import UserUsage
    
    # Get user's plan
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Get current usage
    usage = db.query(UserUsage).filter(
        UserUsage.user_id == user_id,
        UserUsage.month == datetime.utcnow().strftime("%Y-%m")
    ).first()
    
    if not usage:
        usage = UserUsage(
            user_id=user_id,
            month=datetime.utcnow().strftime("%Y-%m"),
            emails_sent=0,
            emails_received=0
        )
        db.add(usage)
        db.commit()
    
    # Check plan limits
    from app.plans import PlanFeatures
    plan_features = PlanFeatures.get_plan_features(user.plan.value)
    
    if user.plan.value == "enterprise":
        return True  # Unlimited for enterprise
    
    max_emails = plan_features.get("max_emails_per_month", 300)
    return usage.emails_sent < max_emails

def update_email_usage(user_id: int, db):
    """Update email usage tracking"""
    from app.models import UserUsage
    
    # Get or create usage record
    usage = db.query(UserUsage).filter(
        UserUsage.user_id == user_id,
        UserUsage.month == datetime.utcnow().strftime("%Y-%m")
    ).first()
    
    if not usage:
        usage = UserUsage(
            user_id=user_id,
            month=datetime.utcnow().strftime("%Y-%m"),
            emails_sent=0,
            emails_received=0
        )
        db.add(usage)
    
    usage.emails_sent += 1
    db.commit()