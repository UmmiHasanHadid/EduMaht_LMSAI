"""Authentication service - fixed to use a single session per call"""
from datetime import timedelta
from typing import Optional
from sqlalchemy import select
from app.database import async_session_maker
from app.models import User, UserRole
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.config import settings


class AuthService:
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == email, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            if not verify_password(password, user.hashed_password):
                return None
            return user

    @staticmethod
    async def create_user(
        email: str,
        username: str,
        full_name: str,
        password: str,
        role=UserRole.STUDENT,
    ) -> User:
        hashed_password = get_password_hash(password)
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(
                    (User.email == email) | (User.username == username)
                )
            )
            if result.scalar_one_or_none():
                raise ValueError("Email atau username sudah terdaftar")

            user = User(
                email=email,
                username=username,
                full_name=full_name,
                hashed_password=hashed_password,
                role=role if isinstance(role, UserRole) else UserRole(role),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_current_user(token: str) -> Optional[User]:
        payload = verify_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == int(user_id), User.is_active.is_(True))
            )
            return result.scalar_one_or_none()

    @staticmethod
    def create_tokens(user: User) -> dict:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": role_val},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[dict]:
        payload = verify_token(refresh_token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == int(user_id), User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return AuthService.create_tokens(user)
