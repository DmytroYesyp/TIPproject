# app/crud.py
from sqlalchemy.orm import Session
# Changed this line: Now importing the specific model classes directly
from .database import User, Room, Message
from . import schemas
from passlib.context import CryptContext # For password hashing

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Utility ---
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# --- User CRUD Operations ---

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first() # Changed from models.User

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first() # Changed from models.User

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first() # Changed from models.User

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all() # Changed from models.User

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User( # Changed from models.User
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,  # New users are active by default
        is_admin=False # New users are not admins by default
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_status(db: Session, user_id: int, is_active: bool):
    return db.query(User).filter(User.id == user_id).update({"is_active": is_active}) # Changed from models.User for update optimization
    # # Alternative for update (if you prefer refreshing the object):
    # db_user = db.query(User).filter(User.id == user_id).first()
    # if db_user:
    #     db_user.is_active = is_active
    #     db.commit()
    #     db.refresh(db_user)
    # return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first() # Changed from models.User
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

# --- Room CRUD Operations ---

def get_room(db: Session, room_id: int):
    return db.query(Room).filter(Room.id == room_id).first() # Changed from models.Room

def get_room_by_name(db: Session, room_name: str):
    return db.query(Room).filter(Room.name == room_name).first() # Changed from models.Room

def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Room).offset(skip).limit(limit).all() # Changed from models.Room

def create_room(db: Session, room: schemas.RoomCreate):
    db_room = Room(name=room.name) # Changed from models.Room
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int):
    db_room = db.query(Room).filter(Room.id == room_id).first() # Changed from models.Room
    if db_room:
        db.delete(db_room)
        db.commit()
        return True
    return False

# --- Message CRUD Operations ---

def get_messages_in_room(db: Session, room_id: int, skip: int = 0, limit: int = 50):
    # Order by timestamp descending to get the latest messages
    return db.query(Message)\
             .filter(Message.room_id == room_id)\
             .order_by(Message.timestamp.desc())\
             .offset(skip).limit(limit).all() # Changed from models.Message

def create_message(db: Session, message: schemas.MessageCreate, sender_id: int):
    # Note: sender_id is passed directly, reflecting the authenticated user
    db_message = Message( # Changed from models.Message
        text=message.text,
        room_id=message.room_id,
        sender_id=sender_id # Use the authenticated sender_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Admin specific: Get all messages
def get_all_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Message).offset(skip).limit(limit).all() # Changed from models.Message