"""
Answer Evaluator for Student Responses
Evaluates student answers against correct answers using semantic similarity and AI
"""
from typing import Dict, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
import json
import re


class AnswerEvaluator:
    """Evaluates student answers for correctness and provides feedback"""
    
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set to use AnswerEvaluator")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.google_api_key,
            temperature=0.3,  # Lower temperature untuk evaluasi yang konsisten
        )
    
    async def evaluate_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str,
        difficulty_level: str = "medium",
        question_type: str = "essay"  # essay, multiple_choice, short_answer
    ) -> Dict:
        """
        Evaluate a student's answer against the correct answer.
        
        Returns a dict with:
        - is_correct: bool (100% match)
        - confidence: float (0.0-1.0)
        - correctness_level: str (correct/partial/incorrect)
        - feedback: str (AI-generated feedback)
        - key_points_missed: list[str] (if partial/incorrect)
        """
        
        if not student_answer.strip():
            return {
                "is_correct": False,
                "confidence": 1.0,
                "correctness_level": "empty",
                "feedback": "Silakan masukkan jawaban Anda untuk memulai.",
                "key_points_missed": ["Belum ada penyelesaian"]
            }
        
        prompt = f"""Anda adalah seorang penilai pendidikan yang ketat namun adil.

PERTANYAAN: {question}
JAWABAN YANG BENAR: {correct_answer}
JAWABAN SISWA: {student_answer}
TINGKAT KESULITAN: {difficulty_level}
JENIS SOAL: {question_type}

Evaluasi jawaban siswa dengan cermat. Tentukan:

1. TINGKAT KEBENARAN:
   - "correct" jika jawaban 90%+ sesuai jawaban yang benar (poin utama semua ada)
   - "partial" jika jawaban memiliki konsep benar tapi ada bagian yang salah/kurang (50-89%)
   - "incorrect" jika jawaban kurang dari 50% benar atau konsepnya salah

2. TINGKAT KEYAKINAN (0.0-1.0): Seberapa yakin Anda dengan penilaian ini

3. POIN POSITIF: Apa yang benar atau baik dari jawaban siswa

4. KESALAHAN KONSEP: Jika ada, apa kesalahan utamanya

5. POIN KUNCI YANG HILANG: Daftar poin penting yang tidak disebutkan siswa

Berikan jawaban dalam format JSON VALID tanpa markdown:
{
    "correctness_level": "correct/partial/incorrect",
    "confidence": 0.85,
    "positive_aspects": "siswa memahami konsep X dengan baik",
    "conceptual_error": "kesalahan: siswa tidak mempertimbangkan Y",
    "key_points_missed": ["poin 1", "poin 2"],
    "reasoning": "penjelasan singkat mengapa penilaian ini"
}"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            response_text = response.content
            
            # Extract JSON dari response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback jika parsing gagal
                result = {
                    "correctness_level": "incomplete",
                    "confidence": 0.5,
                    "positive_aspects": "",
                    "conceptual_error": "",
                    "key_points_missed": [],
                    "reasoning": "Tidak bisa mengevaluasi"
                }
        except Exception as e:
            result = {
                "correctness_level": "error",
                "confidence": 0.0,
                "positive_aspects": "",
                "conceptual_error": str(e),
                "key_points_missed": [],
                "reasoning": "Error dalam evaluasi"
            }
        
        # Transform hasil ke format yang diinginkan
        return {
            "is_correct": result.get("correctness_level") == "correct",
            "confidence": result.get("confidence", 0.5),
            "correctness_level": result.get("correctness_level", "incomplete"),
            "positive_aspects": result.get("positive_aspects", ""),
            "conceptual_error": result.get("conceptual_error", ""),
            "key_points_missed": result.get("key_points_missed", []),
            "reasoning": result.get("reasoning", ""),
        }
    
    async def semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity between two texts (0.0-1.0).
        Better for multiple choice or factual answers.
        """
        prompt = f"""Bandingkan kesamaan semantik dua teks ini pada skala 0.0 sampai 1.0:

TEKS 1: {text1}
TEKS 2: {text2}

Berikan HANYA angka desimal (contoh: 0.85) tanpa penjelasan."""
        
        try:
            response = await self.llm.ainvoke(prompt)
            similarity = float(response.content.strip())
            return max(0.0, min(1.0, similarity))  # Clamp ke 0.0-1.0
        except:
            return 0.5  # Default jika error
    
    def determine_feedback_type(
        self,
        correctness_level: str,
        is_hint_requested: bool = False
    ) -> str:
        """Tentukan tipe feedback yang sesuai"""
        if is_hint_requested:
            return "hint_request"
        elif correctness_level == "correct":
            return "correct"
        elif correctness_level == "partial":
            return "partial"
        else:
            return "incorrect"
