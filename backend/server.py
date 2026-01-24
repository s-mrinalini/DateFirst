from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date
import bcrypt
import jwt
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'datefirst-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

app = FastAPI(title="DateFirst API v2")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FirstDateIdea(BaseModel):
    title: str
    description: str
    tags: List[str] = []
    city: str

class ProfileSetup(BaseModel):
    first_name: str
    main_photo: str
    city: str
    distance_preference: int = 50  # miles
    date_of_birth: str  # ISO date string
    gender: str  # male, female, non_binary
    interested_in: List[str]  # ["male", "female"]
    height: Optional[str] = None  # optional
    bio: Optional[str] = None  # optional, hidden pre-match
    date_preferences: List[str] = []  # coffee, dinner, outdoors, etc.
    first_date_idea: FirstDateIdea

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    main_photo: Optional[str] = None
    city: Optional[str] = None
    distance_preference: Optional[int] = None
    gender: Optional[str] = None
    interested_in: Optional[List[str]] = None
    height: Optional[str] = None
    bio: Optional[str] = None
    date_preferences: Optional[List[str]] = None
    first_date_idea: Optional[FirstDateIdea] = None

class ChatMessageCreate(BaseModel):
    content: str

class DatePlanUpdate(BaseModel):
    proposed_datetime: Optional[str] = None
    proposed_location: Optional[str] = None
    who_pays: Optional[str] = None  # i_pay, split, you_pay, decide_later
    is_confirmed: Optional[bool] = None

class ReportCreate(BaseModel):
    reported_user_id: str
    reason: str
    details: Optional[str] = None

class BlockCreate(BaseModel):
    blocked_user_id: str

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    from datetime import timedelta
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('user_id')
    except:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if not credentials:
        return None
    user_id = decode_token(credentials.credentials)
    if not user_id:
        return None
    return await db.users.find_one({"id": user_id}, {"_id": 0})

async def check_blocked(user_id: str, other_user_id: str) -> bool:
    block = await db.blocks.find_one({
        "$or": [
            {"blocker_id": user_id, "blocked_id": other_user_id},
            {"blocker_id": other_user_id, "blocked_id": user_id}
        ]
    })
    return block is not None

async def get_blocked_user_ids(user_id: str) -> List[str]:
    blocks = await db.blocks.find({
        "$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]
    }, {"_id": 0}).to_list(1000)
    blocked_ids = set()
    for block in blocks:
        blocked_ids.add(block['blocker_id'])
        blocked_ids.add(block['blocked_id'])
    blocked_ids.discard(user_id)
    return list(blocked_ids)

async def are_matched(user1_id: str, user2_id: str) -> bool:
    """Check if two users are matched (mutual likes)"""
    match = await db.matches.find_one({
        "$or": [
            {"user1_id": user1_id, "user2_id": user2_id},
            {"user1_id": user2_id, "user2_id": user1_id}
        ]
    })
    return match is not None

def get_public_profile(profile: dict) -> dict:
    """Return only pre-match visible fields"""
    return {
        "user_id": profile.get("user_id"),
        "first_name": profile.get("first_name"),
        "main_photo": profile.get("main_photo"),
        "city": profile.get("city"),
        "first_date_idea": profile.get("first_date_idea"),
        "date_preferences": profile.get("date_preferences", [])
    }

def get_full_profile(profile: dict) -> dict:
    """Return full profile for matched users"""
    return {
        "user_id": profile.get("user_id"),
        "first_name": profile.get("first_name"),
        "main_photo": profile.get("main_photo"),
        "city": profile.get("city"),
        "distance_preference": profile.get("distance_preference"),
        "date_of_birth": profile.get("date_of_birth"),
        "gender": profile.get("gender"),
        "interested_in": profile.get("interested_in"),
        "height": profile.get("height"),
        "bio": profile.get("bio"),
        "date_preferences": profile.get("date_preferences", []),
        "first_date_idea": profile.get("first_date_idea"),
        "created_at": profile.get("created_at")
    }

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup")
async def signup(data: UserCreate):
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "profile_complete": False,
        "created_at": now
    }
    
    await db.users.insert_one(user)
    token = create_token(user_id)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "profile_complete": False
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user or not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user['id'])
    profile = await db.profiles.find_one({"user_id": user['id']}, {"_id": 0})
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "profile_complete": user.get('profile_complete', False),
            "first_name": profile.get('first_name') if profile else None
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    return {
        "user": {
            "id": current_user['id'],
            "email": current_user['email'],
            "profile_complete": current_user.get('profile_complete', False)
        },
        "profile": get_full_profile(profile) if profile else None
    }

# ==================== PROFILE ROUTES ====================

@api_router.post("/profile/setup")
async def setup_profile(data: ProfileSetup, current_user: dict = Depends(get_current_user)):
    """Complete profile setup after signup"""
    now = datetime.now(timezone.utc).isoformat()
    
    profile = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "first_name": data.first_name,
        "main_photo": data.main_photo,
        "city": data.city,
        "distance_preference": data.distance_preference,
        "date_of_birth": data.date_of_birth,
        "gender": data.gender,
        "interested_in": data.interested_in,
        "height": data.height,
        "bio": data.bio,
        "date_preferences": data.date_preferences,
        "first_date_idea": data.first_date_idea.model_dump(),
        "created_at": now
    }
    
    # Check if profile exists (update) or create new
    existing = await db.profiles.find_one({"user_id": current_user['id']})
    if existing:
        await db.profiles.update_one({"user_id": current_user['id']}, {"$set": profile})
    else:
        await db.profiles.insert_one(profile)
    
    # Mark profile as complete
    await db.users.update_one({"id": current_user['id']}, {"$set": {"profile_complete": True}})
    
    profile.pop('_id', None)
    return {"message": "Profile setup complete", "profile": get_full_profile(profile)}

@api_router.put("/profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if k == 'first_date_idea':
                update_data[k] = v
            else:
                update_data[k] = v
    
    if update_data:
        await db.profiles.update_one({"user_id": current_user['id']}, {"$set": update_data})
    
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    return get_full_profile(profile)

@api_router.get("/profile/{user_id}")
async def get_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a user's profile - returns limited data unless matched"""
    if await check_blocked(current_user['id'], user_id):
        raise HTTPException(status_code=403, detail="User not available")
    
    profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if viewing own profile or matched
    if user_id == current_user['id'] or await are_matched(current_user['id'], user_id):
        return get_full_profile(profile)
    else:
        return get_public_profile(profile)

# ==================== DISCOVER ROUTES ====================

@api_router.get("/discover")
async def discover_profiles(
    interested_in: Optional[str] = None,  # male,female
    max_distance: Optional[int] = None,
    tags: Optional[str] = None,  # comma-separated
    sort_by: Optional[str] = "recommended",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get discovery feed of date invites"""
    my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    if not my_profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")
    
    # Get blocked users and users already liked/matched
    blocked_ids = await get_blocked_user_ids(current_user['id'])
    
    # Get users I've already liked
    my_likes = await db.likes.find({"liker_id": current_user['id']}, {"_id": 0}).to_list(1000)
    liked_ids = [like['liked_id'] for like in my_likes]
    
    # Get my matches
    my_matches = await db.matches.find({
        "$or": [{"user1_id": current_user['id']}, {"user2_id": current_user['id']}]
    }, {"_id": 0}).to_list(1000)
    matched_ids = []
    for m in my_matches:
        matched_ids.append(m['user1_id'] if m['user2_id'] == current_user['id'] else m['user2_id'])
    
    exclude_ids = set(blocked_ids + liked_ids + matched_ids + [current_user['id']])
    
    query: Dict[str, Any] = {"user_id": {"$nin": list(exclude_ids)}}
    
    # Filter by gender (interested_in)
    if interested_in:
        genders = interested_in.split(',')
        query['gender'] = {"$in": genders}
    elif my_profile.get('interested_in'):
        query['gender'] = {"$in": my_profile['interested_in']}
    
    # Filter by tags
    if tags:
        tag_list = tags.split(',')
        query['first_date_idea.tags'] = {"$in": tag_list}
    
    # Filter by city (simple distance approximation)
    if my_profile.get('city'):
        # For MVP, just filter by same city - in production would use geo queries
        query['city'] = {"$regex": my_profile['city'], "$options": "i"}
    
    skip = (page - 1) * limit
    sort_field = "created_at" if sort_by == "new" else "created_at"
    sort_dir = -1
    
    profiles = await db.profiles.find(query, {"_id": 0}).sort(sort_field, sort_dir).skip(skip).limit(limit).to_list(limit)
    total = await db.profiles.count_documents(query)
    
    # Return only public data (pre-match)
    invites = [get_public_profile(p) for p in profiles]
    
    return {
        "invites": invites,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }

# ==================== LIKE / MATCH ROUTES ====================

@api_router.post("/like/{user_id}")
async def like_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Like a user's invite - creates match if mutual"""
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot like yourself")
    
    if await check_blocked(current_user['id'], user_id):
        raise HTTPException(status_code=403, detail="User not available")
    
    # Check if already liked
    existing_like = await db.likes.find_one({
        "liker_id": current_user['id'],
        "liked_id": user_id
    })
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Create like
    like = {
        "id": str(uuid.uuid4()),
        "liker_id": current_user['id'],
        "liked_id": user_id,
        "created_at": now
    }
    await db.likes.insert_one(like)
    
    # Check for mutual like (match)
    mutual_like = await db.likes.find_one({
        "liker_id": user_id,
        "liked_id": current_user['id']
    })
    
    is_match = False
    match_id = None
    
    if mutual_like:
        # It's a match! Create match and chat thread
        is_match = True
        match_id = str(uuid.uuid4())
        
        match = {
            "id": match_id,
            "user1_id": current_user['id'],
            "user2_id": user_id,
            "created_at": now
        }
        await db.matches.insert_one(match)
        
        # Get profiles for chat thread
        my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        their_profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
        
        # Create chat thread
        thread = {
            "id": str(uuid.uuid4()),
            "match_id": match_id,
            "user1_id": current_user['id'],
            "user2_id": user_id,
            "user1_name": my_profile.get('first_name', 'User'),
            "user2_name": their_profile.get('first_name', 'User'),
            "user1_photo": my_profile.get('main_photo'),
            "user2_photo": their_profile.get('main_photo'),
            "matched_on_idea": their_profile.get('first_date_idea'),
            "date_plan": {
                "proposed_datetime": None,
                "proposed_location": None,
                "who_pays": None,
                "is_confirmed": False
            },
            "last_message": None,
            "last_message_at": None,
            "created_at": now
        }
        await db.chat_threads.insert_one(thread)
    
    return {
        "message": "It's a match!" if is_match else "Like sent",
        "is_match": is_match,
        "match_id": match_id
    }

@api_router.delete("/like/{user_id}")
async def unlike_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a like (pass)"""
    result = await db.likes.delete_one({
        "liker_id": current_user['id'],
        "liked_id": user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Like not found")
    return {"message": "Like removed"}

@api_router.get("/vibes")
async def get_vibes(current_user: dict = Depends(get_current_user)):
    """Get users who liked me (but I haven't liked back yet)"""
    # Get users who liked me
    likes_on_me = await db.likes.find({"liked_id": current_user['id']}, {"_id": 0}).to_list(1000)
    liker_ids = [like['liker_id'] for like in likes_on_me]
    
    # Get users I've liked back (already matched)
    my_likes = await db.likes.find({"liker_id": current_user['id']}, {"_id": 0}).to_list(1000)
    my_liked_ids = set([like['liked_id'] for like in my_likes])
    
    # Filter to only show unmatched likes
    pending_liker_ids = [lid for lid in liker_ids if lid not in my_liked_ids]
    
    blocked_ids = await get_blocked_user_ids(current_user['id'])
    pending_liker_ids = [lid for lid in pending_liker_ids if lid not in blocked_ids]
    
    profiles = []
    for uid in pending_liker_ids:
        profile = await db.profiles.find_one({"user_id": uid}, {"_id": 0})
        if profile:
            profiles.append(get_public_profile(profile))
    
    return {"vibes": profiles, "count": len(profiles)}

@api_router.get("/plans")
async def get_plans(current_user: dict = Depends(get_current_user)):
    """Get all matches (plans) with chat threads"""
    threads = await db.chat_threads.find({
        "$or": [
            {"user1_id": current_user['id']},
            {"user2_id": current_user['id']}
        ]
    }, {"_id": 0}).sort("last_message_at", -1).to_list(100)
    
    result = []
    for thread in threads:
        if thread['user1_id'] == current_user['id']:
            other_user_id = thread['user2_id']
            other_user_name = thread['user2_name']
            other_user_photo = thread.get('user2_photo')
        else:
            other_user_id = thread['user1_id']
            other_user_name = thread['user1_name']
            other_user_photo = thread.get('user1_photo')
        
        if await check_blocked(current_user['id'], other_user_id):
            continue
        
        result.append({
            "thread_id": thread['id'],
            "match_id": thread.get('match_id'),
            "other_user_id": other_user_id,
            "other_user_name": other_user_name,
            "other_user_photo": other_user_photo,
            "matched_on_idea": thread.get('matched_on_idea'),
            "date_plan": thread.get('date_plan'),
            "last_message": thread.get('last_message'),
            "last_message_at": thread.get('last_message_at'),
            "created_at": thread['created_at']
        })
    
    return {"plans": result}

# ==================== CHAT ROUTES ====================

@api_router.get("/chat/{thread_id}")
async def get_chat_thread(thread_id: str, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get other user's full profile (they're matched)
    other_user_id = thread['user2_id'] if thread['user1_id'] == current_user['id'] else thread['user1_id']
    
    if await check_blocked(current_user['id'], other_user_id):
        raise HTTPException(status_code=403, detail="Chat not available")
    
    other_profile = await db.profiles.find_one({"user_id": other_user_id}, {"_id": 0})
    
    return {
        "thread": {
            "id": thread['id'],
            "match_id": thread.get('match_id'),
            "matched_on_idea": thread.get('matched_on_idea'),
            "date_plan": thread.get('date_plan'),
            "created_at": thread['created_at']
        },
        "other_user": get_full_profile(other_profile) if other_profile else None
    }

@api_router.get("/chat/{thread_id}/messages")
async def get_messages(
    thread_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    messages = await db.chat_messages.find(
        {"thread_id": thread_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    messages.reverse()
    return {"messages": messages}

@api_router.post("/chat/{thread_id}/messages")
async def send_message(thread_id: str, data: ChatMessageCreate, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    other_user_id = thread['user2_id'] if thread['user1_id'] == current_user['id'] else thread['user1_id']
    if await check_blocked(current_user['id'], other_user_id):
        raise HTTPException(status_code=403, detail="Cannot send message")
    
    my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    
    message = {
        "id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "sender_id": current_user['id'],
        "sender_name": my_profile.get('first_name', 'User') if my_profile else 'User',
        "content": data.content,
        "created_at": now
    }
    
    await db.chat_messages.insert_one(message)
    message.pop('_id', None)
    
    # Update thread
    await db.chat_threads.update_one(
        {"id": thread_id},
        {"$set": {"last_message": data.content[:100], "last_message_at": now}}
    )
    
    return message

@api_router.put("/chat/{thread_id}/plan")
async def update_date_plan(thread_id: str, data: DatePlanUpdate, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            update_data[f"date_plan.{k}"] = v
    
    if update_data:
        await db.chat_threads.update_one({"id": thread_id}, {"$set": update_data})
    
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    return {"date_plan": thread.get('date_plan')}

# ==================== BLOCK / REPORT ====================

@api_router.post("/block")
async def block_user(data: BlockCreate, current_user: dict = Depends(get_current_user)):
    if data.blocked_user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    existing = await db.blocks.find_one({
        "blocker_id": current_user['id'],
        "blocked_id": data.blocked_user_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already blocked")
    
    block = {
        "id": str(uuid.uuid4()),
        "blocker_id": current_user['id'],
        "blocked_id": data.blocked_user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.blocks.insert_one(block)
    
    # Remove any existing likes/matches
    await db.likes.delete_many({
        "$or": [
            {"liker_id": current_user['id'], "liked_id": data.blocked_user_id},
            {"liker_id": data.blocked_user_id, "liked_id": current_user['id']}
        ]
    })
    await db.matches.delete_many({
        "$or": [
            {"user1_id": current_user['id'], "user2_id": data.blocked_user_id},
            {"user1_id": data.blocked_user_id, "user2_id": current_user['id']}
        ]
    })
    
    return {"message": "User blocked"}

@api_router.delete("/block/{user_id}")
async def unblock_user(user_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.blocks.delete_one({
        "blocker_id": current_user['id'],
        "blocked_id": user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Block not found")
    return {"message": "User unblocked"}

@api_router.get("/blocked")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    blocks = await db.blocks.find({"blocker_id": current_user['id']}, {"_id": 0}).to_list(100)
    blocked = []
    for block in blocks:
        profile = await db.profiles.find_one({"user_id": block['blocked_id']}, {"_id": 0})
        if profile:
            blocked.append({
                "user_id": block['blocked_id'],
                "first_name": profile.get('first_name'),
                "blocked_at": block['created_at']
            })
    return {"blocked": blocked}

@api_router.post("/report")
async def report_user(data: ReportCreate, current_user: dict = Depends(get_current_user)):
    report = {
        "id": str(uuid.uuid4()),
        "reporter_id": current_user['id'],
        "reported_user_id": data.reported_user_id,
        "reason": data.reason,
        "details": data.details,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reports.insert_one(report)
    return {"message": "Report submitted"}

# ==================== SEED DATA ====================

@api_router.post("/seed")
async def seed_database():
    # Clear existing data
    for collection in ['users', 'profiles', 'likes', 'matches', 'chat_threads', 'chat_messages', 'blocks', 'reports']:
        await db[collection].delete_many({})
    
    now = datetime.now(timezone.utc).isoformat()
    
    users_data = [
        {"first_name": "Emma", "email": "emma@example.com", "gender": "female", "interested_in": ["male"], "city": "Austin", "bio": "Coffee lover and adventure seeker. Love trying new cafes and spontaneous road trips.", "height": "5'6\"", "dob": "1996-05-15", "tags": ["coffee", "outdoors", "adventure"], "idea": {"title": "Coffee + Bookstore Wander", "description": "Let's grab artisan coffee and browse a cozy indie bookstore. I love discovering hidden literary gems!", "tags": ["coffee", "chill", "books"], "city": "Austin"}},
        {"first_name": "James", "email": "james@example.com", "gender": "male", "interested_in": ["female"], "city": "Austin", "bio": "Foodie and amateur chef. Always hunting for the best tacos in town.", "height": "5'11\"", "dob": "1993-08-22", "tags": ["dinner", "cooking", "music"], "idea": {"title": "Taco Crawl Adventure", "description": "I know all the best taco spots! Let's hit 3 places and rate them together. Bonus points if you love hot sauce.", "tags": ["food", "adventure", "casual"], "city": "Austin"}},
        {"first_name": "Sofia", "email": "sofia@example.com", "gender": "female", "interested_in": ["male"], "city": "Houston", "bio": "Art enthusiast and museum nerd. Could spend hours in a gallery.", "height": "5'4\"", "dob": "1997-11-03", "tags": ["museum", "art", "coffee"], "idea": {"title": "Gallery Hop + Wine", "description": "Houston's art district is amazing. Let's explore galleries and end with wine at a rooftop bar.", "tags": ["art", "wine", "culture"], "city": "Houston"}},
        {"first_name": "Michael", "email": "michael@example.com", "gender": "male", "interested_in": ["female"], "city": "Houston", "bio": "Weekend hiker and nature photographer. The outdoors is my happy place.", "height": "6'0\"", "dob": "1992-02-14", "tags": ["hiking", "outdoors", "photography"], "idea": {"title": "Sunrise Hike + Breakfast", "description": "Early bird? Let's catch sunrise at the nature trail and reward ourselves with brunch after!", "tags": ["outdoors", "active", "brunch"], "city": "Houston"}},
        {"first_name": "Olivia", "email": "olivia@example.com", "gender": "female", "interested_in": ["male"], "city": "Austin", "bio": "Wine sommelier in training. Love a good conversation over great wine.", "height": "5'7\"", "dob": "1994-07-28", "tags": ["wine", "dinner", "conversation"], "idea": {"title": "Wine Tasting Journey", "description": "I'll teach you about wine pairings at my favorite vineyard. No pretentiousness, just good vibes.", "tags": ["wine", "chill", "romantic"], "city": "Austin"}},
        {"first_name": "Ethan", "email": "ethan@example.com", "gender": "male", "interested_in": ["female"], "city": "Austin", "bio": "Tech by day, musician by night. Looking for someone to jam with (literally or figuratively).", "height": "5'10\"", "dob": "1995-12-10", "tags": ["music", "coffee", "creative"], "idea": {"title": "Live Music Discovery", "description": "Austin has the best live music scene. Let's find a hidden gem venue and discover our new favorite band.", "tags": ["music", "nightlife", "adventure"], "city": "Austin"}},
        {"first_name": "Ava", "email": "ava@example.com", "gender": "female", "interested_in": ["male"], "city": "Houston", "bio": "Yoga instructor who believes in balance - between namaste and taco Tuesdays.", "height": "5'5\"", "dob": "1998-03-20", "tags": ["fitness", "brunch", "chill"], "idea": {"title": "Yoga + Smoothie Bowls", "description": "Morning yoga in the park followed by the best açaí bowls in town. Peaceful but delicious!", "tags": ["fitness", "healthy", "outdoors"], "city": "Houston"}},
        {"first_name": "Noah", "email": "noah@example.com", "gender": "male", "interested_in": ["female"], "city": "Houston", "bio": "Stand-up comedy enthusiast. If you can make me laugh, you've already won.", "height": "6'2\"", "dob": "1991-09-05", "tags": ["comedy", "dinner", "fun"], "idea": {"title": "Comedy Show + Late Night Bites", "description": "Nothing breaks the ice like shared laughter. Open mic night, then we grab midnight tacos.", "tags": ["comedy", "fun", "nightlife"], "city": "Houston"}},
        {"first_name": "Isabella", "email": "isabella@example.com", "gender": "female", "interested_in": ["male"], "city": "Austin", "bio": "Travel blogger saving for the next adventure. Obsessed with farmers markets and vintage finds.", "height": "5'3\"", "dob": "1996-01-17", "tags": ["travel", "outdoors", "vintage"], "idea": {"title": "Farmers Market Morning", "description": "Saturday markets are my thing. Let's sample local treats, find vintage treasures, and people-watch.", "tags": ["food", "outdoors", "casual"], "city": "Austin"}},
        {"first_name": "Liam", "email": "liam@example.com", "gender": "male", "interested_in": ["female"], "city": "Austin", "bio": "Board game collector and craft beer enthusiast. Competitive but fun!", "height": "5'9\"", "dob": "1994-04-30", "tags": ["games", "beer", "fun"], "idea": {"title": "Board Game Café Battle", "description": "I'll teach you my favorite strategy games over craft beers. Warning: I'm annoyingly competitive.", "tags": ["games", "chill", "fun"], "city": "Austin"}},
        {"first_name": "Mia", "email": "mia@example.com", "gender": "female", "interested_in": ["male"], "city": "Houston", "bio": "Bookworm and tea connoisseur. Cozy vibes only.", "height": "5'2\"", "dob": "1997-06-12", "tags": ["books", "tea", "chill"], "idea": {"title": "Tea House & Poetry", "description": "There's a hidden tea house with live poetry readings. Let's be cultured together.", "tags": ["tea", "books", "culture"], "city": "Houston"}},
        {"first_name": "Lucas", "email": "lucas@example.com", "gender": "male", "interested_in": ["female"], "city": "Houston", "bio": "Rock climbing instructor. I'll catch you if you fall (literally).", "height": "6'1\"", "dob": "1993-10-08", "tags": ["climbing", "outdoors", "active"], "idea": {"title": "Indoor Climbing Adventure", "description": "First-timers welcome! I'll show you the ropes (pun intended) at the climbing gym. Trust falls included.", "tags": ["active", "adventure", "fun"], "city": "Houston"}}
    ]
    
    photos = [
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400",
        "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400"
    ]
    
    users = []
    for i, u in enumerate(users_data):
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": u['email'],
            "password_hash": hash_password("password123"),
            "profile_complete": True,
            "created_at": now
        }
        await db.users.insert_one(user)
        users.append({"id": user_id, **u})
        
        profile = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "first_name": u['first_name'],
            "main_photo": photos[i],
            "city": u['city'],
            "distance_preference": 50,
            "date_of_birth": u['dob'],
            "gender": u['gender'],
            "interested_in": u['interested_in'],
            "height": u['height'],
            "bio": u['bio'],
            "date_preferences": u['tags'],
            "first_date_idea": u['idea'],
            "created_at": now
        }
        await db.profiles.insert_one(profile)
    
    # Create likes to produce matches
    # Emma (0) <-> James (1) - Match
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[0]['id'], "liked_id": users[1]['id'], "created_at": now})
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[1]['id'], "liked_id": users[0]['id'], "created_at": now})
    
    # Sofia (2) <-> Michael (3) - Match
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[2]['id'], "liked_id": users[3]['id'], "created_at": now})
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[3]['id'], "liked_id": users[2]['id'], "created_at": now})
    
    # Olivia (4) <-> Ethan (5) - Match
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[4]['id'], "liked_id": users[5]['id'], "created_at": now})
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[5]['id'], "liked_id": users[4]['id'], "created_at": now})
    
    # Create matches
    matches = [
        {"user1": users[0], "user2": users[1]},
        {"user1": users[2], "user2": users[3]},
        {"user1": users[4], "user2": users[5]}
    ]
    
    for m in matches:
        match_id = str(uuid.uuid4())
        await db.matches.insert_one({
            "id": match_id,
            "user1_id": m['user1']['id'],
            "user2_id": m['user2']['id'],
            "created_at": now
        })
        
        thread_id = str(uuid.uuid4())
        thread = {
            "id": thread_id,
            "match_id": match_id,
            "user1_id": m['user1']['id'],
            "user2_id": m['user2']['id'],
            "user1_name": m['user1']['first_name'],
            "user2_name": m['user2']['first_name'],
            "user1_photo": photos[users_data.index(next(u for u in users_data if u['first_name'] == m['user1']['first_name']))],
            "user2_photo": photos[users_data.index(next(u for u in users_data if u['first_name'] == m['user2']['first_name']))],
            "matched_on_idea": m['user2']['idea'],
            "date_plan": {"proposed_datetime": None, "proposed_location": None, "who_pays": None, "is_confirmed": False},
            "last_message": "Hey! Excited about your date idea!",
            "last_message_at": now,
            "created_at": now
        }
        await db.chat_threads.insert_one(thread)
        
        # Add some messages
        messages = [
            {"sender": m['user1'], "content": f"Hey {m['user2']['first_name']}! Your date idea sounds amazing!"},
            {"sender": m['user2'], "content": f"Thanks! I've been wanting to try it. When works for you?"},
            {"sender": m['user1'], "content": "How about this weekend?"},
            {"sender": m['user2'], "content": "Perfect! Let's do it!"}
        ]
        for msg in messages:
            await db.chat_messages.insert_one({
                "id": str(uuid.uuid4()),
                "thread_id": thread_id,
                "sender_id": msg['sender']['id'],
                "sender_name": msg['sender']['first_name'],
                "content": msg['content'],
                "created_at": now
            })
    
    # Add some pending likes (vibes)
    # Ava (6) likes James (1)
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[6]['id'], "liked_id": users[1]['id'], "created_at": now})
    # Mia (10) likes Ethan (5)
    await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": users[10]['id'], "liked_id": users[5]['id'], "created_at": now})
    
    return {"message": "Database seeded", "users": 12, "matches": 3}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
