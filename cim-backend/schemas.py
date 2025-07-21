from pydantic import BaseModel
from typing import List, Dict, Any

class FeedbackBase(BaseModel):
    comment: str
    ratings: Dict[str, int]

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    deal_id: int
    class Config:
        orm_mode = True

class DealBase(BaseModel):
    file_name: str
    s3_url: str
    status: str
    analysis_data: Dict[str, Any]

class Deal(DealBase):
    id: int
    feedbacks: List[Feedback] = []
    class Config:
        orm_mode = True