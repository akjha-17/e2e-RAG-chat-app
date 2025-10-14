from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class AskRequest(BaseModel):
    query: str
    top_k: int = 4
    use_synthesis: Optional[bool] = True
    session_id: Optional[str] = None
    response_length: Optional[int] = 50  # Response length preference (10-100)

class SourceItem(BaseModel):
    file: str
    chunk_id: str
    score: float
    score_normalized: float
    preview: str
    page_number: Optional[int] = -1

class AskResponse(BaseModel):
    query: str
    language: str
    answer: str
    sources: List[SourceItem]
    session_id: Optional[str] = None

class UploadResponse(BaseModel):
    file: str
    chunks_added: int

class ReindexResponse(BaseModel):
    folder: str
    chunks_indexed: int

class DevTokenRequest(BaseModel):
    username: str

class FeedbackRequest(BaseModel):
    session_id: str
    query: str
    rating: int
    comment: str = ""
    message_id: Optional[int] = None

# User Authentication Models
class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    preferred_name: str
    role: str = "user"
    organization: str = ""

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserProfileUpdateRequest(BaseModel):
    email: Optional[str] = None
    preferred_name: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    preferred_name: str
    puid: str
    role: str
    organization: str
    is_admin: bool
    created_at: str
    last_login: Optional[str] = None

# Chat Session Models
class ChatSessionCreateRequest(BaseModel):
    title: str

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message_time: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    message_type: str  # 'user' or 'assistant'
    content: str
    sources: List[SourceItem] = []
    rating: Optional[int] = None
    feedback_comment: str = ""
    timestamp: str

class ChatSessionDetailResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]

class ChatSessionUpdateRequest(BaseModel):
    title: str

class MessageFeedbackRequest(BaseModel):
    message_id: int
    rating: int
    comment: str = ""
