"""
Database Schemas for LDI/SD Prototype

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Participant(BaseModel):
    name: str = Field(..., description="Full name of participant")
    email: str = Field(..., description="Unique email of participant")
    cohort: Optional[str] = Field(None, description="Cohort or batch identifier")
    role: Optional[str] = Field(None, description="Role, e.g., participant/mentor/admin")

class SessionTopic(BaseModel):
    title: str
    date: datetime
    description: Optional[str] = None

class PictureCard(BaseModel):
    user_id: str = Field(..., description="Participant identifier (email or id)")
    topic: str = Field(..., description="Session topic title or id")
    image_url: str = Field(..., description="Public URL to the uploaded image")
    caption: Optional[str] = None
    session_date: Optional[datetime] = None

class VoiceNote(BaseModel):
    user_id: str
    topic: str
    audio_url: str
    transcript: Optional[str] = None
    duration_sec: Optional[int] = None
    session_date: Optional[datetime] = None

class Thread(BaseModel):
    user_id: str
    topic: str
    content: str
    session_date: Optional[datetime] = None
    likes: int = 0

class Attendance(BaseModel):
    user_id: str
    topic: str
    session_date: datetime

class Pitch(BaseModel):
    user_id: str
    topic: str
    session_date: datetime
    selected_for_sd: bool = False

class Selection(BaseModel):
    user_id: str
    topic: str
    session_date: datetime
    status: str = Field("selected", description="selected/rejected/waitlist")
