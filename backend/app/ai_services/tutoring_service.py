"""
AI Tutoring Service
Provides AI-powered tutoring with strict guardrails to ensure learning is supportive, not answer-giving.
Uses Gemini AI with carefully crafted system prompts.
"""
from typing import Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.ai_services.answer_evaluator import AnswerEvaluator
from app.ai_services.tutor_config import (
    TUTORING_SYSTEM_PROMPT,
    HINT_GENERATION_PROMPT,
    SAFE_RESPONSE_TEMPLATES,
    TUTOR_PERSONALITY,
)
import random


class TutoringService:
    """Service for AI-powered tutoring with strict guardrails"""
    
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set to use TutoringService")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.google_api_key,
            temperature=0.7,  # Moderate creativity untuk respon yang natural
            max_output_tokens=500,  # Batasi panjang respon
        )
        self.evaluator = AnswerEvaluator()
    
    async def answer_student_question(
        self, 
        question: str,
        course_id: int,
        lesson_id: Optional[int] = None,
        context: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Answer student questions using AI with teaching guardrails.
        Never gives direct answers - only guides and hints.
        
        Returns:
        {
            "response": "AI response",
            "type": "guidance/hint/explanation",
            "is_directed": bool (whether it's guiding toward answer)
        }
        """
        
        if not question.strip():
            return {
                "response": "Bisa Anda jelaskan pertanyaannya dengan lebih detail? Saya siap membantu!",
                "type": "clarification_request",
                "is_directed": False,
            }
        
        # Ensure the prompt respects the system guidelines
        user_prompt = f"""Siswa bertanya: "{question}"

Topik: {topic or "Umum"}
Konteks: {context or "Tidak ada konteks tambahan"}
Kursus: {course_id}

INGAT: Anda hanya boleh MEMBIMBING, TIDAK memberikan JAWABAN LANGSUNG.
Gunakan pertanyaan penuntun dan konsep untuk memandu siswa berpikir sendiri.

Respon Anda harus:
1. Jelas dan mudah dipahami
2. Memotivasi siswa untuk berpikir
3. Tidak membosankan (max 3 kalimat)
4. Positif dan mendukung"""
        
        try:
            response = await self.llm.ainvoke(
                input=user_prompt,
                system=TUTORING_SYSTEM_PROMPT,
            )
            
            ai_response = response.content.strip()
            
            # Ensure response is not too long
            if len(ai_response) > TUTOR_PERSONALITY["max_response_length"]:
                ai_response = ai_response[:TUTOR_PERSONALITY["max_response_length"]] + "..."
            
            return {
                "response": ai_response,
                "type": "guidance",
                "is_directed": True,
            }
        
        except Exception as e:
            return {
                "response": f"Maaf, terjadi kesalahan dalam memproses pertanyaan Anda: {str(e)}",
                "type": "error",
                "is_directed": False,
            }
    
    async def evaluate_and_respond_to_answer(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        difficulty_level: str = "medium",
        question_type: str = "essay",
    ) -> Dict:
        """
        Evaluate student answer and provide encouraging feedback.
        
        WORKFLOW:
        1. Evaluate answer against correct answer
        2. Generate appropriate response based on correctness
        3. Provide guidance for improvement if needed
        
        Returns:
        {
            "is_correct": bool,
            "correctness_level": "correct/partial/incorrect",
            "evaluation": {...} (from evaluator),
            "feedback": "Tailored AI feedback",
            "next_step": "hint/detailed_guidance/celebration",
        }
        """
        
        # Step 1: Evaluate the answer
        evaluation = await self.evaluator.evaluate_answer(
            question=question,
            correct_answer=correct_answer,
            student_answer=student_answer,
            difficulty_level=difficulty_level,
            question_type=question_type,
        )
        
        # Step 2: Generate feedback based on correctness
        feedback = await self._generate_tailored_feedback(
            evaluation=evaluation,
            student_answer=student_answer,
            correct_answer=correct_answer,
            question=question,
        )
        
        # Step 3: Determine next step
        if evaluation["is_correct"]:
            next_step = "celebration"
        elif evaluation["correctness_level"] == "partial":
            next_step = "refinement_hint"
        else:
            next_step = "detailed_guidance"
        
        return {
            "is_correct": evaluation["is_correct"],
            "correctness_level": evaluation["correctness_level"],
            "confidence": evaluation["confidence"],
            "feedback": feedback,
            "next_step": next_step,
            "evaluation_details": {
                "positive_aspects": evaluation.get("positive_aspects", ""),
                "conceptual_error": evaluation.get("conceptual_error", ""),
                "key_points_missed": evaluation.get("key_points_missed", []),
            },
        }
    
    async def _generate_tailored_feedback(
        self,
        evaluation: Dict,
        student_answer: str,
        correct_answer: str,
        question: str,
    ) -> str:
        """Generate feedback based on evaluation result"""
        
        correctness = evaluation["correctness_level"]
        
        # Use safe templates atau generate custom
        if correctness == "correct":
            template = random.choice(SAFE_RESPONSE_TEMPLATES["correct_answer"])
            feedback = template.replace("[konsep]", "konsep ini")
            feedback = feedback.replace("[aspek]", "jawaban Anda")
        
        elif correctness == "partial":
            template = random.choice(SAFE_RESPONSE_TEMPLATES["partial_answer"])
            feedback = template.replace("[spesifik aspek]", evaluation.get("positive_aspects", "bagian ini"))
            feedback = feedback.replace("[detail spesifik]", "detail penting")
            feedback = feedback.replace("[aspek lain]", "bagian lainnya")
        
        else:  # incorrect
            template = random.choice(SAFE_RESPONSE_TEMPLATES["incorrect_answer"])
            feedback = template.replace("[aspek spesifik]", "bagian ini")
            feedback = feedback.replace("[konsep kunci]", "konsep utama")
            feedback = feedback.replace("[bagian spesifik]", "detail tertentu")
            feedback = feedback.replace("[topik]", "materi ini")
            feedback = feedback.replace("[pertanyaan panduan]", "mengapa jawaban itu masuk akal")
        
        return feedback
    
    async def provide_hint(
        self,
        question: str,
        current_attempt: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty_level: str = "medium",
    ) -> Dict[str, str]:
        """
        Provide a helpful hint without giving away the answer.
        
        Hint should:
        1. Ask guiding questions
        2. Break down into smaller steps
        3. Be encouraging and specific
        """
        
        user_prompt = f"""Berikan satu petunjuk yang SANGAT MEMBANTU namun TIDAK memberikan jawaban.

PERTANYAAN SISWA: {question}
USAHA SEBELUMNYA: {current_attempt or "Belum ada usaha"}
TOPIK: {topic or "Umum"}
TINGKAT KESULITAN: {difficulty_level}

PETUNJUK HARUS:
✓ Dalam bentuk pertanyaan yang membimbing
✓ Fokus pada SATU aspek kecil saja
✓ Mendorong siswa untuk berpikir lebih dalam
✓ Positif dan tidak membuat frustasi
✓ Maksimal 2 kalimat

HINDARI:
✗ Memberikan formula/rumus lengkap
✗ Memberikan jawaban parsial
✗ Pertanyaan yang ambigu
✗ Kata-kata negatif

Berikan HANYA petunjuk tanpa penjelasan tambahan."""
        
        try:
            response = await self.llm.ainvoke(
                input=user_prompt,
                system=TUTORING_SYSTEM_PROMPT,
            )
            
            hint = response.content.strip()
            
            if len(hint) > TUTOR_PERSONALITY["max_response_length"]:
                hint = hint[:TUTOR_PERSONALITY["max_response_length"]] + "..."
            
            return {
                "hint": hint,
                "type": "guiding_question",
                "is_safe": True,
            }
        
        except Exception as e:
            return {
                "hint": "Coba ingat kembali pelajaran sebelumnya dan lihat pertanyaan dari sudut pandang berbeda.",
                "type": "generic_hint",
                "is_safe": True,
            }
    
    async def generate_follow_up_questions(
        self,
        topic: str,
        level: str = "intermediate",
        num_questions: int = 3,
    ) -> List[str]:
        """Generate follow-up questions to deepen understanding"""
        
        prompt = f"""Buat {num_questions} pertanyaan lanjutan untuk memperdalam pemahaman topik berikut:

TOPIK: {topic}
LEVEL: {level}

KRITERIA PERTANYAAN:
- Membangun atas konsep dasar
- Mendorong pemikiran kritis
- Relevan dengan kehidupan nyata jika memungkinkan
- Tidak terlalu sulit, tapi menantang
- Jelas dan tidak ambigu

Berikan HANYA daftar pertanyaan, satu per baris, tanpa numbering."""
        
        try:
            response = await self.llm.ainvoke(
                input=prompt,
                system=TUTORING_SYSTEM_PROMPT,
            )
            
            questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
            return questions[:num_questions]
        
        except:
            return [
                f"Bagaimana konsep {topic} berkaitan dengan kehidupan sehari-hari Anda?",
                f"Apa perbedaan utama antara teori dan praktik dalam {topic}?",
                f"Bagaimana Anda bisa menerapkan pemahaman tentang {topic} untuk problem yang berbeda?",
            ]

