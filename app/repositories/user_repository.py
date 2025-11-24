from typing import Optional, Dict, Any
from uuid import UUID
import asyncpg
import logging
from fastapi import HTTPException, status
from app.core.interfaces import IDatabase
from app.repositories.interfaces import IUserRepository

logger = logging.getLogger(__name__)

class UserRepository(IUserRepository):
    def __init__(self, db: IDatabase):
        self._db = db
    
    async def create(self, email: str, username: str, hashed_password: str) -> Dict[str, Any]:
        try:
            user = await self._db.fetchrow(
                """
                INSERT INTO users (email, username, hashed_password)
                VALUES ($1, $2, $3)
                RETURNING id, email, username, is_active, created_at
                """,
                email, username, hashed_password
            )
            return dict(user)
        except asyncpg.UniqueViolationError:
            logger.warning(f"Duplicate email or username: {email}, {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            user = await self._db.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            return dict(user) if user else None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in find_by_email: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user"
            )
    
    async def find_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            user = await self._db.fetchrow(
                "SELECT id, email, username, is_active, created_at FROM users WHERE id = $1",
                user_id
            )
            return dict(user) if user else None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in find_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user"
            )
    
    async def exists_by_email_or_username(self, email: str, username: str) -> bool:
        try:
            result = await self._db.fetchrow(
                "SELECT id FROM users WHERE email = $1 OR username = $2",
                email, username
            )
            return result is not None
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in exists_by_email_or_username: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check user existence"
            )
