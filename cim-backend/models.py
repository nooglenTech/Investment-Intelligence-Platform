from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, engine # <-- CORRECTED IMPORT

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    s3_url = Column(String) # To store the link to the PDF in S3
    status = Column(String, default="Feedback Required")
    analysis_data = Column(JSON)
    
    feedbacks = relationship("Feedback", back_populates="deal")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    comment = Column(String)
    ratings = Column(JSON) # Store ratings like {"risk": 4, "return": 5}
    deal_id = Column(Integer, ForeignKey("deals.id"))
    
    deal = relationship("Deal", back_populates="feedbacks")

# Create all tables in the database
Base.metadata.create_all(bind=engine)