# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# IMPORTANT: Replace with your actual PostgreSQL connection string
# Example: "postgresql://user:password@localhost:5432/chat_db"
DATABASE_URL = "postgresql://postgres:root@localhost:5432/tip_project"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define your models here (copied from previous step)
# Association table for many-to-many relationship between users and rooms
room_users = Table(
    "room_users",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("room_id", Integer, ForeignKey("rooms.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    rooms = relationship("Room", secondary=room_users, back_populates="users")
    messages = relationship("Message", back_populates="sender")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # Ensure room names are unique
    users = relationship("User", secondary=room_users, back_populates="rooms")
    messages = relationship("Message", back_populates="room")

    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}')>"

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    room_id = Column(Integer, ForeignKey("rooms.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    room = relationship("Room", back_populates="messages")
    sender = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, text='{self.text[:20]}...', room_id={self.room_id}, sender_id={self.sender_id})>"

def create_db_and_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")

# This part will only run when the script is executed directly
if __name__ == "__main__":
    create_db_and_tables()