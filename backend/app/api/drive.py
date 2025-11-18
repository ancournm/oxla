from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import aiofiles
import tempfile
import os

from app.models import get_db, User
from app.api.auth import get_current_user
from app.services.drive import drive_service
from app.utils import get_logger
from app.plans import PlanFeatures

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

class FolderCreateRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None

class ShareCreateRequest(BaseModel):
    share_type: str = "view"  # "view" or "edit"
    expires_hours: Optional[int] = None

class FileResponse(BaseModel):
    id: int
    name: str
    file_size: int
    mime_type: str
    virus_scan_status: str
    created_at: str

class FolderResponse(BaseModel):
    id: int
    name: str
    path: str
    created_at: str

class DriveListResponse(BaseModel):
    folders: List[FolderResponse]
    files: List[FileResponse]

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file to drive"""
    try:
        # Check file size limits
        plan_features = PlanFeatures.get_plan_features(current_user.plan.value)
        max_upload_size = plan_features["max_upload_size_mb"]
        
        if max_upload_size != "unlimited" and file.size > max_upload_size * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds limit of {max_upload_size}MB"
            )
        
        result = await drive_service.upload_file(
            user_id=current_user.id,
            file=file,
            folder_id=folder_id,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.post("/upload-chunked")
async def upload_file_chunked(
    chunk_data: UploadFile = File(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    original_filename: str = Form(...),
    mime_type: str = Form(...),
    folder_id: Optional[int] = Form(None),
    upload_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file in chunks"""
    try:
        # Read chunk data
        chunk_content = await chunk_data.read()
        
        result = await drive_service.upload_file_chunked(
            user_id=current_user.id,
            chunk_data=chunk_content,
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            original_filename=original_filename,
            mime_type=mime_type,
            folder_id=folder_id,
            upload_id=upload_id,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading chunked file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload chunked file"
        )

@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download file from drive"""
    try:
        result = await drive_service.download_file(file_id, current_user.id, db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "File not found")
            )
        
        # Return file for download
        import os
        from fastapi.responses import FileResponse
        
        return FileResponse(
            path=result["file_path"],
            filename=result["filename"],
            media_type=result["mime_type"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete file from drive"""
    try:
        result = await drive_service.delete_file(file_id, current_user.id, db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "File not found")
            )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )

@router.post("/folders")
async def create_folder(
    request: FolderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create folder"""
    try:
        result = await drive_service.create_folder(
            user_id=current_user.id,
            name=request.name,
            parent_id=request.parent_id,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create folder"
        )

@router.get("/list", response_model=DriveListResponse)
async def list_files(
    folder_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List files and folders"""
    try:
        result = await drive_service.list_files(
            user_id=current_user.id,
            folder_id=folder_id,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )

@router.post("/share/{file_id}")
async def create_share_link(
    file_id: int,
    request: ShareCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create share link for file"""
    try:
        result = await drive_service.create_share_link(
            file_id=file_id,
            user_id=current_user.id,
            share_type=request.share_type,
            expires_hours=request.expires_hours,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating share link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link"
        )

@router.get("/share/{share_token}")
async def access_shared_file(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Access file via share link (no authentication required)"""
    try:
        result = await drive_service.get_shared_file(share_token, db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Share link not found")
            )
        
        # Return file for download
        from fastapi.responses import FileResponse
        
        return FileResponse(
            path=result["file_path"],
            filename=result["filename"],
            media_type=result["mime_type"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error accessing shared file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access shared file"
        )

@router.get("/storage-stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get storage statistics"""
    try:
        result = await drive_service.get_storage_stats(current_user.id, db)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get storage stats"
        )