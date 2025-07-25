from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FeedbackBase(BaseModel):
    comment: str
    ratings: Dict[str, int]

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    user_id: str
    user_name: Optional[str] = "Anonymous"
    deal_id: int
    class Config:
        from_attributes = True

class DealBase(BaseModel):
    file_name: str
    # S3 URL and analysis are now optional
    s3_url: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = None
    # --- NEW ---
    status: str

class Deal(DealBase):
    id: int
    user_id: str
    user_name: Optional[str] = "Anonymous"
    feedbacks: List[Feedback] = []
    class Config:
        from_attributes = True
