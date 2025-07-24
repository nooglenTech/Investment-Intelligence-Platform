from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, engine

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # To associate a deal with a user
    file_name = Column(String, index=True)
    s3_url = Column(String)
    status = Column(String, default="Feedback Required")
    analysis_data = Column(JSON)
    feedbacks = relationship("Feedback", back_populates="deal", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # To associate feedback with a user
    comment = Column(String)
    ratings = Column(JSON)
    deal_id = Column(Integer, ForeignKey("deals.id"))
    deal = relationship("Deal", back_populates="feedbacks")

# The line `Base.metadata.create_all(bind=engine)` has been removed from this file.
# It should only be run from a dedicated script.
