"""
WebSocket handler for real-time chat using Socket.IO
"""

import socketio
import jwt
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Set
import uuid

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'datefirst-secret-key-change-in-production')

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

# Track connected users: user_id -> set of session_ids
connected_users: Dict[str, Set[str]] = {}
# Track session to user mapping: sid -> user_id
session_to_user: Dict[str, str] = {}
# Track which threads users are in: sid -> thread_id
session_to_thread: Dict[str, str] = {}


def decode_token(token: str):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        return None


@sio.event
async def connect(sid, environ, auth):
    """Handle new connection"""
    logger.info(f"Client connecting: {sid}")
    
    # Get token from auth or query params
    token = None
    if auth and 'token' in auth:
        token = auth['token']
    elif 'HTTP_AUTHORIZATION' in environ:
        auth_header = environ['HTTP_AUTHORIZATION']
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if not token:
        logger.warning(f"Connection rejected - no token: {sid}")
        return False
    
    payload = decode_token(token)
    if not payload:
        logger.warning(f"Connection rejected - invalid token: {sid}")
        return False
    
    user_id = payload.get('user_id')
    if not user_id:
        return False
    
    # Track connection
    session_to_user[sid] = user_id
    if user_id not in connected_users:
        connected_users[user_id] = set()
    connected_users[user_id].add(sid)
    
    logger.info(f"User {user_id} connected with session {sid}")
    
    # Notify user they're connected
    await sio.emit('connected', {'user_id': user_id}, room=sid)
    
    return True


@sio.event
async def disconnect(sid):
    """Handle disconnection"""
    user_id = session_to_user.pop(sid, None)
    
    if user_id and user_id in connected_users:
        connected_users[user_id].discard(sid)
        if not connected_users[user_id]:
            del connected_users[user_id]
    
    # Remove from thread tracking
    session_to_thread.pop(sid, None)
    
    logger.info(f"User {user_id} disconnected (session {sid})")


@sio.event
async def join_thread(sid, data):
    """Join a chat thread room"""
    thread_id = data.get('thread_id')
    if not thread_id:
        return
    
    user_id = session_to_user.get(sid)
    if not user_id:
        return
    
    # Leave previous thread if any
    old_thread = session_to_thread.get(sid)
    if old_thread:
        await sio.leave_room(sid, f"thread_{old_thread}")
    
    # Join new thread room
    await sio.enter_room(sid, f"thread_{thread_id}")
    session_to_thread[sid] = thread_id
    
    logger.info(f"User {user_id} joined thread {thread_id}")
    
    # Notify room that user joined
    await sio.emit('user_joined', {
        'user_id': user_id,
        'thread_id': thread_id
    }, room=f"thread_{thread_id}", skip_sid=sid)


@sio.event
async def leave_thread(sid, data):
    """Leave a chat thread room"""
    thread_id = data.get('thread_id')
    if not thread_id:
        return
    
    await sio.leave_room(sid, f"thread_{thread_id}")
    session_to_thread.pop(sid, None)
    
    user_id = session_to_user.get(sid)
    logger.info(f"User {user_id} left thread {thread_id}")


@sio.event
async def typing(sid, data):
    """Handle typing indicator"""
    thread_id = data.get('thread_id')
    user_id = session_to_user.get(sid)
    
    if not thread_id or not user_id:
        return
    
    await sio.emit('user_typing', {
        'user_id': user_id,
        'thread_id': thread_id,
        'is_typing': data.get('is_typing', True)
    }, room=f"thread_{thread_id}", skip_sid=sid)


async def broadcast_new_message(thread_id: str, message: dict, sender_id: str):
    """Broadcast new message to thread participants"""
    await sio.emit('new_message', {
        'thread_id': thread_id,
        'message': message
    }, room=f"thread_{thread_id}")
    
    logger.info(f"Broadcast message to thread {thread_id}")


async def broadcast_date_plan_update(thread_id: str, date_plan: dict, updated_by: str):
    """Broadcast date plan update to thread"""
    await sio.emit('date_plan_updated', {
        'thread_id': thread_id,
        'date_plan': date_plan,
        'updated_by': updated_by
    }, room=f"thread_{thread_id}")


async def broadcast_match(user1_id: str, user2_id: str, match_data: dict):
    """Notify both users of a new match"""
    for user_id in [user1_id, user2_id]:
        if user_id in connected_users:
            for sid in connected_users[user_id]:
                await sio.emit('new_match', match_data, room=sid)


async def send_notification(user_id: str, notification: dict):
    """Send notification to a specific user"""
    if user_id in connected_users:
        for sid in connected_users[user_id]:
            await sio.emit('notification', notification, room=sid)


def is_user_online(user_id: str) -> bool:
    """Check if user is currently online"""
    return user_id in connected_users and len(connected_users[user_id]) > 0


def get_online_users() -> Set[str]:
    """Get set of online user IDs"""
    return set(connected_users.keys())
