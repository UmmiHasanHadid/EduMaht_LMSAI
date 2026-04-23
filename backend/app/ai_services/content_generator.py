"""
AI Content Generation Service
Generates educational content using AI
"""
from typing import Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from app.config import settings


class ContentGenerator:
    """Service for AI-generated educational content"""
    
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set in the environment to use Gemini AI services")

        # Initialize Gemini AI
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        
    async def generate_lesson_content(
        self,
        topic: str,
        level: str = "intermediate",
        format: str = "markdown"
    ) -> str:
        """Generate lesson content for a given topic"""
        prompt = PromptTemplate(
            input_variables=["topic", "level", "format"],
            template="""
            Generate educational content for the topic: {topic}
            Level: {level}
            Format: {format}
            
            Please create comprehensive lesson content including:
            1. Introduction
            2. Key concepts
            3. Examples
            4. Summary
            
            Make it engaging and educational.
            """
        )
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "topic": topic,
            "level": level,
            "format": format
        })
        
        return response.content
    
    async def generate_quiz_questions(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """Generate quiz questions for a topic"""
        prompt = PromptTemplate(
            input_variables=["topic", "num_questions", "difficulty"],
            template="""
            Generate {num_questions} quiz questions about {topic}.
            Difficulty level: {difficulty}
            
            Format each question as:
            Question: [question text]
            Options: A) [option1] B) [option2] C) [option3] D) [option4]
            Correct Answer: [letter]
            Explanation: [brief explanation]
            
            Return as a list of questions.
            """
        )
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "topic": topic,
            "num_questions": num_questions,
            "difficulty": difficulty
        })
        
        # Parse the response (this would need proper parsing logic)
        return [{"question": "Parsed question", "options": [], "answer": "", "explanation": ""}]
    
    async def generate_examples(
        self,
        concept: str,
        num_examples: int = 3,
        context: Optional[str] = None
    ) -> List[str]:
        """Generate examples for a concept"""
        prompt = PromptTemplate(
            input_variables=["concept", "num_examples", "context"],
            template="""
            Generate {num_examples} practical examples for the concept: {concept}
            {context}
            
            Make examples clear and relevant.
            """
        )
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "concept": concept,
            "num_examples": num_examples,
            "context": f"Context: {context}" if context else ""
        })
        
        return response.content.split("\n")[:num_examples]
