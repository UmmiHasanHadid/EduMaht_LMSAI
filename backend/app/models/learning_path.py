from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    recommended_courses = Column(JSON)  # List of recommended course IDs
    learning_style = Column(String(100))  # visual, auditory, kinesthetic, etc
    goals = Column(JSON)  # Student's learning goals
    skill_gaps = Column(JSON)  # Identified skill gaps
    ai_recommendations = Column(JSON)  # AI-generated recommendations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="learning_paths")
    
    def __repr__(self):
        return f"<LearningPath {self.title}>"
