# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base, User, Room, Message # Import your models and session
from fastapi.middleware.cors import CORSMiddleware

from .websocket_manager import manager # Import your ConnectionManager instance
import json # For sending JSON over WebSocket

from datetime import datetime, timedelta
from typing import Optional, List # Added List for admin endpoint response

from jose import JWTError, jwt # For JWT handling

# Import your database and crud operations
from . import crud, schemas # Import crud operations and pydantic schemas

# --- Configuration ---
# IMPORTANT: Use a strong, truly random secret key in a production environment
# Get it from environment variables or a configuration file.
SECRET_KEY = "your-super-secret-jwt-key" # CHANGE THIS IN PRODUCTION!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # How long an access token is valid
REFRESH_TOKEN_EXPIRE_DAYS = 7 # How long a refresh token is valid (for remembering login)

# OAuth2PasswordBearer will be used to extract the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# --- FastAPI Application Setup ---
app = FastAPI(
    title="FastAPI Chat App",
    description="A real-time chat application with user management and chat rooms.",
    version="0.1.0",
)

# --- CORS Configuration ---
# Define allowed origins. For development, you can use ["*"] to allow all origins,
# but for production, list specific origins where your frontend will be hosted.
origins = [
    "http://localhost",
    "http://localhost:8000", # Your FastAPI app
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    # If you open index.html directly from file system:
    "file://", # This is for local file system access, use with caution
    "null" # Sometimes browsers use 'null' origin for file:// or sandboxed iframes
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins during development. CHANGE THIS FOR PRODUCTION!
                          # In production, use `origins` list: allow_origins=origins
    allow_credentials=True, # Allow cookies to be sent with requests
    allow_methods=["*"], # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- JWT Token Creation Functions ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Authentication Dependency ---
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username) # Assuming TokenData schema exists for username
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an administrator")
    return current_user


# --- API Routes ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Chat App!"}

# User Registration
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_username = crud.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    return crud.create_user(db=db, user=user)

# User Login (OAuth2PasswordRequestForm is used for standard username/password login)
@app.post("/login", response_model=schemas.Token) # Define Token schema below
async def login_for_access_token(
    response: Response, # To set HTTP-only cookie
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )

    # Set tokens as HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=access_token_expires.total_seconds(),
        expires=access_token_expires.total_seconds(),
        secure=True, # Use True in production with HTTPS
        samesite="lax", # Strict, Lax, None
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token, # No "Bearer" for refresh token unless you want it
        httponly=True,
        max_age=refresh_token_expires.total_seconds(),
        expires=refresh_token_expires.total_seconds(),
        secure=True, # Use True in production with HTTPS
        samesite="lax",
        path="/refresh_token" # Path for refresh token endpoint
    )

    # Return access token in response body (optional, but common for client-side storage)
    return {"access_token": access_token, "token_type": "bearer"}


# --- User Logout ---
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}

# --- Example Protected Route (for testing) ---
@app.get("/users/me/", response_model=schemas.UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)): # Change models.User to User
    return current_user

# --- Admin Protected Route Example ---
@app.get("/admin/users/", response_model=List[schemas.UserResponse])
async def read_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user) # Change models.User to User
):
    users = crud.get_users(db)
    return users

# --- Room API Endpoints ---

@app.post("/rooms/", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_new_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Only active users can create rooms
):
    db_room = crud.get_room_by_name(db, room_name=room.name)
    if db_room:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room with this name already exists")
    
    return crud.create_room(db=db, room=room)

@app.get("/rooms/", response_model=List[schemas.RoomResponse])
async def list_all_rooms(
    db: Session = Depends(get_db),
    # You might choose to make listing rooms accessible to anyone or only authenticated users
    # current_user: User = Depends(get_current_active_user) # Uncomment if rooms list requires login
):
    rooms = crud.get_rooms(db)
    return rooms

@app.get("/rooms/{room_id}", response_model=schemas.RoomResponse)
async def get_room_details(
    room_id: int,
    db: Session = Depends(get_db),
    # Optional: require login to view specific room details
    # current_user: User = Depends(get_current_active_user)
):
    db_room = crud.get_room(db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return db_room


@app.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_room(
    room_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user) # Only administrators can delete rooms
):
    success = crud.delete_room(db, room_id=room_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # No content on successful deletion


# --- WebSocket Endpoint for Chat ---

@app.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    db: Session = Depends(get_db),
    # Optional: Authenticate WebSocket connection using a query parameter token
    # In a real app, you'd typically extract a token from a cookie or header in `on_connect`
    token: Optional[str] = None # Expect token as a query parameter for simplicity here: /ws/chat/{room_id}?token=<YOUR_JWT>
):
    current_user = None
    if token:
        try:
            # Re-use get_current_user logic for WebSocket authentication
            # Note: For WebSockets, we can't use Depends(oauth2_scheme) directly in path,
            # so we manually decode/verify the token.
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise JWTError
            current_user = crud.get_user_by_username(db, username=username)
            if current_user is None or not current_user.is_active:
                raise JWTError
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            return
    
    if not current_user: # If no token or invalid token, deny connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return

    # Check if room exists
    db_room = crud.get_room(db, room_id=room_id)
    if not db_room:
        await websocket.close(code=status.WS_1007_INVALID_PAYLOAD_DATA, reason="Room not found")
        return

    # User successfully authenticated and room exists, connect them
    user_username = current_user.username
    await manager.connect(room_id, websocket, user_username)
    
    # Send last 50 messages upon connection
    messages = crud.get_messages_in_room(db, room_id=room_id, limit=50)
    # Messages are fetched in descending order, send them in ascending order (oldest first)
    for msg in reversed(messages):
        message_data = {
            "type": "chat_message",
            "message_id": msg.id,
            "sender_username": msg.sender.username, # Access sender's username
            "text": msg.text,
            "timestamp": msg.timestamp.isoformat()
        }
        await websocket.send_text(json.dumps(message_data))

    # Broadcast updated active users list to the room
    await manager.broadcast_active_users_list(room_id)

    try:
        while True:
            data = await websocket.receive_text()
            # Expecting data to be JSON string containing "text" of the message
            try:
                message_payload = json.loads(data)
                message_text = message_payload.get("text")
                if not message_text:
                    raise ValueError("Message text missing")
            except (json.JSONDecodeError, ValueError):
                # Send error back to client or just ignore malformed message
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid message format"}))
                continue

            # Save message to DB
            message_schema = schemas.MessageCreate(text=message_text, room_id=room_id, sender_id=current_user.id)
            db_message = crud.create_message(db=db, message=message_schema, sender_id=current_user.id)
            
            # Prepare message for broadcast
            broadcast_data = {
                "type": "chat_message",
                "message_id": db_message.id,
                "sender_username": current_user.username,
                "text": db_message.text,
                "timestamp": db_message.timestamp.isoformat()
            }
            await manager.broadcast_message(room_id, json.dumps(broadcast_data))

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket, user_username)
        # Broadcast updated active users list after disconnect
        await manager.broadcast_active_users_list(room_id)
    except Exception as e:
        # Catch any other unexpected errors and disconnect
        print(f"WebSocket error in room {room_id} for user {user_username}: {e}")
        manager.disconnect(room_id, websocket, user_username)
        await manager.broadcast_active_users_list(room_id) # Update list even on unexpected errors


# --- Remember to add a Pydantic Schema for Token in app/schemas.py ---
# Add this to app/schemas.py
# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: Optional[str] = None