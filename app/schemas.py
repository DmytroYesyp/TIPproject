# app/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    # We can add `rooms` here later if we want to include user's rooms in the response

    class Config:
        from_attributes = True # Was orm_mode = True in older Pydantic versions

# --- Room Schemas ---
class RoomBase(BaseModel):
    name: str

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: int
    # users: List[UserResponse] # Optional: if you want to embed users in room response

    class Config:
        from_attributes = True

# --- Message Schemas ---
class MessageBase(BaseModel):
    text: str

class MessageCreate(MessageBase):
    room_id: int
    sender_id: int # In a real app, sender_id would come from auth, not user input

class MessageResponse(MessageBase):
    id: int
    timestamp: datetime
    room_id: int
    sender_id: int
    sender_username: str # To display sender's username directly

    class Config:
        from_attributes = True
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None # Used by the JWT parsing