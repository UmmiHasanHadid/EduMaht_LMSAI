"""Authentication Routes"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from app.services.auth_service import AuthService
from app.models import UserRole

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.STUDENT

    @field_validator('password')
    @classmethod
    def password_must_be_valid(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password minimal 6 karakter')
        if len(v) > 72:
            raise ValueError('Password maksimal 72 karakter')
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def _user_public(user) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
    }


@router.post("/register")
async def register(data: RegisterRequest):
    try:
        user = await AuthService.create_user(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            password=data.password,
            role=data.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    tokens = AuthService.create_tokens(user)
    return {
        "message": "User registered successfully",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
        "user": _user_public(user),
    }


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    user = await AuthService.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = AuthService.create_tokens(user)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=_user_public(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    tokens = await AuthService.refresh_access_token(data.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user = await AuthService.get_current_user(tokens["access_token"])
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=_user_public(user),
    )
