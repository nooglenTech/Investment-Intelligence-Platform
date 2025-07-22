from pydantic import BaseModel
from typing import List, Dict, Any

class FeedbackBase(BaseModel):
    comment: str
    ratings: Dict[str, int]

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    user_id: str # <-- ADD THIS LINE
    deal_id: int
    class Config:
        from_attributes = True

class DealBase(BaseModel):
    file_name: str
    s3_url: str
    status: str
    analysis_data: Dict[str, Any]

class Deal(DealBase):
    id: int
    user_id: str # <-- ADD THIS LINE
    feedbacks: List[Feedback] = []
    class Config:
        from_attributes = True
