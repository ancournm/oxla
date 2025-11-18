import os
import uuid
import aiofiles
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
import aioimaplib
import re
from pathlib import Path

from app.tasks.email_tasks import send_email_task
from app.middleware import check_email_limits
from app.models import get_db, User, Mailbox, Alias, Email, EmailAttachment, EmailStatus
from app.utils import get_logger
from app.config import settings
from app.plans import PlanFeatures

logger = get_logger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        self.imap_host = os.getenv("IMAP_HOST", "localhost")
        self.imap_port = int(os.getenv("IMAP_PORT", "993"))
        self.imap_use_ssl = os.getenv("IMAP_USE_SSL", "true").lower() == "true"
        
        self.storage_path = Path("storage")
        self.storage_path.mkdir(exist_ok=True)
        
        self.spam_keywords = [
            "spam", "scam", "phishing", "winner", "congratulations",
            "urgent", "act now", "limited time", "free money", "click here"
        ]
    
    async def send_email(
        self,
        user_id: int,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        db=None
    ) -> Dict[str, Any]:
        """Send email via task queue"""
        if db is None:
            db = next(get_db())
        
        # Check usage limits
        limit_check = check_email_limits(user_id)
        if not limit_check["allowed"]:
            if limit_check["reason"] == "rate_limit_exceeded":
                raise ValueError(f"Rate limit exceeded. Retry after {limit_check.get('retry_after', 60)} seconds")
            elif limit_check["reason"] == "monthly_limit_exceeded":
                raise ValueError(f"Monthly email limit exceeded. Sent: {limit_check['emails_sent']}, Limit: {limit_check['limit']}")
            else:
                raise ValueError("Email sending not allowed")
        
        # Get user and check plan limits
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if user can send emails (basic check)
        if not PlanFeatures.check_feature_access(user.plan.value, "basic_email_features"):
            raise ValueError("Email sending not available in your plan")
        
        # Save email to database first
        sent_email = Email(
            user_id=user_id,
            mailbox_id=self._get_or_create_sent_mailbox(user_id, db),
            sender=user.email,
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            status=EmailStatus.PENDING,
            received_at=datetime.utcnow()
        )
        
        db.add(sent_email)
        db.commit()
        db.refresh(sent_email)
        
        # Queue email sending task
        task = send_email_task.delay(
            user_id=user_id,
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            email_id=sent_email.id
        )
        
        logger.info(f"Email queued for sending from {user.email} to {recipient}, task_id: {task.id}")
        
        return {
            "success": True,
            "message": "Email queued for sending",
            "email_id": sent_email.id,
            "task_id": task.id,
            "status": "pending"
        }
    
    async def receive_emails(self, user_id: int, db=None) -> List[Dict[str, Any]]:
        """Receive emails via IMAP-like API"""
        if db is None:
            db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
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
        
        # Simulate receiving emails (in real implementation, this would connect to IMAP)
        # For now, we'll just return existing emails from the database
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
        
        return result
    
    async def create_alias(
        self,
        user_id: int,
        alias_name: str,
        is_disposable: bool = False,
        expires_hours: Optional[int] = None,
        db=None
    ) -> Dict[str, Any]:
        """Create email alias"""
        if db is None:
            db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check plan limits
        current_aliases = db.query(Alias).filter(
            Alias.user_id == user_id,
            Alias.is_active == True
        ).count()
        
        if not PlanFeatures.check_feature_access(user.plan.value, "unlimited_aliases"):
            max_aliases = PlanFeatures.get_plan_features(user.plan.value)["max_aliases"]
            if current_aliases >= max_aliases:
                raise ValueError(f"Maximum aliases ({max_aliases}) reached for your plan")
        
        # Generate alias email
        base_email = user.email.split('@')[0]
        domain = user.email.split('@')[1]
        alias_email = f"{base_email}+{alias_name}@{domain}"
        
        # Check if alias already exists
        existing_alias = db.query(Alias).filter(
            Alias.alias_email == alias_email
        ).first()
        
        if existing_alias:
            raise ValueError("Alias already exists")
        
        # Create alias
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        new_alias = Alias(
            user_id=user_id,
            alias_name=alias_name,
            alias_email=alias_email,
            is_disposable=is_disposable,
            expires_at=expires_at
        )
        
        db.add(new_alias)
        db.commit()
        
        logger.info(f"Alias created for user {user.email}: {alias_email}")
        
        return {
            "success": True,
            "alias_id": new_alias.id,
            "alias_email": new_alias.alias_email,
            "alias_name": new_alias.alias_name,
            "is_disposable": new_alias.is_disposable,
            "expires_at": new_alias.expires_at.isoformat() if new_alias.expires_at else None
        }
    
    async def delete_alias(self, user_id: int, alias_id: int, db=None) -> Dict[str, Any]:
        """Delete email alias"""
        if db is None:
            db = next(get_db())
        
        alias = db.query(Alias).filter(
            Alias.id == alias_id,
            Alias.user_id == user_id
        ).first()
        
        if not alias:
            raise ValueError("Alias not found")
        
        alias.is_active = False
        db.commit()
        
        logger.info(f"Alias deleted for user {user_id}: {alias.alias_email}")
        
        return {
            "success": True,
            "message": "Alias deleted successfully"
        }
    
    async def get_aliases(self, user_id: int, db=None) -> List[Dict[str, Any]]:
        """Get user's aliases"""
        if db is None:
            db = next(get_db())
        
        aliases = db.query(Alias).filter(
            Alias.user_id == user_id,
            Alias.is_active == True
        ).all()
        
        result = []
        for alias in aliases:
            result.append({
                "id": alias.id,
                "alias_name": alias.alias_name,
                "alias_email": alias.alias_email,
                "is_disposable": alias.is_disposable,
                "created_at": alias.created_at.isoformat(),
                "expires_at": alias.expires_at.isoformat() if alias.expires_at else None
            })
        
        return result
    
    def _is_spam(self, email_content: str) -> bool:
        """Basic spam detection"""
        content_lower = email_content.lower()
        
        # Check for spam keywords
        for keyword in self.spam_keywords:
            if keyword in content_lower:
                return True
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\$\d+',  # Money amounts
            r'http://\S+',  # HTTP links
            r'click\s+here',  # Click here
            r'urgent',  # Urgent
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    def _get_or_create_sent_mailbox(self, user_id: int, db) -> int:
        """Get or create sent mailbox for user"""
        sent_mailbox = db.query(Mailbox).filter(
            Mailbox.user_id == user_id,
            Mailbox.name == "Sent"
        ).first()
        
        if not sent_mailbox:
            user = db.query(User).filter(User.id == user_id).first()
            sent_mailbox = Mailbox(
                user_id=user_id,
                name="Sent",
                email_address=user.email
            )
            db.add(sent_mailbox)
            db.commit()
            db.refresh(sent_mailbox)
        
        return sent_mailbox.id
    
    async def save_attachment(self, email_id: int, filename: str, file_data: bytes, content_type: str, db=None) -> Dict[str, Any]:
        """Save email attachment"""
        if db is None:
            db = next(get_db())
        
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.storage_path / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        # Save attachment record
        attachment = EmailAttachment(
            email_id=email_id,
            filename=filename,
            file_size=len(file_data),
            file_path=str(file_path),
            content_type=content_type
        )
        
        db.add(attachment)
        db.commit()
        
        return {
            "success": True,
            "attachment_id": attachment.id,
            "filename": filename,
            "file_size": len(file_data),
            "file_path": str(file_path)
        }

# Global email service instance
email_service = EmailService()