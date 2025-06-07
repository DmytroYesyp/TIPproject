# app/websocket_manager.py
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect
import json 

class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections per room:
        # { room_id: [websocket1, websocket2, ...], ... }
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Dictionary to store active users per room (username only for simplicity for now):
        # { room_id: { username1: websocket1, username2: websocket2, ... }, ... }
        self.active_users_in_rooms: Dict[int, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket, username: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        if room_id not in self.active_users_in_rooms:
            self.active_users_in_rooms[room_id] = {}

        self.active_connections[room_id].append(websocket)
        self.active_users_in_rooms[room_id][username] = websocket # Store websocket by username

    def disconnect(self, room_id: int, websocket: WebSocket, username: str):
        if room_id in self.active_connections and websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)
        
        if room_id in self.active_users_in_rooms and username in self.active_users_in_rooms[room_id]:
            del self.active_users_in_rooms[room_id][username]

        # Clean up empty room entries
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]
        if not self.active_users_in_rooms[room_id]:
            del self.active_users_in_rooms[room_id]


    async def broadcast_message(self, room_id: int, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

    async def broadcast_active_users_list(self, room_id: int):
        if room_id in self.active_users_in_rooms:
            users_list = list(self.active_users_in_rooms[room_id].keys())
            message_data = {
                "type": "active_users_update",
                "users": users_list
            }
            # Send as JSON string to be parsed by client
            await self.broadcast_message(room_id, json.dumps(message_data))
        else:
            # If room is empty, broadcast an empty list
            message_data = {
                "type": "active_users_update",
                "users": []
            }
            await self.broadcast_message(room_id, json.dumps(message_data))

# Instantiate the manager
manager = ConnectionManager()