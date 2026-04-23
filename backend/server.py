"""
EduMaht LMS AI Backend - Entry point for supervisor (server:app on 0.0.0.0:8001)
"""
from dotenv import load_dotenv
load_dotenv()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import User, UserRole  # ensure model registration
from app.utils.auth import get_password_hash
from app.routes import (
    auth_router, users_router, courses_router, lessons_router,
    enrollments_router, assessments_router, ai_router, attendance_router,
    ai_tutor_router, quizzes_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("edumaht")


def _seed_demo_users():
    """Seed a demo teacher & student on first boot if absent."""
    from sqlalchemy.orm import Session
    with Session(engine) as s:
        existing = s.query(User).filter(User.email == "guru@edumaht.com").first()
        if not existing:
            s.add_all([
                User(
                    email="guru@edumaht.com",
                    username="guru",
                    full_name="Bu Guru Demo",
                    hashed_password=get_password_hash("Guru1234"),
                    role=UserRole.INSTRUCTOR,
                    is_active=True,
                ),
                User(
                    email="siswa@edumaht.com",
                    username="siswa",
                    full_name="Siswa Demo",
                    hashed_password=get_password_hash("Siswa1234"),
                    role=UserRole.STUDENT,
                    is_active=True,
                ),
                User(
                    email="admin@edumaht.com",
                    username="admin",
                    full_name="Admin Demo",
                    hashed_password=get_password_hash("Admin1234"),
                    role=UserRole.ADMIN,
                    is_active=True,
                ),
            ])
            s.commit()
            logger.info("Seeded demo users: guru@edumaht.com / siswa@edumaht.com / admin@edumaht.com")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EduMaht backend…")
    Base.metadata.create_all(bind=engine)
    _seed_demo_users()
    yield
    logger.info("Shutting down EduMaht backend.")


app = FastAPI(
    title="EduMaht LMS AI",
    description="AI-powered Learning Management System API (Gemini-powered AI Tutor)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
allowed = settings.allowed_origins.split(",") if settings.allowed_origins and settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(lessons_router)
app.include_router(enrollments_router)
app.include_router(assessments_router)
app.include_router(ai_router)
app.include_router(attendance_router)
app.include_router(ai_tutor_router)
app.include_router(quizzes_router)


@app.get("/api/")
async def root():
    return {
        "name": "EduMaht LMS AI",
        "version": "1.0.0",
        "environment": settings.environment,
        "ai_model": settings.gemini_model,
        "tutor_retention_days": settings.tutor_retention_days,
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "model": settings.gemini_model}
