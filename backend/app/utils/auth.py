from datetime import datetime, timedelta
from typing import Optional
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthManager:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_email_verification_token(email: str) -> str:
        """Create email verification token"""
        from app.utils import get_logger
        logger = get_logger(__name__)
        
        expire = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        to_encode = {"sub": email, "exp": expire, "type": "email_verification", "jti": str(uuid.uuid4())}
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        logger.info(f"Created email verification token for {email}")
        return encoded_jwt
    
    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """Create password reset token"""
        from app.utils import get_logger
        logger = get_logger(__name__)
        
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        to_encode = {"sub": email, "exp": expire, "type": "password_reset", "jti": str(uuid.uuid4())}
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        logger.info(f"Created password reset token for {email}")
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """Verify JWT token and return payload"""
        from app.utils import get_logger
        logger = get_logger(__name__)
        
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            email: str = payload.get("sub")
            if email is None:
                logger.warning("Token missing subject")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            
            logger.debug(f"Token verified successfully for {email}")
            return payload
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def create_tokens(email: str) -> dict:
        """Create both access and refresh tokens"""
        from app.utils import get_logger
        logger = get_logger(__name__)
        
        access_token = AuthManager.create_access_token(data={"sub": email})
        refresh_token = AuthManager.create_refresh_token(data={"sub": email})
        
        logger.info(f"Created tokens for {email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }