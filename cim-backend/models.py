from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    user_name = Column(String, default="Anonymous") 
    file_name = Column(String, index=True)
    s3_url = Column(String, nullable=True) # S3 URL can be null initially
    # --- NEW: Status to track analysis progress ---
    status = Column(String, default="Pending") # e.g., "Pending", "Analyzing", "Complete", "Failed"
    analysis_data = Column(JSON, nullable=True) # Analysis can be null initially
    feedbacks = relationship("Feedback", back_populates="deal", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    user_name = Column(String, default="Anonymous")
    comment = Column(String)
    ratings = Column(JSON)
    deal_id = Column(Integer, ForeignKey("deals.id"))
    deal = relationship("Deal", back_populates="feedbacks")
