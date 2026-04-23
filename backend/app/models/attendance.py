from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="present")  # present, absent, late
    notes = Column(String(500), nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # instructor who marked
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")
    lesson = relationship("Lesson")
    marker = relationship("User", foreign_keys=[marked_by])


class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    grade_letter = Column(String(5), nullable=True)  # A, B, C, D, F
    feedback = Column(String(1000), nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    assessment = relationship("Assessment")
    grader = relationship("User", foreign_keys=[graded_by])