"""
AI Services Routes
Handles AI tutoring, content generation, learning paths, and assessment evaluation.
All AI responses are strictly guided to ensure learning is supportive and not answer-giving.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/ai", tags=["ai"])

_tutoring_service = None

def get_tutoring_service():
    global _tutoring_service
    if _tutoring_service is None:
        try:
            from app.ai_services.tutoring_service import TutoringService
        except ModuleNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI tutoring service unavailable: {exc}"
            )
        _tutoring_service = TutoringService()
    return _tutoring_service


# ==================== REQUEST MODELS ====================

class TutoringQuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500, description="Student question")
    course_id: int
    lesson_id: Optional[int] = None
    context: Optional[str] = Field(None, max_length=1000)
    topic: Optional[str] = None


class AnswerEvaluationRequest(BaseModel):
    question: str = Field(..., min_length=5)
    student_answer: str = Field(..., min_length=1, max_length=2000)
    correct_answer: str = Field(..., min_length=1, max_length=2000)
    difficulty_level: str = Field("medium", pattern="^(easy|medium|hard)$")
    question_type: str = Field("essay", pattern="^(essay|multiple_choice|short_answer)$")


class HintRequest(BaseModel):
    question: str = Field(..., min_length=5)
    current_attempt: Optional[str] = Field(None, max_length=2000)
    topic: Optional[str] = None
    difficulty_level: str = Field("medium", pattern="^(easy|medium|hard)$")


class LearningPathRequest(BaseModel):
    skill_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    learning_style: str = Field("visual", pattern="^(visual|auditory|kinesthetic|reading)$")
    goals: List[str] = Field(..., min_items=1, max_items=5)


# ==================== TUTORING ENDPOINTS ====================

@router.post("/tutoring/ask")
async def ask_tutor(
    data: TutoringQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ask AI tutor a question about course material.
    
    The tutor will guide and direct thinking, NOT give direct answers.
    
    Returns: Guided response with hints or explanation.
    """
    try:
        response = await get_tutoring_service().answer_student_question(
            question=data.question,
            course_id=data.course_id,
            lesson_id=data.lesson_id,
            context=data.context,
            topic=data.topic,
        )
        
        return {
            "success": True,
            "data": response,
            "user_id": current_user.id,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process tutoring question: {str(e)}"
        )


@router.post("/tutoring/evaluate")
async def evaluate_answer(
    data: AnswerEvaluationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate student's answer and provide encouraging feedback.
    
    This endpoint:
    1. Analyzes the student answer against the correct answer
    2. Determines if answer is correct/partial/incorrect
    3. Generates supportive feedback
    4. Suggests next learning step
    
    Returns: Evaluation result with feedback and guidance.
    """
    try:
        result = await get_tutoring_service().evaluate_and_respond_to_answer(
            question=data.question,
            student_answer=data.student_answer,
            correct_answer=data.correct_answer,
            difficulty_level=data.difficulty_level,
            question_type=data.question_type,
        )
        
        return {
            "success": True,
            "data": result,
            "user_id": current_user.id,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate answer: {str(e)}"
        )


@router.post("/tutoring/hint")
async def get_hint(
    data: HintRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get a hint for a question without revealing the answer.
    
    Hints are designed to:
    - Guide thinking in the right direction
    - Ask leading questions
    - Help break down complex problems
    - Encourage critical thinking
    
    Returns: Guiding hint that promotes learning, not answers.
    """
    try:
        result = await get_tutoring_service().provide_hint(
            question=data.question,
            current_attempt=data.current_attempt,
            topic=data.topic,
            difficulty_level=data.difficulty_level,
        )
        
        return {
            "success": True,
            "data": result,
            "user_id": current_user.id,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hint: {str(e)}"
        )


# ==================== LEARNING PATH ENDPOINTS ====================

@router.post("/learning-path/generate")
async def generate_learning_path(
    data: LearningPathRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate personalized learning path based on student profile"""
    try:
        # TODO: Implement learning path generation
        return {
            "success": True,
            "message": "Learning path generation coming soon",
            "student_id": current_user.id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning path: {str(e)}"
        )


@router.get("/learning-path/my-path")
async def get_my_learning_path(
    current_user: User = Depends(get_current_user)
):
    """Get current user's personalized learning path"""
    try:
        # TODO: Implement get learning path
        return {
            "success": True,
            "message": "Learning path retrieval coming soon",
            "student_id": current_user.id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve learning path: {str(e)}"
        )


# ==================== CONTENT GENERATION ENDPOINTS ====================

@router.post("/content/generate")
async def generate_content(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Generate educational content using AI"""
    try:
        # TODO: Implement content generation
        return {
            "success": True,
            "message": "Content generation coming soon",
            "user_id": current_user.id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/performance")
async def get_performance_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered performance analytics for current student"""
    try:
        # TODO: Implement analytics
        return {
            "success": True,
            "message": "Analytics coming soon",
            "student_id": current_user.id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


# ==================== ASSESSMENT EVALUATION ====================

@router.post("/assessment/evaluate")
async def evaluate_response(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Get AI evaluation of an answer in assessment"""
    try:
        # TODO: Implement assessment evaluation
        return {
            "success": True,
            "message": "Assessment evaluation coming soon",
            "user_id": current_user.id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate response: {str(e)}"
        )
