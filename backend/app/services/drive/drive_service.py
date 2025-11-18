import os
import uuid
import hashlib
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import aiofiles
from fastapi import UploadFile, HTTPException, status

from app.models import get_db, User, DriveFile, DriveFolder, DriveShare
from app.utils import get_logger
from app.config import settings
from app.plans import PlanFeatures

logger = get_logger(__name__)

class DriveService:
    def __init__(self):
        self.base_path = Path("drive_storage")
        self.base_path.mkdir(exist_ok=True)
        
        # Create user directories
        self.user_storage = self.base_path / "users"
        self.user_storage.mkdir(exist_ok=True)
        
        # Chunk size for large file uploads (10MB)
        self.chunk_size = 10 * 1024 * 1024
    
    async def upload_file(
        self,
        user_id: int,
        file: UploadFile,
        folder_id: Optional[int] = None,
        db=None
    ) -> Dict[str, Any]:
        """Upload file to drive"""
        if db is None:
            db = next(get_db())
        
        # Get user and check storage quota
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check storage quota
        if not await self.check_storage_quota(user_id, file.size, db):
            raise ValueError("Storage quota exceeded")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create user directory if not exists
        user_dir = self.user_storage / str(user_id)
        user_dir.mkdir(exist_ok=True)
        
        file_path = user_dir / unique_filename
        
        # Calculate checksum
        checksum = await self.calculate_checksum(file)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create file record
        drive_file = DriveFile(
            user_id=user_id,
            folder_id=folder_id,
            name=unique_filename,
            original_name=file.filename,
            file_path=str(file_path),
            file_size=file.size,
            mime_type=file.content_type or "application/octet-stream",
            checksum=checksum,
            virus_scan_status="pending"
        )
        
        db.add(drive_file)
        db.commit()
        db.refresh(drive_file)
        
        # Update user storage usage
        await self.update_storage_usage(user_id, file.size, db)
        
        # Queue virus scan
        from app.tasks.drive_tasks import scan_file_task
        scan_file_task.delay(drive_file.id)
        
        logger.info(f"File uploaded: {file.filename} for user {user_id}")
        
        return {
            "success": True,
            "file_id": drive_file.id,
            "filename": file.filename,
            "file_size": file.size,
            "mime_type": file.content_type,
            "checksum": checksum,
            "virus_scan_status": "pending"
        }
    
    async def upload_file_chunked(
        self,
        user_id: int,
        chunk_data: bytes,
        chunk_number: int,
        total_chunks: int,
        original_filename: str,
        mime_type: str,
        folder_id: Optional[int] = None,
        upload_id: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        """Upload file in chunks"""
        if db is None:
            db = next(get_db())
        
        # Generate upload ID if not provided
        if not upload_id:
            upload_id = str(uuid.uuid4())
        
        # Create temporary directory for chunks
        temp_dir = self.base_path / "temp" / upload_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save chunk
        chunk_path = temp_dir / f"chunk_{chunk_number}"
        async with aiofiles.open(chunk_path, 'wb') as f:
            await f.write(chunk_data)
        
        # Check if all chunks are uploaded
        uploaded_chunks = len(list(temp_dir.glob("chunk_*")))
        
        if uploaded_chunks == total_chunks:
            # All chunks uploaded, combine them
            return await self.combine_chunks(
                user_id, temp_dir, original_filename, mime_type, folder_id, db
            )
        
        return {
            "success": True,
            "upload_id": upload_id,
            "chunk_number": chunk_number,
            "chunks_uploaded": uploaded_chunks,
            "total_chunks": total_chunks,
            "status": "uploading"
        }
    
    async def combine_chunks(
        self,
        user_id: int,
        temp_dir: Path,
        original_filename: str,
        mime_type: str,
        folder_id: Optional[int],
        db
    ) -> Dict[str, Any]:
        """Combine uploaded chunks into final file"""
        try:
            # Get user and check storage quota
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Calculate total file size
            total_size = 0
            chunk_files = sorted(temp_dir.glob("chunk_*"), key=lambda x: int(x.stem.split("_")[1]))
            
            for chunk_file in chunk_files:
                total_size += chunk_file.stat().st_size
            
            # Check storage quota
            if not await self.check_storage_quota(user_id, total_size, db):
                raise ValueError("Storage quota exceeded")
            
            # Generate unique filename
            file_extension = Path(original_filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create user directory if not exists
            user_dir = self.user_storage / str(user_id)
            user_dir.mkdir(exist_ok=True)
            
            final_path = user_dir / unique_filename
            
            # Combine chunks
            async with aiofiles.open(final_path, 'wb') as final_file:
                for chunk_file in chunk_files:
                    async with aiofiles.open(chunk_file, 'rb') as chunk:
                        await final_file.write(await chunk.read())
            
            # Calculate checksum
            checksum = await self.calculate_file_checksum(final_path)
            
            # Create file record
            drive_file = DriveFile(
                user_id=user_id,
                folder_id=folder_id,
                name=unique_filename,
                original_name=original_filename,
                file_path=str(final_path),
                file_size=total_size,
                mime_type=mime_type,
                checksum=checksum,
                virus_scan_status="pending"
            )
            
            db.add(drive_file)
            db.commit()
            db.refresh(drive_file)
            
            # Update user storage usage
            await self.update_storage_usage(user_id, total_size, db)
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            # Queue virus scan
            from app.tasks.drive_tasks import scan_file_task
            scan_file_task.delay(drive_file.id)
            
            logger.info(f"Chunked file upload completed: {original_filename} for user {user_id}")
            
            return {
                "success": True,
                "file_id": drive_file.id,
                "filename": original_filename,
                "file_size": total_size,
                "mime_type": mime_type,
                "checksum": checksum,
                "virus_scan_status": "pending"
            }
            
        except Exception as e:
            logger.error(f"Error combining chunks: {str(e)}")
            # Clean up temporary directory on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    async def download_file(self, file_id: int, user_id: int, db=None) -> Dict[str, Any]:
        """Download file from drive"""
        if db is None:
            db = next(get_db())
        
        file_record = db.query(DriveFile).filter(
            DriveFile.id == file_id,
            DriveFile.user_id == user_id,
            DriveFile.is_deleted == False
        ).first()
        
        if not file_record:
            raise ValueError("File not found")
        
        if not os.path.exists(file_record.file_path):
            raise ValueError("File not found on disk")
        
        return {
            "success": True,
            "file_path": file_record.file_path,
            "filename": file_record.original_name,
            "mime_type": file_record.mime_type,
            "file_size": file_record.file_size
        }
    
    async def delete_file(self, file_id: int, user_id: int, db=None) -> Dict[str, Any]:
        """Delete file from drive"""
        if db is None:
            db = next(get_db())
        
        file_record = db.query(DriveFile).filter(
            DriveFile.id == file_id,
            DriveFile.user_id == user_id,
            DriveFile.is_deleted == False
        ).first()
        
        if not file_record:
            raise ValueError("File not found")
        
        # Mark as deleted (soft delete)
        file_record.is_deleted = True
        db.commit()
        
        # Update storage usage
        await self.update_storage_usage(user_id, -file_record.file_size, db)
        
        # Delete actual file
        try:
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
        except Exception as e:
            logger.error(f"Error deleting file {file_record.file_path}: {str(e)}")
        
        logger.info(f"File deleted: {file_record.original_name} for user {user_id}")
        
        return {
            "success": True,
            "message": "File deleted successfully"
        }
    
    async def create_folder(
        self,
        user_id: int,
        name: str,
        parent_id: Optional[int] = None,
        db=None
    ) -> Dict[str, Any]:
        """Create folder"""
        if db is None:
            db = next(get_db())
        
        # Validate parent folder
        if parent_id:
            parent_folder = db.query(DriveFolder).filter(
                DriveFolder.id == parent_id,
                DriveFolder.user_id == user_id,
                DriveFolder.is_deleted == False
            ).first()
            
            if not parent_folder:
                raise ValueError("Parent folder not found")
        
        # Generate folder path
        if parent_id:
            parent_folder = db.query(DriveFolder).filter(DriveFolder.id == parent_id).first()
            parent_path = parent_folder.path or ""
            folder_path = f"{parent_path}/{name}" if parent_path else name
        else:
            folder_path = name
        
        # Create folder record
        folder = DriveFolder(
            user_id=user_id,
            parent_id=parent_id,
            name=name,
            path=folder_path
        )
        
        db.add(folder)
        db.commit()
        db.refresh(folder)
        
        logger.info(f"Folder created: {name} for user {user_id}")
        
        return {
            "success": True,
            "folder_id": folder.id,
            "name": name,
            "path": folder_path
        }
    
    async def list_files(
        self,
        user_id: int,
        folder_id: Optional[int] = None,
        db=None
    ) -> Dict[str, Any]:
        """List files and folders in a directory"""
        if db is None:
            db = next(get_db())
        
        # Get folders
        folders_query = db.query(DriveFolder).filter(
            DriveFolder.user_id == user_id,
            DriveFolder.is_deleted == False
        )
        
        if folder_id is not None:
            folders_query = folders_query.filter(DriveFolder.parent_id == folder_id)
        else:
            folders_query = folders_query.filter(DriveFolder.parent_id.is_(None))
        
        folders = folders_query.all()
        
        # Get files
        files_query = db.query(DriveFile).filter(
            DriveFile.user_id == user_id,
            DriveFile.is_deleted == False
        )
        
        if folder_id is not None:
            files_query = files_query.filter(DriveFile.folder_id == folder_id)
        else:
            files_query = files_query.filter(DriveFile.folder_id.is_(None))
        
        files = files_query.all()
        
        return {
            "success": True,
            "folders": [
                {
                    "id": folder.id,
                    "name": folder.name,
                    "path": folder.path,
                    "created_at": folder.created_at.isoformat()
                }
                for folder in folders
            ],
            "files": [
                {
                    "id": file.id,
                    "name": file.original_name,
                    "file_size": file.file_size,
                    "mime_type": file.mime_type,
                    "virus_scan_status": file.virus_scan_status,
                    "created_at": file.created_at.isoformat()
                }
                for file in files
            ]
        }
    
    async def create_share_link(
        self,
        file_id: int,
        user_id: int,
        share_type: str = "view",
        expires_hours: Optional[int] = None,
        db=None
    ) -> Dict[str, Any]:
        """Create share link for file"""
        if db is None:
            db = next(get_db())
        
        # Check file ownership
        file_record = db.query(DriveFile).filter(
            DriveFile.id == file_id,
            DriveFile.user_id == user_id,
            DriveFile.is_deleted == False
        ).first()
        
        if not file_record:
            raise ValueError("File not found")
        
        # Generate share token
        share_token = hashlib.sha256(f"{file_id}{user_id}{datetime.utcnow()}".encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Create share record
        share = DriveShare(
            file_id=file_id,
            share_token=share_token,
            share_type=share_type,
            expires_at=expires_at
        )
        
        db.add(share)
        db.commit()
        db.refresh(share)
        
        logger.info(f"Share link created for file {file_id} by user {user_id}")
        
        return {
            "success": True,
            "share_id": share.id,
            "share_token": share_token,
            "share_url": f"/drive/share/{share_token}",
            "share_type": share_type,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    
    async def get_shared_file(self, share_token: str, db=None) -> Dict[str, Any]:
        """Get file via share link"""
        if db is None:
            db = next(get_db())
        
        share = db.query(DriveShare).filter(
            DriveShare.share_token == share_token,
            DriveShare.is_active == True
        ).first()
        
        if not share:
            raise ValueError("Share link not found")
        
        # Check expiration
        if share.expires_at and share.expires_at < datetime.utcnow():
            raise ValueError("Share link expired")
        
        # Update access time
        share.accessed_at = datetime.utcnow()
        db.commit()
        
        file_record = share.file
        
        if not os.path.exists(file_record.file_path):
            raise ValueError("File not found on disk")
        
        return {
            "success": True,
            "file_path": file_record.file_path,
            "filename": file_record.original_name,
            "mime_type": file_record.mime_type,
            "file_size": file_record.file_size,
            "share_type": share.share_type
        }
    
    async def check_storage_quota(self, user_id: int, file_size: int, db) -> bool:
        """Check if user has enough storage quota"""
        # Get user's current usage
        usage = db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == datetime.utcnow().strftime("%Y-%m")
        ).first()
        
        current_usage = usage.storage_used_bytes if usage else 0
        
        # Get user's plan
        user = db.query(User).filter(User.id == user_id).first()
        plan_features = PlanFeatures.get_plan_features(user.plan.value)
        
        storage_limit_gb = plan_features["storage_limit_gb"]
        
        if storage_limit_gb == "unlimited":
            return True
        
        storage_limit_bytes = storage_limit_gb * 1024 * 1024 * 1024
        return (current_usage + file_size) <= storage_limit_bytes
    
    async def update_storage_usage(self, user_id: int, size_change: int, db):
        """Update user's storage usage"""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        usage = db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == current_month
        ).first()
        
        if not usage:
            usage = UserUsage(
                user_id=user_id,
                month=current_month,
                storage_used_bytes=0
            )
            db.add(usage)
        
        usage.storage_used_bytes += size_change
        db.commit()
    
    async def calculate_checksum(self, file: UploadFile) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        # Reset file pointer
        await file.seek(0)
        
        # Read file in chunks to handle large files
        while chunk := await file.read(8192):
            sha256_hash.update(chunk)
        
        # Reset file pointer again
        await file.seek(0)
        
        return sha256_hash.hexdigest()
    
    async def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file from path"""
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def get_storage_stats(self, user_id: int, db=None) -> Dict[str, Any]:
        """Get storage statistics for user"""
        if db is None:
            db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get current usage
        usage = db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == datetime.utcnow().strftime("%Y-%m")
        ).first()
        
        current_usage = usage.storage_used_bytes if usage else 0
        
        # Get plan limits
        plan_features = PlanFeatures.get_plan_features(user.plan.value)
        storage_limit_gb = plan_features["storage_limit_gb"]
        
        if storage_limit_gb == "unlimited":
            storage_limit_bytes = float('inf')
        else:
            storage_limit_bytes = storage_limit_gb * 1024 * 1024 * 1024
        
        return {
            "user_id": user_id,
            "plan": user.plan.value,
            "storage_used_bytes": current_usage,
            "storage_limit_bytes": storage_limit_bytes,
            "storage_used_gb": current_usage / (1024 ** 3),
            "storage_limit_gb": storage_limit_gb,
            "usage_percentage": (current_usage / storage_limit_bytes * 100) if storage_limit_bytes != float('inf') else 0
        }

# Global drive service instance
drive_service = DriveService()