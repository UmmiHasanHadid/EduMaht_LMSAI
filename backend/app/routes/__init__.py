from .auth import router as auth_router
from .users import router as users_router
from .courses import router as courses_router
from .lessons import router as lessons_router
from .enrollments import router as enrollments_router
from .assessments import router as assessments_router
from .ai import router as ai_router
from .attendance import router as attendance_router
from .ai_tutor import router as ai_tutor_router
from .quizzes import router as quizzes_router

__all__ = [
    "auth_router",
    "users_router",
    "courses_router",
    "lessons_router",
    "enrollments_router",
    "assessments_router",
    "ai_router",
    "attendance_router",
    "ai_tutor_router",
    "quizzes_router",
]
