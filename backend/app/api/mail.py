from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import tempfile
import os

from app.models import get_db, User
from app.api.auth import get_current_user
from app.services.mail import email_service
from app.utils import get_logger
from app.plans import PlanFeatures

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

class SendEmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body_text: str
    body_html: Optional[str] = None

class CreateAliasRequest(BaseModel):
    alias_name: str
    is_disposable: bool = False
    expires_hours: Optional[int] = None

class EmailResponse(BaseModel):
    id: int
    sender: str
    recipient: str
    subject: str
    body_text: Optional[str]
    status: str
    is_read: bool
    is_spam: bool
    created_at: str
    received_at: Optional[str]
    attachments: List[dict]

class AliasResponse(BaseModel):
    id: int
    alias_name: str
    alias_email: str
    is_disposable: bool
    created_at: str
    expires_at: Optional[str]

@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send email"""
    try:
        result = await email_service.send_email(
            user_id=current_user.id,
            recipient=request.recipient,
            subject=request.subject,
            body_text=request.body_text,
            body_html=request.body_html,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

@router.post("/send-with-attachments")
async def send_email_with_attachments(
    recipient: EmailStr = Form(...),
    subject: str = Form(...),
    body_text: str = Form(...),
    body_html: Optional[str] = Form(None),
    attachments: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send email with attachments"""
    try:
        # Check file size limits
        plan_features = PlanFeatures.get_plan_features(current_user.plan.value)
        max_upload_size = plan_features["max_upload_size_mb"]
        
        attachment_paths = []
        
        if attachments:
            for attachment in attachments:
                # Check file size
                file_size = len(await attachment.read())
                await attachment.seek(0)  # Reset file pointer
                
                if max_upload_size != "unlimited" and file_size > max_upload_size * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds limit of {max_upload_size}MB"
                    )
                
                # Save temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{attachment.filename}") as tmp_file:
                    content = await attachment.read()
                    tmp_file.write(content)
                    attachment_paths.append(tmp_file.name)
        
        result = await email_service.send_email(
            user_id=current_user.id,
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=attachment_paths,
            db=db
        )
        
        # Clean up temporary files
        for path in attachment_paths:
            try:
                os.unlink(path)
            except:
                pass
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending email with attachments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

@router.get("/inbox", response_model=List[EmailResponse])
async def get_inbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get inbox emails"""
    try:
        emails = await email_service.receive_emails(current_user.id, db)
        return emails
        
    except Exception as e:
        logger.error(f"Error getting inbox: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inbox"
        )

@router.post("/alias", response_model=dict)
async def create_alias(
    request: CreateAliasRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create email alias"""
    try:
        result = await email_service.create_alias(
            user_id=current_user.id,
            alias_name=request.alias_name,
            is_disposable=request.is_disposable,
            expires_hours=request.expires_hours,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating alias: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alias"
        )

@router.delete("/alias/{alias_id}")
async def delete_alias(
    alias_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete email alias"""
    try:
        result = await email_service.delete_alias(
            user_id=current_user.id,
            alias_id=alias_id,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting alias: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alias"
        )

@router.get("/aliases", response_model=List[AliasResponse])
async def get_aliases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's aliases"""
    try:
        aliases = await email_service.get_aliases(current_user.id, db)
        return aliases
        
    except Exception as e:
        logger.error(f"Error getting aliases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve aliases"
        )

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread email count"""
    try:
        emails = await email_service.receive_emails(current_user.id, db)
        unread_count = sum(1 for email in emails if not email["is_read"])
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )

@router.post("/mark-read/{email_id}")
async def mark_email_as_read(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark email as read"""
    try:
        from app.models import Email
        
        email = db.query(Email).filter(
            Email.id == email_id,
            Email.user_id == current_user.id
        ).first()
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email.is_read = True
        db.commit()
        
        return {"message": "Email marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking email as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark email as read"
        )

@router.post("/mark-spam/{email_id}")
async def mark_email_as_spam(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark email as spam"""
    try:
        from app.models import Email
        
        email = db.query(Email).filter(
            Email.id == email_id,
            Email.user_id == current_user.id
        ).first()
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        email.is_spam = True
        db.commit()
        
        return {"message": "Email marked as spam"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking email as spam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark email as spam"
        )