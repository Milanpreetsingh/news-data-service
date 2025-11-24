from typing import Optional
from datetime import timedelta
import logging
from fastapi import HTTPException, status
from app.repositories.interfaces import IUserRepository
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_refresh_token
)
from app.models.schemas import UserSignup, UserLogin

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_repository: IUserRepository):
        self._user_repo = user_repository
    
    async def signup(self, user_data: UserSignup) -> dict:
        if await self._user_repo.exists_by_email_or_username(user_data.email, user_data.username):
            logger.warning(f"Signup attempt with existing email/username: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        hashed_password = get_password_hash(user_data.password)
        user = await self._user_repo.create(user_data.email, user_data.username, hashed_password)
        logger.info(f"New user created: {user['email']}")
        return user
    
    async def login(self, login_data: UserLogin) -> dict:
        user = await self._user_repo.find_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user['hashed_password']):
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user['is_active']:
            logger.warning(f"Login attempt for inactive user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        access_token = create_access_token(
            data={"sub": user['email'], "user_id": str(user['id'])}
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user['email'], "user_id": str(user['id'])}
        )
        
        logger.info(f"User logged in: {user['email']}")
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_refresh_token(refresh_token)
        
        if not payload:
            logger.warning("Invalid refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        email = payload.get("sub")
        
        if not user_id or not email:
            logger.warning("Invalid token payload in refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = await self._user_repo.find_by_id(user_id)
        
        if not user:
            logger.warning(f"User not found during token refresh: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user['is_active']:
            logger.warning(f"Token refresh attempt for inactive user: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        new_access_token = create_access_token(
            data={"sub": email, "user_id": str(user_id)}
        )
        
        return {"access_token": new_access_token, "token_type": "bearer"}
    
    async def get_current_user(self, user_id: str) -> Optional[dict]:
        return await self._user_repo.find_by_id(user_id)
