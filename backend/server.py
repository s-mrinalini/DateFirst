from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect, UploadFile, File
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
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import re
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'datefirst-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Create the main app
app = FastAPI(title="DateFirst API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Profanity filter - simple list
PROFANITY_WORDS = ['badword1', 'badword2', 'spam', 'scam']

def contains_profanity(text: str) -> bool:
    text_lower = text.lower()
    return any(word in text_lower for word in PROFANITY_WORDS)

def clean_text(text: str) -> str:
    """Basic profanity filter"""
    for word in PROFANITY_WORDS:
        text = re.sub(re.escape(word), '***', text, flags=re.IGNORECASE)
    return text

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    first_name: str
    is_premium: bool = False
    created_at: str

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    preferred_genders: Optional[List[str]] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    profile_photo: Optional[str] = None
    extra_photos: Optional[List[str]] = None
    job_title: Optional[str] = None
    interests: Optional[List[str]] = None
    intent: Optional[str] = None  # relationship, casual, new_friends
    safety_preferences: Optional[str] = None

class ProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    first_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    preferred_genders: Optional[List[str]] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    profile_photo: Optional[str] = None
    extra_photos: Optional[List[str]] = None
    job_title: Optional[str] = None
    interests: Optional[List[str]] = None
    intent: Optional[str] = None
    is_premium: bool = False
    created_at: str

class DatePostCreate(BaseModel):
    title: str
    description: str
    city: str
    place_name: Optional[str] = None
    map_link: Optional[str] = None
    date_time: str  # ISO format
    duration: Optional[str] = None
    who_pays: str  # i_pay, split, you_pay, decide_later
    tags: List[str] = []
    preferred_genders: Optional[List[str]] = None
    age_range_min: Optional[int] = None
    age_range_max: Optional[int] = None
    max_applicants: int = 10
    application_deadline: Optional[str] = None

class DatePostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    place_name: Optional[str] = None
    map_link: Optional[str] = None
    date_time: Optional[str] = None
    duration: Optional[str] = None
    who_pays: Optional[str] = None
    tags: Optional[List[str]] = None
    preferred_genders: Optional[List[str]] = None
    age_range_min: Optional[int] = None
    age_range_max: Optional[int] = None
    max_applicants: Optional[int] = None
    application_deadline: Optional[str] = None
    status: Optional[str] = None

class DatePostResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    poster_id: str
    poster_name: str
    poster_photo: Optional[str] = None
    title: str
    description: str
    city: str
    place_name: Optional[str] = None
    map_link: Optional[str] = None
    date_time: str
    duration: Optional[str] = None
    who_pays: str
    tags: List[str] = []
    preferred_genders: Optional[List[str]] = None
    age_range_min: Optional[int] = None
    age_range_max: Optional[int] = None
    max_applicants: int = 10
    application_deadline: Optional[str] = None
    status: str  # OPEN, CLOSED, SELECTED, COMPLETED, CANCELLED
    like_count: int = 0
    application_count: int = 0
    created_at: str
    is_liked: bool = False
    has_applied: bool = False

class ApplicationCreate(BaseModel):
    message: str
    quick_answers: Optional[Dict[str, str]] = None

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    date_post_id: str
    applicant_id: str
    applicant_name: str
    applicant_age: Optional[int] = None
    applicant_city: Optional[str] = None
    applicant_photo: Optional[str] = None
    applicant_bio: Optional[str] = None
    # Premium fields (will be None for non-premium viewers)
    applicant_extra_photos: Optional[List[str]] = None
    applicant_job_title: Optional[str] = None
    applicant_interests: Optional[List[str]] = None
    applicant_intent: Optional[str] = None
    compatibility_score: Optional[int] = None
    message: str
    quick_answers: Optional[Dict[str, str]] = None
    status: str  # pending, accepted, declined, withdrawn
    created_at: str
    is_premium_locked: bool = False

class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    thread_id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: str
    is_read: bool = False

class ChatThreadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    date_post_id: str
    date_post_title: str
    user1_id: str
    user2_id: str
    other_user_id: str
    other_user_name: str
    other_user_photo: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    unread_count: int = 0
    confirmed_time: Optional[str] = None
    confirmed_location: Optional[str] = None
    confirmed_who_pays: Optional[str] = None
    is_confirmed: bool = False
    created_at: str

class ReportCreate(BaseModel):
    reported_user_id: Optional[str] = None
    reported_post_id: Optional[str] = None
    reason: str
    details: Optional[str] = None

class BlockCreate(BaseModel):
    blocked_user_id: str

class ConfirmDateDetails(BaseModel):
    confirmed_time: Optional[str] = None
    confirmed_location: Optional[str] = None
    confirmed_who_pays: Optional[str] = None
    is_confirmed: Optional[bool] = None

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
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
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        return None
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user

async def check_blocked(user_id: str, other_user_id: str) -> bool:
    """Check if either user has blocked the other"""
    block = await db.blocks.find_one({
        "$or": [
            {"blocker_id": user_id, "blocked_id": other_user_id},
            {"blocker_id": other_user_id, "blocked_id": user_id}
        ]
    })
    return block is not None

async def get_blocked_user_ids(user_id: str) -> List[str]:
    """Get all user IDs that are blocked by or have blocked this user"""
    blocks = await db.blocks.find({
        "$or": [
            {"blocker_id": user_id},
            {"blocked_id": user_id}
        ]
    }, {"_id": 0}).to_list(1000)
    
    blocked_ids = set()
    for block in blocks:
        blocked_ids.add(block['blocker_id'])
        blocked_ids.add(block['blocked_id'])
    blocked_ids.discard(user_id)
    return list(blocked_ids)

def calculate_compatibility(profile1: dict, profile2: dict) -> int:
    """Basic compatibility heuristic"""
    score = 50  # Base score
    
    # Same city bonus
    if profile1.get('city') and profile2.get('city'):
        if profile1['city'].lower() == profile2['city'].lower():
            score += 15
    
    # Age range compatibility
    age1 = profile1.get('age')
    age2 = profile2.get('age')
    if age1 and age2:
        age_diff = abs(age1 - age2)
        if age_diff <= 3:
            score += 15
        elif age_diff <= 7:
            score += 10
        elif age_diff <= 12:
            score += 5
    
    # Shared interests
    interests1 = set(profile1.get('interests', []))
    interests2 = set(profile2.get('interests', []))
    if interests1 and interests2:
        shared = len(interests1.intersection(interests2))
        score += min(shared * 5, 20)
    
    # Intent match
    if profile1.get('intent') and profile2.get('intent'):
        if profile1['intent'] == profile2['intent']:
            score += 10
    
    return min(score, 100)

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup")
async def signup(data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "first_name": data.first_name,
        "is_premium": False,
        "applications_today": 0,
        "last_application_date": None,
        "created_at": now
    }
    
    await db.users.insert_one(user)
    
    # Create profile
    profile = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "first_name": data.first_name,
        "age": None,
        "gender": None,
        "preferred_genders": [],
        "city": None,
        "bio": None,
        "profile_photo": None,
        "extra_photos": [],
        "job_title": None,
        "interests": [],
        "intent": None,
        "safety_preferences": None,
        "created_at": now
    }
    await db.profiles.insert_one(profile)
    
    token = create_token(user_id)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "first_name": data.first_name,
            "is_premium": False,
            "created_at": now
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user['id'])
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "first_name": user['first_name'],
            "is_premium": user.get('is_premium', False),
            "created_at": user['created_at']
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    return {
        "user": {
            "id": current_user['id'],
            "email": current_user['email'],
            "first_name": current_user['first_name'],
            "is_premium": current_user.get('is_premium', False),
            "created_at": current_user['created_at']
        },
        "profile": profile
    }

# ==================== PROFILE ROUTES ====================

@api_router.get("/profile/{user_id}")
async def get_profile(user_id: str, current_user: dict = Depends(get_optional_user)):
    profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if blocked
    if current_user:
        if await check_blocked(current_user['id'], user_id):
            raise HTTPException(status_code=403, detail="User not available")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    profile['is_premium'] = user.get('is_premium', False) if user else False
    
    return profile

@api_router.put("/profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if update_data:
        await db.profiles.update_one(
            {"user_id": current_user['id']},
            {"$set": update_data}
        )
        
        # Update first_name in user too
        if 'first_name' in update_data:
            await db.users.update_one(
                {"id": current_user['id']},
                {"$set": {"first_name": update_data['first_name']}}
            )
    
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    return profile

# ==================== DATE POST ROUTES ====================

@api_router.post("/dates")
async def create_date_post(data: DatePostCreate, current_user: dict = Depends(get_current_user)):
    # Check profanity
    if contains_profanity(data.title) or contains_profanity(data.description):
        raise HTTPException(status_code=400, detail="Content contains inappropriate language")
    
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    post = {
        "id": post_id,
        "poster_id": current_user['id'],
        "poster_name": current_user['first_name'],
        "poster_photo": profile.get('profile_photo') if profile else None,
        "title": clean_text(data.title),
        "description": clean_text(data.description),
        "city": data.city,
        "place_name": data.place_name,
        "map_link": data.map_link,
        "date_time": data.date_time,
        "duration": data.duration,
        "who_pays": data.who_pays,
        "tags": data.tags,
        "preferred_genders": data.preferred_genders,
        "age_range_min": data.age_range_min,
        "age_range_max": data.age_range_max,
        "max_applicants": data.max_applicants,
        "application_deadline": data.application_deadline,
        "status": "OPEN",
        "like_count": 0,
        "application_count": 0,
        "created_at": now
    }
    
    await db.date_posts.insert_one(post)
    post.pop('_id', None)  # Remove MongoDB ObjectId before returning
    return post

@api_router.get("/dates")
async def get_date_posts(
    city: Optional[str] = None,
    tags: Optional[str] = None,
    who_pays: Optional[str] = None,
    time_filter: Optional[str] = None,  # today, this_week
    status: Optional[str] = "OPEN",
    search: Optional[str] = None,
    sort_by: Optional[str] = "newest",  # newest, soonest, popular
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_optional_user)
):
    query: Dict[str, Any] = {}
    
    # Get blocked users if logged in
    blocked_ids = []
    if current_user:
        blocked_ids = await get_blocked_user_ids(current_user['id'])
        if blocked_ids:
            query['poster_id'] = {"$nin": blocked_ids}
    
    if city:
        query['city'] = {"$regex": city, "$options": "i"}
    
    if tags:
        tag_list = tags.split(',')
        query['tags'] = {"$in": tag_list}
    
    if who_pays:
        query['who_pays'] = who_pays
    
    if status:
        query['status'] = status
    
    if search:
        query['$or'] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if time_filter:
        now = datetime.now(timezone.utc)
        if time_filter == "today":
            end = now.replace(hour=23, minute=59, second=59)
            query['date_time'] = {"$lte": end.isoformat()}
        elif time_filter == "this_week":
            end = now + timedelta(days=7)
            query['date_time'] = {"$lte": end.isoformat()}
    
    # Sort
    sort_field = "created_at"
    sort_dir = -1
    if sort_by == "soonest":
        sort_field = "date_time"
        sort_dir = 1
    elif sort_by == "popular":
        sort_field = "like_count"
        sort_dir = -1
    
    skip = (page - 1) * limit
    
    posts = await db.date_posts.find(query, {"_id": 0}).sort(sort_field, sort_dir).skip(skip).limit(limit).to_list(limit)
    total = await db.date_posts.count_documents(query)
    
    # Add user-specific fields
    if current_user:
        for post in posts:
            like = await db.likes.find_one({"user_id": current_user['id'], "date_post_id": post['id']})
            post['is_liked'] = like is not None
            
            application = await db.applications.find_one({
                "applicant_id": current_user['id'],
                "date_post_id": post['id'],
                "status": {"$ne": "withdrawn"}
            })
            post['has_applied'] = application is not None
    else:
        for post in posts:
            post['is_liked'] = False
            post['has_applied'] = False
    
    return {
        "posts": posts,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/dates/{post_id}")
async def get_date_post(post_id: str, current_user: dict = Depends(get_optional_user)):
    post = await db.date_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    # Check if blocked
    if current_user:
        if await check_blocked(current_user['id'], post['poster_id']):
            raise HTTPException(status_code=403, detail="Content not available")
        
        like = await db.likes.find_one({"user_id": current_user['id'], "date_post_id": post_id})
        post['is_liked'] = like is not None
        
        application = await db.applications.find_one({
            "applicant_id": current_user['id'],
            "date_post_id": post_id,
            "status": {"$ne": "withdrawn"}
        })
        post['has_applied'] = application is not None
    else:
        post['is_liked'] = False
        post['has_applied'] = False
    
    return post

@api_router.put("/dates/{post_id}")
async def update_date_post(post_id: str, data: DatePostUpdate, current_user: dict = Depends(get_current_user)):
    post = await db.date_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    if post['poster_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Check profanity in updates
    if 'title' in update_data and contains_profanity(update_data['title']):
        raise HTTPException(status_code=400, detail="Content contains inappropriate language")
    if 'description' in update_data and contains_profanity(update_data['description']):
        raise HTTPException(status_code=400, detail="Content contains inappropriate language")
    
    if update_data:
        await db.date_posts.update_one({"id": post_id}, {"$set": update_data})
    
    post = await db.date_posts.find_one({"id": post_id}, {"_id": 0})
    return post

@api_router.delete("/dates/{post_id}")
async def delete_date_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = await db.date_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    if post['poster_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.date_posts.delete_one({"id": post_id})
    await db.applications.delete_many({"date_post_id": post_id})
    await db.likes.delete_many({"date_post_id": post_id})
    
    return {"message": "Date post deleted"}

@api_router.get("/my-dates")
async def get_my_date_posts(current_user: dict = Depends(get_current_user)):
    posts = await db.date_posts.find({"poster_id": current_user['id']}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for post in posts:
        post['is_liked'] = False
        post['has_applied'] = False
    
    return posts

# ==================== LIKE ROUTES ====================

@api_router.post("/dates/{post_id}/like")
async def like_date_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = await db.date_posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    existing = await db.likes.find_one({"user_id": current_user['id'], "date_post_id": post_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")
    
    like = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "date_post_id": post_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.likes.insert_one(like)
    await db.date_posts.update_one({"id": post_id}, {"$inc": {"like_count": 1}})
    
    return {"message": "Liked"}

@api_router.delete("/dates/{post_id}/like")
async def unlike_date_post(post_id: str, current_user: dict = Depends(get_current_user)):
    existing = await db.likes.find_one({"user_id": current_user['id'], "date_post_id": post_id})
    if not existing:
        raise HTTPException(status_code=400, detail="Not liked")
    
    await db.likes.delete_one({"user_id": current_user['id'], "date_post_id": post_id})
    await db.date_posts.update_one({"id": post_id}, {"$inc": {"like_count": -1}})
    
    return {"message": "Unliked"}

# ==================== APPLICATION ROUTES ====================

@api_router.post("/dates/{post_id}/apply")
async def apply_to_date(post_id: str, data: ApplicationCreate, current_user: dict = Depends(get_current_user)):
    post = await db.date_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    # Can't apply to own post
    if post['poster_id'] == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot apply to your own date")
    
    # Check if blocked
    if await check_blocked(current_user['id'], post['poster_id']):
        raise HTTPException(status_code=403, detail="Cannot apply to this date")
    
    # Check status
    if post['status'] != "OPEN":
        raise HTTPException(status_code=400, detail="Date is no longer accepting applications")
    
    # Check deadline
    if post.get('application_deadline'):
        deadline = datetime.fromisoformat(post['application_deadline'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > deadline:
            raise HTTPException(status_code=400, detail="Application deadline has passed")
    
    # Check if already applied
    existing = await db.applications.find_one({
        "applicant_id": current_user['id'],
        "date_post_id": post_id,
        "status": {"$ne": "withdrawn"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already applied")
    
    # Rate limit: max 10 applications per day
    today = datetime.now(timezone.utc).date().isoformat()
    user = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    if user.get('last_application_date') == today:
        if user.get('applications_today', 0) >= 10:
            raise HTTPException(status_code=429, detail="Daily application limit reached (10/day)")
        await db.users.update_one(
            {"id": current_user['id']},
            {"$inc": {"applications_today": 1}}
        )
    else:
        await db.users.update_one(
            {"id": current_user['id']},
            {"$set": {"applications_today": 1, "last_application_date": today}}
        )
    
    # Check profanity
    if contains_profanity(data.message):
        raise HTTPException(status_code=400, detail="Message contains inappropriate language")
    
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    application = {
        "id": str(uuid.uuid4()),
        "date_post_id": post_id,
        "applicant_id": current_user['id'],
        "applicant_name": current_user['first_name'],
        "applicant_age": profile.get('age') if profile else None,
        "applicant_city": profile.get('city') if profile else None,
        "applicant_photo": profile.get('profile_photo') if profile else None,
        "applicant_bio": profile.get('bio') if profile else None,
        "applicant_extra_photos": profile.get('extra_photos') if profile else [],
        "applicant_job_title": profile.get('job_title') if profile else None,
        "applicant_interests": profile.get('interests') if profile else [],
        "applicant_intent": profile.get('intent') if profile else None,
        "message": clean_text(data.message),
        "quick_answers": data.quick_answers,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.applications.insert_one(application)
    await db.date_posts.update_one({"id": post_id}, {"$inc": {"application_count": 1}})
    
    return {"message": "Application submitted", "application_id": application['id']}

@api_router.delete("/applications/{application_id}")
async def withdraw_application(application_id: str, current_user: dict = Depends(get_current_user)):
    application = await db.applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application['applicant_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if application['status'] != "pending":
        raise HTTPException(status_code=400, detail="Can only withdraw pending applications")
    
    await db.applications.update_one({"id": application_id}, {"$set": {"status": "withdrawn"}})
    await db.date_posts.update_one({"id": application['date_post_id']}, {"$inc": {"application_count": -1}})
    
    return {"message": "Application withdrawn"}

@api_router.get("/dates/{post_id}/applications")
async def get_applications(post_id: str, current_user: dict = Depends(get_current_user)):
    post = await db.date_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    if post['poster_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    applications = await db.applications.find(
        {"date_post_id": post_id, "status": {"$ne": "withdrawn"}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get poster profile for compatibility calculation
    poster_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    is_premium = current_user.get('is_premium', False)
    
    for app in applications:
        # Calculate compatibility
        applicant_profile = await db.profiles.find_one({"user_id": app['applicant_id']}, {"_id": 0})
        if applicant_profile and poster_profile:
            app['compatibility_score'] = calculate_compatibility(poster_profile, applicant_profile)
        else:
            app['compatibility_score'] = 50
        
        # Lock premium fields for non-premium users
        if not is_premium:
            app['is_premium_locked'] = True
            app['applicant_extra_photos'] = None
            app['applicant_job_title'] = None
            app['applicant_interests'] = None
            app['applicant_intent'] = None
            app['compatibility_score'] = None
        else:
            app['is_premium_locked'] = False
    
    return applications

@api_router.post("/applications/{application_id}/accept")
async def accept_application(application_id: str, current_user: dict = Depends(get_current_user)):
    application = await db.applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    post = await db.date_posts.find_one({"id": application['date_post_id']}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Date post not found")
    
    if post['poster_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if post['status'] != "OPEN":
        raise HTTPException(status_code=400, detail="Date is no longer open")
    
    if application['status'] != "pending":
        raise HTTPException(status_code=400, detail="Application is not pending")
    
    # Accept this application
    await db.applications.update_one({"id": application_id}, {"$set": {"status": "accepted"}})
    
    # Decline all other applications
    await db.applications.update_many(
        {"date_post_id": post['id'], "id": {"$ne": application_id}, "status": "pending"},
        {"$set": {"status": "declined"}}
    )
    
    # Update post status
    await db.date_posts.update_one({"id": post['id']}, {"$set": {"status": "SELECTED"}})
    
    # Create chat thread
    thread = {
        "id": str(uuid.uuid4()),
        "date_post_id": post['id'],
        "date_post_title": post['title'],
        "user1_id": current_user['id'],
        "user2_id": application['applicant_id'],
        "user1_name": current_user['first_name'],
        "user2_name": application['applicant_name'],
        "user1_photo": post.get('poster_photo'),
        "user2_photo": application.get('applicant_photo'),
        "last_message": None,
        "last_message_at": None,
        "unread_count_user1": 0,
        "unread_count_user2": 0,
        "confirmed_time": None,
        "confirmed_location": None,
        "confirmed_who_pays": None,
        "is_confirmed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_threads.insert_one(thread)
    
    return {"message": "Application accepted", "thread_id": thread['id']}

@api_router.get("/my-applications")
async def get_my_applications(current_user: dict = Depends(get_current_user)):
    applications = await db.applications.find(
        {"applicant_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Add date post info
    for app in applications:
        post = await db.date_posts.find_one({"id": app['date_post_id']}, {"_id": 0})
        if post:
            app['date_post'] = {
                "id": post['id'],
                "title": post['title'],
                "date_time": post['date_time'],
                "city": post['city'],
                "status": post['status']
            }
    
    return applications

# ==================== CHAT ROUTES ====================

@api_router.get("/chat/threads")
async def get_chat_threads(current_user: dict = Depends(get_current_user)):
    threads = await db.chat_threads.find({
        "$or": [
            {"user1_id": current_user['id']},
            {"user2_id": current_user['id']}
        ]
    }, {"_id": 0}).sort("last_message_at", -1).to_list(100)
    
    result = []
    for thread in threads:
        # Determine the other user
        if thread['user1_id'] == current_user['id']:
            other_user_id = thread['user2_id']
            other_user_name = thread['user2_name']
            other_user_photo = thread.get('user2_photo')
            unread_count = thread.get('unread_count_user1', 0)
        else:
            other_user_id = thread['user1_id']
            other_user_name = thread['user1_name']
            other_user_photo = thread.get('user1_photo')
            unread_count = thread.get('unread_count_user2', 0)
        
        # Check if blocked
        if await check_blocked(current_user['id'], other_user_id):
            continue
        
        result.append({
            "id": thread['id'],
            "date_post_id": thread['date_post_id'],
            "date_post_title": thread['date_post_title'],
            "user1_id": thread['user1_id'],
            "user2_id": thread['user2_id'],
            "other_user_id": other_user_id,
            "other_user_name": other_user_name,
            "other_user_photo": other_user_photo,
            "last_message": thread.get('last_message'),
            "last_message_at": thread.get('last_message_at'),
            "unread_count": unread_count,
            "confirmed_time": thread.get('confirmed_time'),
            "confirmed_location": thread.get('confirmed_location'),
            "confirmed_who_pays": thread.get('confirmed_who_pays'),
            "is_confirmed": thread.get('is_confirmed', False),
            "created_at": thread['created_at']
        })
    
    return result

@api_router.get("/chat/threads/{thread_id}")
async def get_chat_thread(thread_id: str, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Determine the other user
    if thread['user1_id'] == current_user['id']:
        other_user_id = thread['user2_id']
        other_user_name = thread['user2_name']
        other_user_photo = thread.get('user2_photo')
    else:
        other_user_id = thread['user1_id']
        other_user_name = thread['user1_name']
        other_user_photo = thread.get('user1_photo')
    
    # Check if blocked
    if await check_blocked(current_user['id'], other_user_id):
        raise HTTPException(status_code=403, detail="Chat not available")
    
    return {
        "id": thread['id'],
        "date_post_id": thread['date_post_id'],
        "date_post_title": thread['date_post_title'],
        "user1_id": thread['user1_id'],
        "user2_id": thread['user2_id'],
        "other_user_id": other_user_id,
        "other_user_name": other_user_name,
        "other_user_photo": other_user_photo,
        "confirmed_time": thread.get('confirmed_time'),
        "confirmed_location": thread.get('confirmed_location'),
        "confirmed_who_pays": thread.get('confirmed_who_pays'),
        "is_confirmed": thread.get('is_confirmed', False),
        "created_at": thread['created_at']
    }

@api_router.get("/chat/threads/{thread_id}/messages")
async def get_chat_messages(
    thread_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query: Dict[str, Any] = {"thread_id": thread_id}
    if before:
        query['created_at'] = {"$lt": before}
    
    messages = await db.chat_messages.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    messages.reverse()
    
    # Mark messages as read
    if thread['user1_id'] == current_user['id']:
        await db.chat_threads.update_one({"id": thread_id}, {"$set": {"unread_count_user1": 0}})
    else:
        await db.chat_threads.update_one({"id": thread_id}, {"$set": {"unread_count_user2": 0}})
    
    await db.chat_messages.update_many(
        {"thread_id": thread_id, "sender_id": {"$ne": current_user['id']}, "is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return messages

@api_router.post("/chat/threads/{thread_id}/messages")
async def send_chat_message(thread_id: str, data: ChatMessageCreate, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if blocked
    other_user_id = thread['user2_id'] if thread['user1_id'] == current_user['id'] else thread['user1_id']
    if await check_blocked(current_user['id'], other_user_id):
        raise HTTPException(status_code=403, detail="Cannot send message")
    
    if contains_profanity(data.content):
        raise HTTPException(status_code=400, detail="Message contains inappropriate language")
    
    now = datetime.now(timezone.utc).isoformat()
    
    message = {
        "id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "sender_id": current_user['id'],
        "sender_name": current_user['first_name'],
        "content": clean_text(data.content),
        "is_read": False,
        "created_at": now
    }
    
    await db.chat_messages.insert_one(message)
    message.pop('_id', None)  # Remove MongoDB ObjectId before returning
    
    # Update thread
    update_data: Dict[str, Any] = {
        "last_message": data.content[:100],
        "last_message_at": now
    }
    
    if thread['user1_id'] == current_user['id']:
        update_data['$inc'] = {"unread_count_user2": 1}
    else:
        update_data['$inc'] = {"unread_count_user1": 1}
    
    if '$inc' in update_data:
        inc_data = update_data.pop('$inc')
        await db.chat_threads.update_one({"id": thread_id}, {"$set": update_data, "$inc": inc_data})
    else:
        await db.chat_threads.update_one({"id": thread_id}, {"$set": update_data})
    
    return message

@api_router.put("/chat/threads/{thread_id}/confirm")
async def confirm_date_details(thread_id: str, data: ConfirmDateDetails, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if update_data:
        await db.chat_threads.update_one({"id": thread_id}, {"$set": update_data})
    
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    return thread

# ==================== BLOCK & REPORT ROUTES ====================

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

@api_router.get("/blocked-users")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    blocks = await db.blocks.find({"blocker_id": current_user['id']}, {"_id": 0}).to_list(100)
    
    blocked_users = []
    for block in blocks:
        user = await db.users.find_one({"id": block['blocked_id']}, {"_id": 0, "password_hash": 0})
        if user:
            blocked_users.append({
                "id": user['id'],
                "first_name": user['first_name'],
                "blocked_at": block['created_at']
            })
    
    return blocked_users

@api_router.post("/report")
async def report_content(data: ReportCreate, current_user: dict = Depends(get_current_user)):
    report = {
        "id": str(uuid.uuid4()),
        "reporter_id": current_user['id'],
        "reported_user_id": data.reported_user_id,
        "reported_post_id": data.reported_post_id,
        "reason": data.reason,
        "details": data.details,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reports.insert_one(report)
    return {"message": "Report submitted"}

# ==================== PREMIUM ROUTES ====================

@api_router.post("/upgrade")
async def upgrade_to_premium(current_user: dict = Depends(get_current_user)):
    """Placeholder for premium upgrade - would integrate payment in production"""
    await db.users.update_one({"id": current_user['id']}, {"$set": {"is_premium": True}})
    return {"message": "Upgraded to premium", "is_premium": True}

@api_router.post("/downgrade")
async def downgrade_from_premium(current_user: dict = Depends(get_current_user)):
    """Placeholder for premium downgrade"""
    await db.users.update_one({"id": current_user['id']}, {"$set": {"is_premium": False}})
    return {"message": "Downgraded from premium", "is_premium": False}

# ==================== SEED DATA ====================

@api_router.post("/seed")
async def seed_database():
    """Seed the database with sample data"""
    # Clear existing data
    await db.users.delete_many({})
    await db.profiles.delete_many({})
    await db.date_posts.delete_many({})
    await db.applications.delete_many({})
    await db.likes.delete_many({})
    await db.chat_threads.delete_many({})
    await db.chat_messages.delete_many({})
    await db.blocks.delete_many({})
    await db.reports.delete_many({})
    
    now = datetime.now(timezone.utc)
    
    # Sample users
    users_data = [
        {"first_name": "Emma", "email": "emma@example.com", "gender": "female", "age": 28, "city": "Austin", "bio": "Coffee enthusiast and hiking lover", "intent": "relationship", "interests": ["coffee", "hiking", "photography"]},
        {"first_name": "James", "email": "james@example.com", "gender": "male", "age": 32, "city": "Austin", "bio": "Foodie exploring the city", "intent": "relationship", "interests": ["dinner", "museum", "wine"]},
        {"first_name": "Sofia", "email": "sofia@example.com", "gender": "female", "age": 26, "city": "Houston", "bio": "Art lover and museum enthusiast", "intent": "casual", "interests": ["museum", "art", "coffee"]},
        {"first_name": "Michael", "email": "michael@example.com", "gender": "male", "age": 29, "city": "Houston", "bio": "Adventure seeker", "intent": "relationship", "interests": ["hiking", "outdoors", "travel"]},
        {"first_name": "Olivia", "email": "olivia@example.com", "gender": "female", "age": 31, "city": "Austin", "bio": "Wine lover and bookworm", "intent": "new_friends", "interests": ["wine", "books", "dinner"]},
        {"first_name": "Ethan", "email": "ethan@example.com", "gender": "male", "age": 27, "city": "Austin", "bio": "Tech guy who loves outdoors", "intent": "relationship", "interests": ["hiking", "coffee", "tech"]},
        {"first_name": "Ava", "email": "ava@example.com", "gender": "female", "age": 25, "city": "Houston", "bio": "Fitness enthusiast and foodie", "intent": "casual", "interests": ["fitness", "dinner", "coffee"]},
        {"first_name": "Noah", "email": "noah@example.com", "gender": "male", "age": 33, "city": "Houston", "bio": "Music lover and concert goer", "intent": "relationship", "interests": ["music", "concerts", "dinner"]},
        {"first_name": "Isabella", "email": "isabella@example.com", "gender": "female", "age": 29, "city": "Austin", "bio": "Travel enthusiast exploring local gems", "intent": "new_friends", "interests": ["travel", "coffee", "photography"]},
        {"first_name": "Liam", "email": "liam@example.com", "gender": "male", "age": 30, "city": "Austin", "bio": "Casual coffee dates and good conversations", "intent": "casual", "interests": ["coffee", "books", "movies"], "is_premium": True}
    ]
    
    profile_photos = [
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400"
    ]
    
    users = []
    for i, u in enumerate(users_data):
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": u['email'],
            "password_hash": hash_password("password123"),
            "first_name": u['first_name'],
            "is_premium": u.get('is_premium', False),
            "applications_today": 0,
            "last_application_date": None,
            "created_at": now.isoformat()
        }
        users.append(user)
        await db.users.insert_one(user)
        
        profile = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "first_name": u['first_name'],
            "age": u['age'],
            "gender": u['gender'],
            "preferred_genders": ["male", "female"],
            "city": u['city'],
            "bio": u['bio'],
            "profile_photo": profile_photos[i],
            "extra_photos": [],
            "job_title": None,
            "interests": u['interests'],
            "intent": u['intent'],
            "safety_preferences": None,
            "created_at": now.isoformat()
        }
        await db.profiles.insert_one(profile)
    
    # Sample date posts
    date_posts_data = [
        {"poster_idx": 0, "title": "Coffee and a Walk at Lady Bird Lake", "description": "Let's grab some coffee from Jo's and enjoy a relaxing walk along the lake trail. Perfect for a Saturday morning!", "city": "Austin", "place_name": "Lady Bird Lake Trail", "tags": ["coffee", "outdoors", "walking"], "who_pays": "split"},
        {"poster_idx": 1, "title": "Fine Dining at Uchi", "description": "I have reservations at Uchi for an omakase experience. Looking for someone who appreciates great sushi!", "city": "Austin", "place_name": "Uchi Restaurant", "tags": ["dinner", "sushi", "fine_dining"], "who_pays": "i_pay"},
        {"poster_idx": 2, "title": "Museum of Fine Arts Houston Visit", "description": "The new exhibit just opened and I'd love some company. Art discussions welcome!", "city": "Houston", "place_name": "MFAH", "tags": ["museum", "art", "culture"], "who_pays": "split"},
        {"poster_idx": 3, "title": "Hiking at Big Bend", "description": "Planning a day trip to Big Bend. Looking for an adventurous hiking partner!", "city": "Houston", "place_name": "Big Bend National Park", "tags": ["hiking", "outdoors", "adventure"], "who_pays": "split"},
        {"poster_idx": 4, "title": "Wine Tasting Evening", "description": "Exploring the Hill Country wineries. Who wants to join for some wine tasting?", "city": "Austin", "place_name": "Fredericksburg Wine Trail", "tags": ["wine", "tasting", "outdoors"], "who_pays": "split"},
        {"poster_idx": 5, "title": "Brunch at Paperboy", "description": "Sunday brunch at one of Austin's best spots. Good food and great company!", "city": "Austin", "place_name": "Paperboy", "tags": ["brunch", "coffee", "casual"], "who_pays": "decide_later"},
        {"poster_idx": 6, "title": "Yoga in the Park", "description": "Morning yoga session at Hermann Park followed by smoothies. Beginners welcome!", "city": "Houston", "place_name": "Hermann Park", "tags": ["fitness", "outdoors", "wellness"], "who_pays": "you_pay"},
        {"poster_idx": 7, "title": "Live Music at White Oak", "description": "There's an amazing band playing. Love to share the experience with someone!", "city": "Houston", "place_name": "White Oak Music Hall", "tags": ["music", "concert", "nightlife"], "who_pays": "i_pay"},
        {"poster_idx": 8, "title": "Photo Walk Downtown", "description": "Golden hour photography walk through downtown Austin. Bring your camera!", "city": "Austin", "place_name": "Downtown Austin", "tags": ["photography", "walking", "creative"], "who_pays": "split"},
        {"poster_idx": 9, "title": "Book Club Coffee", "description": "Currently reading 'The Midnight Library'. Let's discuss over coffee!", "city": "Austin", "place_name": "BookPeople Cafe", "tags": ["coffee", "books", "casual"], "who_pays": "split"},
        {"poster_idx": 0, "title": "Sunset Kayaking", "description": "Kayaking on Lady Bird Lake at sunset. Gear rental included!", "city": "Austin", "place_name": "Rowing Dock", "tags": ["outdoors", "water", "adventure"], "who_pays": "i_pay"},
        {"poster_idx": 1, "title": "Cooking Class Together", "description": "Italian cooking class at Sur La Table. Let's learn to make fresh pasta!", "city": "Austin", "place_name": "Sur La Table", "tags": ["cooking", "food", "creative"], "who_pays": "split"},
        {"poster_idx": 2, "title": "Space Center Houston", "description": "Always wanted to visit the Space Center. Science nerds unite!", "city": "Houston", "place_name": "Space Center Houston", "tags": ["museum", "science", "adventure"], "who_pays": "split"},
        {"poster_idx": 3, "title": "BBQ Tour", "description": "Let's hit the best BBQ spots in Houston. Bring your appetite!", "city": "Houston", "place_name": "Various BBQ Joints", "tags": ["food", "bbq", "adventure"], "who_pays": "split"},
        {"poster_idx": 4, "title": "Comedy Night", "description": "Stand-up comedy at Cap City. Laughter is the best date activity!", "city": "Austin", "place_name": "Cap City Comedy Club", "tags": ["comedy", "nightlife", "entertainment"], "who_pays": "i_pay"},
        {"poster_idx": 5, "title": "Farmers Market Morning", "description": "Exploring the farmers market and grabbing fresh breakfast tacos!", "city": "Austin", "place_name": "Hope Farmers Market", "tags": ["food", "outdoors", "morning"], "who_pays": "decide_later"},
        {"poster_idx": 6, "title": "Art Class Date", "description": "Paint and sip evening. No experience needed, just enthusiasm!", "city": "Houston", "place_name": "Pinot's Palette", "tags": ["art", "creative", "casual"], "who_pays": "split"},
        {"poster_idx": 7, "title": "Jazz Night", "description": "Live jazz at The Continental Club. Great vibes guaranteed!", "city": "Houston", "place_name": "The Continental Club", "tags": ["music", "jazz", "nightlife"], "who_pays": "split"},
        {"poster_idx": 8, "title": "Botanical Garden Stroll", "description": "Peaceful walk through the botanical gardens. Perfect for good conversation!", "city": "Austin", "place_name": "Zilker Botanical Garden", "tags": ["outdoors", "nature", "walking"], "who_pays": "split"},
        {"poster_idx": 9, "title": "Escape Room Challenge", "description": "Think we can escape in 60 minutes? Let's find out!", "city": "Austin", "place_name": "The Escape Game", "tags": ["games", "adventure", "fun"], "who_pays": "split"}
    ]
    
    date_images = [
        "https://images.unsplash.com/photo-1734989591520-eb44771b9077?w=800",
        "https://images.unsplash.com/photo-1663437555931-d385ee04b8d1?w=800",
        "https://images.unsplash.com/photo-1696238378039-821fc376ebd4?w=800",
        "https://images.unsplash.com/photo-1628531832865-989e137150ce?w=800",
        "https://images.unsplash.com/photo-1650313525165-40c8132c0ae0?w=800"
    ]
    
    posts = []
    for i, p in enumerate(date_posts_data):
        post_id = str(uuid.uuid4())
        poster = users[p['poster_idx']]
        date_time = (now + timedelta(days=i % 14 + 1, hours=10 + (i % 8))).isoformat()
        
        post = {
            "id": post_id,
            "poster_id": poster['id'],
            "poster_name": poster['first_name'],
            "poster_photo": profile_photos[p['poster_idx']],
            "title": p['title'],
            "description": p['description'],
            "city": p['city'],
            "place_name": p['place_name'],
            "map_link": None,
            "date_time": date_time,
            "duration": "2-3 hours",
            "who_pays": p['who_pays'],
            "tags": p['tags'],
            "preferred_genders": None,
            "age_range_min": 21,
            "age_range_max": 45,
            "max_applicants": 10,
            "application_deadline": None,
            "status": "OPEN",
            "like_count": (i * 3) % 15,
            "application_count": 0,
            "image_url": date_images[i % len(date_images)],
            "created_at": now.isoformat()
        }
        posts.append(post)
        await db.date_posts.insert_one(post)
    
    # Add some applications
    applications_data = [
        {"post_idx": 0, "applicant_idx": 1, "message": "I love Lady Bird Lake! Would be great to explore it together."},
        {"post_idx": 0, "applicant_idx": 5, "message": "Coffee walks are my favorite. Count me in!"},
        {"post_idx": 1, "applicant_idx": 4, "message": "Uchi is on my bucket list! Would love to join."},
        {"post_idx": 2, "applicant_idx": 3, "message": "Art enthusiast here. The new exhibit looks amazing!"},
        {"post_idx": 3, "applicant_idx": 6, "message": "Hiking is my passion. Big Bend sounds perfect!"},
        {"post_idx": 4, "applicant_idx": 1, "message": "Wine tasting in Hill Country? Yes please!"},
    ]
    
    for app in applications_data:
        post = posts[app['post_idx']]
        applicant = users[app['applicant_idx']]
        
        application = {
            "id": str(uuid.uuid4()),
            "date_post_id": post['id'],
            "applicant_id": applicant['id'],
            "applicant_name": applicant['first_name'],
            "applicant_age": users_data[app['applicant_idx']]['age'],
            "applicant_city": users_data[app['applicant_idx']]['city'],
            "applicant_photo": profile_photos[app['applicant_idx']],
            "applicant_bio": users_data[app['applicant_idx']]['bio'],
            "applicant_extra_photos": [],
            "applicant_job_title": None,
            "applicant_interests": users_data[app['applicant_idx']]['interests'],
            "applicant_intent": users_data[app['applicant_idx']]['intent'],
            "message": app['message'],
            "quick_answers": None,
            "status": "pending",
            "created_at": now.isoformat()
        }
        await db.applications.insert_one(application)
        await db.date_posts.update_one({"id": post['id']}, {"$inc": {"application_count": 1}})
    
    # Create 2 matched chats
    # Match 1: Emma accepted James for Coffee Walk
    match1_thread = {
        "id": str(uuid.uuid4()),
        "date_post_id": posts[0]['id'],
        "date_post_title": posts[0]['title'],
        "user1_id": users[0]['id'],
        "user2_id": users[1]['id'],
        "user1_name": users[0]['first_name'],
        "user2_name": users[1]['first_name'],
        "user1_photo": profile_photos[0],
        "user2_photo": profile_photos[1],
        "last_message": "See you Saturday!",
        "last_message_at": now.isoformat(),
        "unread_count_user1": 0,
        "unread_count_user2": 1,
        "confirmed_time": (now + timedelta(days=3)).isoformat(),
        "confirmed_location": "Jo's Coffee",
        "confirmed_who_pays": "split",
        "is_confirmed": True,
        "created_at": now.isoformat()
    }
    await db.chat_threads.insert_one(match1_thread)
    
    # Add some messages to match 1
    messages1 = [
        {"sender_idx": 0, "content": "Hey James! Excited for our coffee walk!"},
        {"sender_idx": 1, "content": "Me too! Jo's Coffee at 10am works for you?"},
        {"sender_idx": 0, "content": "Perfect! I'll meet you there."},
        {"sender_idx": 1, "content": "See you Saturday!"}
    ]
    for msg in messages1:
        sender = users[msg['sender_idx']]
        message = {
            "id": str(uuid.uuid4()),
            "thread_id": match1_thread['id'],
            "sender_id": sender['id'],
            "sender_name": sender['first_name'],
            "content": msg['content'],
            "is_read": True,
            "created_at": now.isoformat()
        }
        await db.chat_messages.insert_one(message)
    
    # Match 2: Sofia accepted Michael for Museum
    match2_thread = {
        "id": str(uuid.uuid4()),
        "date_post_id": posts[2]['id'],
        "date_post_title": posts[2]['title'],
        "user1_id": users[2]['id'],
        "user2_id": users[3]['id'],
        "user1_name": users[2]['first_name'],
        "user2_name": users[3]['first_name'],
        "user1_photo": profile_photos[2],
        "user2_photo": profile_photos[3],
        "last_message": "Can't wait to see the new impressionist collection!",
        "last_message_at": now.isoformat(),
        "unread_count_user1": 1,
        "unread_count_user2": 0,
        "confirmed_time": None,
        "confirmed_location": None,
        "confirmed_who_pays": None,
        "is_confirmed": False,
        "created_at": now.isoformat()
    }
    await db.chat_threads.insert_one(match2_thread)
    
    messages2 = [
        {"sender_idx": 2, "content": "Hi Michael! Thanks for applying!"},
        {"sender_idx": 3, "content": "The exhibit looks incredible. When were you thinking?"},
        {"sender_idx": 2, "content": "How about next Sunday afternoon?"},
        {"sender_idx": 3, "content": "Can't wait to see the new impressionist collection!"}
    ]
    for msg in messages2:
        sender = users[msg['sender_idx']]
        message = {
            "id": str(uuid.uuid4()),
            "thread_id": match2_thread['id'],
            "sender_id": sender['id'],
            "sender_name": sender['first_name'],
            "content": msg['content'],
            "is_read": True,
            "created_at": now.isoformat()
        }
        await db.chat_messages.insert_one(message)
    
    return {"message": "Database seeded successfully", "users": 10, "date_posts": 20, "chat_threads": 2}

# ==================== HEALTH CHECK ====================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router
app.include_router(api_router)

# CORS middleware
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
