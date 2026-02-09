from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import socketio
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict, validator
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timezone, timedelta, date
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
import re
import secrets
import hashlib
from math import radians, sin, cos, sqrt, atan2
from better_profanity import profanity
import aiofiles
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import services
from services import sms_service, email_service, file_storage
from websocket_handler import sio, broadcast_new_message, broadcast_date_plan_update, broadcast_match, send_notification

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'datefirst-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

# Rate limiting settings
RATE_LIMITS = {
    "likes_per_minute": 10,
    "likes_per_day": 100,
    "messages_per_minute": 20,
    "messages_to_new_matches_per_day": 50,
    "reports_per_minute": 3,
    "profile_edits_per_hour": 10
}

# Upload settings
UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/uploads'))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(title="DateFirst API v3 - Safety Enhanced")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

api_router = APIRouter(prefix="/api")
security = HTTPBearer()
ph = PasswordHasher()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize profanity filter
profanity.load_censor_words()

# ==================== CITY GEOCODING ====================
CITY_COORDINATES = {
    # United States
    "new york city": {"lat": 40.7128, "lng": -74.0060, "country": "US"},
    "new york": {"lat": 40.7128, "lng": -74.0060, "country": "US"},
    "nyc": {"lat": 40.7128, "lng": -74.0060, "country": "US"},
    "los angeles": {"lat": 34.0522, "lng": -118.2437, "country": "US"},
    "la": {"lat": 34.0522, "lng": -118.2437, "country": "US"},
    "san francisco": {"lat": 37.7749, "lng": -122.4194, "country": "US"},
    "sf": {"lat": 37.7749, "lng": -122.4194, "country": "US"},
    "chicago": {"lat": 41.8781, "lng": -87.6298, "country": "US"},
    "boston": {"lat": 42.3601, "lng": -71.0589, "country": "US"},
    "washington dc": {"lat": 38.9072, "lng": -77.0369, "country": "US"},
    "dc": {"lat": 38.9072, "lng": -77.0369, "country": "US"},
    "seattle": {"lat": 47.6062, "lng": -122.3321, "country": "US"},
    "austin": {"lat": 30.2672, "lng": -97.7431, "country": "US"},
    "miami": {"lat": 25.7617, "lng": -80.1918, "country": "US"},
    "houston": {"lat": 29.7604, "lng": -95.3698, "country": "US"},
    "dallas": {"lat": 32.7767, "lng": -96.7970, "country": "US"},
    "atlanta": {"lat": 33.7490, "lng": -84.3880, "country": "US"},
    "denver": {"lat": 39.7392, "lng": -104.9903, "country": "US"},
    "san diego": {"lat": 32.7157, "lng": -117.1611, "country": "US"},
    "philadelphia": {"lat": 39.9526, "lng": -75.1652, "country": "US"},
    # India
    "mumbai": {"lat": 19.0760, "lng": 72.8777, "country": "IN"},
    "delhi": {"lat": 28.6139, "lng": 77.2090, "country": "IN"},
    "new delhi": {"lat": 28.6139, "lng": 77.2090, "country": "IN"},
    "bengaluru": {"lat": 12.9716, "lng": 77.5946, "country": "IN"},
    "bangalore": {"lat": 12.9716, "lng": 77.5946, "country": "IN"},
    "hyderabad": {"lat": 17.3850, "lng": 78.4867, "country": "IN"},
    "chennai": {"lat": 13.0827, "lng": 80.2707, "country": "IN"},
    "kolkata": {"lat": 22.5726, "lng": 88.3639, "country": "IN"},
    "pune": {"lat": 18.5204, "lng": 73.8567, "country": "IN"},
    "ahmedabad": {"lat": 23.0225, "lng": 72.5714, "country": "IN"},
    "jaipur": {"lat": 26.9124, "lng": 75.7873, "country": "IN"},
    "goa": {"lat": 15.2993, "lng": 74.1240, "country": "IN"},
    "kochi": {"lat": 9.9312, "lng": 76.2673, "country": "IN"},
    "chandigarh": {"lat": 30.7333, "lng": 76.7794, "country": "IN"},
}

def get_city_coords(city_name: str) -> Optional[Dict]:
    """Get coordinates for a city from our internal mapping"""
    if not city_name:
        return None
    normalized = city_name.lower().strip()
    return CITY_COORDINATES.get(normalized)

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in miles"""
    R = 3959  # Earth's radius in miles
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ==================== CONTENT SAFETY ====================
CONTACT_PATTERNS = [
    r'\b\d{10}\b',  # Phone numbers
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone with separators
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b(instagram|ig|insta|snap|snapchat|whatsapp|telegram|signal|discord)\s*[@:]\s*\w+',
    r'@\w{3,}',  # Social handles
]

SAFETY_KEYWORDS = [
    'hurt', 'kill', 'threat', 'force', 'must', 'have to', 'or else',
    'dont tell', "don't tell", 'secret', 'nobody knows', 'alone',
]

def contains_contact_info(text: str) -> bool:
    """Check if text contains phone/email/social handles"""
    if not text:
        return False
    for pattern in CONTACT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def contains_safety_concern(text: str) -> bool:
    """Check for concerning language patterns"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in SAFETY_KEYWORDS)

def check_profanity(text: str) -> Dict[str, Any]:
    """Check text for profanity and return result"""
    if not text:
        return {"has_profanity": False, "censored": text}
    has_profanity = profanity.contains_profanity(text)
    censored = profanity.censor(text) if has_profanity else text
    return {"has_profanity": has_profanity, "censored": censored}

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class EmailVerification(BaseModel):
    code: str

class FirstDateIdea(BaseModel):
    title: str
    description: str
    tags: List[str] = []
    city: str
    is_public_meetup: bool = True
    suggested_meetup: Optional[str] = None

class ProfileSetup(BaseModel):
    first_name: str
    main_photo: str
    city: str
    distance_preference: int = 50
    date_of_birth: str  # ISO date string YYYY-MM-DD
    gender: str
    interested_in: List[str]
    height: Optional[str] = None
    bio: Optional[str] = None
    date_preferences: List[str] = []
    first_date_idea: FirstDateIdea
    precise_location: Optional[bool] = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        try:
            dob = datetime.strptime(v, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise ValueError('You must be 18 or older to use DateFirst')
            return v
        except ValueError as e:
            if 'must be 18' in str(e):
                raise e
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

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
    who_pays: Optional[str] = None
    is_confirmed: Optional[bool] = None

class TrustedContactCreate(BaseModel):
    name: str
    email: EmailStr

class SafetyCheckInCreate(BaseModel):
    thread_id: str
    scheduled_time: str  # ISO datetime
    grace_minutes: int = 30

class ReportCreate(BaseModel):
    reported_user_id: str
    reason: str  # harassment, spam, impersonation, underage, violence, nudity, scam, hate, other
    details: Optional[str] = None
    include_messages: bool = False

class BlockCreate(BaseModel):
    blocked_user_id: str

class PhotoVerificationSubmit(BaseModel):
    gesture_type: str = "peace_sign"  # peace_sign, thumbs_up, wave

class PhoneVerificationStart(BaseModel):
    phone_number: str

class PhoneVerificationVerify(BaseModel):
    code: str

class AdminUserAction(BaseModel):
    action: str  # warn, restrict_messaging, shadow_ban, suspend, unsuspend
    reason: str

class AdminVerificationAction(BaseModel):
    status: str  # APPROVED, REJECTED
    notes: Optional[str] = None

# NEW: Pass/Dislike model
class PassCreate(BaseModel):
    passed_user_id: str

# NEW: Date Feedback model
class DateFeedbackCreate(BaseModel):
    thread_id: str
    overall_rating: int = Field(..., ge=1, le=5)  # 1-5 stars
    safety_rating: int = Field(..., ge=1, le=5)  # How safe did you feel?
    accuracy_rating: int = Field(..., ge=1, le=5)  # Did the date match the idea?
    would_recommend: bool = True
    feedback_text: Optional[str] = None
    tags: List[str] = []  # "great_conversation", "felt_safe", "punctual", "respectful", etc.

# NEW: File upload response
class FileUploadResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, password)
        return True
    except VerifyMismatchError:
        return False

def create_token(user_id: str, session_id: str = None) -> str:
    payload = {
        'user_id': user_id,
        'session_id': session_id or str(uuid.uuid4()),
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        return None

def generate_verification_code() -> str:
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if session is valid
    session_id = payload.get('session_id')
    if session_id:
        session = await db.sessions.find_one({"id": session_id, "user_id": user['id'], "is_active": True})
        if not session:
            raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    
    # Check if user is suspended
    if user.get('status') == 'suspended':
        raise HTTPException(status_code=403, detail="Your account has been suspended")
    
    return user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ==================== RATE LIMITING ====================

async def check_rate_limit(user_id: str, action: str, limit: int, window_seconds: int) -> bool:
    """Check if user has exceeded rate limit. Returns True if allowed."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=window_seconds)
    
    count = await db.rate_limit_events.count_documents({
        "user_id": user_id,
        "action": action,
        "timestamp": {"$gte": window_start.isoformat()}
    })
    
    if count >= limit:
        return False
    
    # Log this event
    await db.rate_limit_events.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "timestamp": now.isoformat()
    })
    return True

async def check_shadow_ban(user_id: str) -> bool:
    """Check if user is shadow banned"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user.get('shadow_banned', False)

# ==================== VERIFICATION HELPERS ====================

def get_verification_badges(user: dict) -> List[Dict]:
    """Get list of verification badges for display"""
    badges = []
    if user.get('email_verified'):
        badges.append({"type": "email", "label": "Email Verified", "icon": "mail-check"})
    if user.get('photo_verified'):
        badges.append({"type": "photo", "label": "Photo Verified", "icon": "camera-check"})
    if user.get('phone_verified'):
        badges.append({"type": "phone", "label": "Phone Verified", "icon": "phone-check"})
    if user.get('id_verified'):
        badges.append({"type": "id", "label": "ID Verified", "icon": "shield-check"})
    return badges

# ==================== PRIVACY HELPERS ====================

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

async def get_passed_user_ids(user_id: str) -> List[str]:
    """Get list of user IDs that the user has passed/disliked"""
    passes = await db.passes.find({"passer_id": user_id}, {"_id": 0, "passed_id": 1}).to_list(10000)
    return [p['passed_id'] for p in passes]

async def are_matched(user1_id: str, user2_id: str) -> bool:
    match = await db.matches.find_one({
        "$or": [
            {"user1_id": user1_id, "user2_id": user2_id},
            {"user1_id": user2_id, "user2_id": user1_id}
        ]
    })
    return match is not None

def get_public_profile(profile: dict, user: dict = None) -> dict:
    """Return only pre-match visible fields + verification badges"""
    result = {
        "user_id": profile.get("user_id"),
        "first_name": profile.get("first_name"),
        "main_photo": profile.get("main_photo"),
        "city": profile.get("city"),
        "first_date_idea": profile.get("first_date_idea"),
        "date_preferences": profile.get("date_preferences", []),
        "badges": []
    }
    if user:
        result["badges"] = get_verification_badges(user)
    return result

def get_full_profile(profile: dict, user: dict = None) -> dict:
    """Return full profile for matched users"""
    result = {
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
        "created_at": profile.get("created_at"),
        "badges": []
    }
    if user:
        result["badges"] = get_verification_badges(user)
        result["verification_details"] = {
            "email_verified": user.get('email_verified', False),
            "photo_verified": user.get('photo_verified', False),
            "phone_verified": user.get('phone_verified', False),
        }
    return result

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup")
async def signup(data: UserCreate, request: Request):
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    verification_code = generate_verification_code()
    
    # Fraud signals
    ip_hash = hash_ip(request.client.host) if request.client else None
    user_agent = request.headers.get('user-agent', '')[:500]
    
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "profile_complete": False,
        "email_verified": False,
        "email_verification_code": verification_code,
        "email_verification_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "photo_verified": False,
        "phone_verified": False,
        "id_verified": False,
        "status": "active",  # active, limited, suspended
        "shadow_banned": False,
        "is_admin": False,
        "ip_hash": ip_hash,
        "user_agent": user_agent,
        "report_count_24h": 0,
        "last_report_reset": now,
        "created_at": now
    }
    
    await db.users.insert_one(user)
    
    # Create session
    session = {
        "id": session_id,
        "user_id": user_id,
        "ip_hash": ip_hash,
        "user_agent": user_agent,
        "is_active": True,
        "created_at": now
    }
    await db.sessions.insert_one(session)
    
    token = create_token(user_id, session_id)
    
    # Send verification email
    email_result = await email_service.send_verification_email(data.email, verification_code)
    logger.info(f"Email verification sent to {data.email}: {email_result}")
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "profile_complete": False,
            "email_verified": False
        },
        "message": "Please check your email for verification code",
        "verification_code": verification_code if email_result.get('mock') else None  # Only show in mock mode
    }

@api_router.post("/auth/verify-email")
async def verify_email(data: EmailVerification, current_user: dict = Depends(get_current_user)):
    if current_user.get('email_verified'):
        return {"message": "Email already verified"}
    
    if current_user.get('email_verification_code') != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    expires = current_user.get('email_verification_expires')
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code expired. Request a new one.")
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"email_verified": True}, "$unset": {"email_verification_code": "", "email_verification_expires": ""}}
    )
    
    return {"message": "Email verified successfully"}

@api_router.post("/auth/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user)):
    if current_user.get('email_verified'):
        return {"message": "Email already verified"}
    
    verification_code = generate_verification_code()
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {
            "email_verification_code": verification_code,
            "email_verification_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }}
    )
    
    # Send verification email
    email_result = await email_service.send_verification_email(current_user['email'], verification_code)
    logger.info(f"Resent verification to {current_user['email']}: {email_result}")
    
    return {
        "message": "Verification code sent to your email",
        "verification_code": verification_code if email_result.get('mock') else None
    }

@api_router.post("/auth/login")
async def login(data: UserLogin, request: Request):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user or not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user.get('status') == 'suspended':
        raise HTTPException(status_code=403, detail="Your account has been suspended")
    
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    ip_hash = hash_ip(request.client.host) if request.client else None
    user_agent = request.headers.get('user-agent', '')[:500]
    
    # Create new session
    session = {
        "id": session_id,
        "user_id": user['id'],
        "ip_hash": ip_hash,
        "user_agent": user_agent,
        "is_active": True,
        "created_at": now
    }
    await db.sessions.insert_one(session)
    
    token = create_token(user['id'], session_id)
    profile = await db.profiles.find_one({"user_id": user['id']}, {"_id": 0})
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "profile_complete": user.get('profile_complete', False),
            "email_verified": user.get('email_verified', False),
            "first_name": profile.get('first_name') if profile else None
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    trusted_contacts = await db.trusted_contacts.find({"user_id": current_user['id']}, {"_id": 0}).to_list(10)
    
    return {
        "user": {
            "id": current_user['id'],
            "email": current_user['email'],
            "profile_complete": current_user.get('profile_complete', False),
            "email_verified": current_user.get('email_verified', False),
            "photo_verified": current_user.get('photo_verified', False),
            "phone_verified": current_user.get('phone_verified', False),
            "badges": get_verification_badges(current_user)
        },
        "profile": get_full_profile(profile, current_user) if profile else None,
        "trusted_contacts": trusted_contacts
    }

@api_router.get("/auth/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    sessions = await db.sessions.find(
        {"user_id": current_user['id'], "is_active": True},
        {"_id": 0, "id": 1, "user_agent": 1, "created_at": 1}
    ).to_list(20)
    return {"sessions": sessions}

@api_router.post("/auth/logout-all")
async def logout_all_devices(current_user: dict = Depends(get_current_user)):
    await db.sessions.update_many(
        {"user_id": current_user['id']},
        {"$set": {"is_active": False}}
    )
    return {"message": "Logged out of all devices"}

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    if payload and payload.get('session_id'):
        await db.sessions.update_one(
            {"id": payload['session_id']},
            {"$set": {"is_active": False}}
        )
    return {"message": "Logged out successfully"}

# ==================== PROFILE ROUTES ====================

@api_router.post("/profile/setup")
async def setup_profile(data: ProfileSetup, current_user: dict = Depends(get_current_user)):
    # Check email verification (required before profile)
    if not current_user.get('email_verified'):
        raise HTTPException(status_code=403, detail="Please verify your email before setting up your profile")
    
    # Content safety check
    profanity_check = check_profanity(data.first_date_idea.title + " " + data.first_date_idea.description)
    if profanity_check['has_profanity']:
        raise HTTPException(status_code=400, detail="Your date idea contains inappropriate language. Please revise.")
    
    if data.bio:
        bio_check = check_profanity(data.bio)
        if bio_check['has_profanity']:
            raise HTTPException(status_code=400, detail="Your bio contains inappropriate language. Please revise.")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Handle geolocation
    latitude = data.latitude
    longitude = data.longitude
    if not latitude or not longitude:
        coords = get_city_coords(data.city)
        if coords:
            latitude = coords['lat']
            longitude = coords['lng']
    
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
        "precise_location": data.precise_location,
        "latitude": latitude,
        "longitude": longitude,
        "created_at": now
    }
    
    existing = await db.profiles.find_one({"user_id": current_user['id']})
    if existing:
        await db.profiles.update_one({"user_id": current_user['id']}, {"$set": profile})
    else:
        await db.profiles.insert_one(profile)
    
    await db.users.update_one({"id": current_user['id']}, {"$set": {"profile_complete": True}})
    
    profile.pop('_id', None)
    return {"message": "Profile setup complete", "profile": get_full_profile(profile, current_user)}

@api_router.put("/profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    # Rate limit check
    if not await check_rate_limit(current_user['id'], 'profile_edit', RATE_LIMITS['profile_edits_per_hour'], 3600):
        raise HTTPException(status_code=429, detail="Too many profile edits. Please wait.")
    
    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if k == 'first_date_idea':
                # Content safety check
                profanity_check = check_profanity(v.get('title', '') + " " + v.get('description', ''))
                if profanity_check['has_profanity']:
                    raise HTTPException(status_code=400, detail="Your date idea contains inappropriate language")
                update_data[k] = v
            elif k == 'bio':
                bio_check = check_profanity(v)
                if bio_check['has_profanity']:
                    raise HTTPException(status_code=400, detail="Your bio contains inappropriate language")
                update_data[k] = v
            elif k == 'city':
                update_data[k] = v
                # Update coordinates if city changes
                coords = get_city_coords(v)
                if coords:
                    update_data['latitude'] = coords['lat']
                    update_data['longitude'] = coords['lng']
            else:
                update_data[k] = v
    
    if update_data:
        await db.profiles.update_one({"user_id": current_user['id']}, {"$set": update_data})
    
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    return get_full_profile(profile, current_user)

@api_router.get("/profile/{user_id}")
async def get_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    if await check_blocked(current_user['id'], user_id):
        raise HTTPException(status_code=403, detail="User not available")
    
    profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if user_id == current_user['id'] or await are_matched(current_user['id'], user_id):
        return get_full_profile(profile, user)
    else:
        return get_public_profile(profile, user)

# ==================== VERIFICATION ROUTES ====================

@api_router.post("/verification/photo/submit")
async def submit_photo_verification(
    gesture_type: str = Form(...),
    selfie: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Submit photo for verification - selfie with gesture"""
    if current_user.get('photo_verified'):
        raise HTTPException(status_code=400, detail="Already photo verified")
    
    # Check for pending submission
    existing = await db.verification_submissions.find_one({
        "user_id": current_user['id'],
        "type": "photo",
        "status": "PENDING"
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have a pending verification. Please wait for review.")
    
    # Save file
    file_ext = selfie.filename.split('.')[-1] if '.' in selfie.filename else 'jpg'
    filename = f"verification_{current_user['id']}_{uuid.uuid4()}.{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await selfie.read()
        await f.write(content)
    
    now = datetime.now(timezone.utc).isoformat()
    submission = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "type": "photo",
        "gesture_type": gesture_type,
        "media_url": f"/uploads/{filename}",
        "status": "PENDING",  # PENDING, APPROVED, REJECTED
        "admin_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": now
    }
    await db.verification_submissions.insert_one(submission)
    
    return {"message": "Photo verification submitted. You'll be notified once reviewed.", "submission_id": submission['id']}

@api_router.get("/verification/photo/status")
async def get_photo_verification_status(current_user: dict = Depends(get_current_user)):
    submission = await db.verification_submissions.find_one(
        {"user_id": current_user['id'], "type": "photo"},
        {"_id": 0}
    )
    return {
        "verified": current_user.get('photo_verified', False),
        "submission": submission
    }

@api_router.post("/verification/phone/start")
async def start_phone_verification(data: PhoneVerificationStart, current_user: dict = Depends(get_current_user)):
    """Start phone verification - sends OTP via SMS"""
    if current_user.get('phone_verified'):
        raise HTTPException(status_code=400, detail="Phone already verified")
    
    # Generate OTP
    otp = generate_verification_code()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {
            "phone_number": data.phone_number,
            "phone_otp": otp,
            "phone_otp_expires": expires
        }}
    )
    
    # Send OTP via SMS service
    sms_result = await sms_service.send_otp(data.phone_number, otp)
    logger.info(f"Phone OTP sent to {data.phone_number}: {sms_result}")
    
    return {
        "message": f"OTP sent to {data.phone_number}",
        "otp": otp if sms_result.get('mock') else None  # Only show in mock mode
    }

@api_router.post("/verification/phone/verify")
async def verify_phone(data: PhoneVerificationVerify, current_user: dict = Depends(get_current_user)):
    if current_user.get('phone_verified'):
        raise HTTPException(status_code=400, detail="Phone already verified")
    
    user = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    if user.get('phone_otp') != data.code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    expires = user.get('phone_otp_expires')
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"phone_verified": True}, "$unset": {"phone_otp": "", "phone_otp_expires": ""}}
    )
    
    return {"message": "Phone verified successfully"}

# ==================== DISCOVER ROUTES ====================

@api_router.get("/discover")
async def discover_profiles(
    interested_in: Optional[str] = None,
    max_distance: Optional[int] = None,
    tags: Optional[str] = None,
    sort_by: Optional[str] = "recommended",
    verified_only: bool = False,
    public_meetup_only: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get discovery feed - requires email verification"""
    if not current_user.get('email_verified'):
        raise HTTPException(status_code=403, detail="Please verify your email to browse")
    
    my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    if not my_profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")
    
    blocked_ids = await get_blocked_user_ids(current_user['id'])
    passed_ids = await get_passed_user_ids(current_user['id'])  # NEW: Get passed/disliked users
    my_likes = await db.likes.find({"liker_id": current_user['id']}, {"_id": 0}).to_list(1000)
    liked_ids = [like['liked_id'] for like in my_likes]
    
    my_matches = await db.matches.find({
        "$or": [{"user1_id": current_user['id']}, {"user2_id": current_user['id']}]
    }, {"_id": 0}).to_list(1000)
    matched_ids = []
    for m in my_matches:
        matched_ids.append(m['user1_id'] if m['user2_id'] == current_user['id'] else m['user2_id'])
    
    # Exclude blocked, passed, liked, matched, and self
    exclude_ids = set(blocked_ids + passed_ids + liked_ids + matched_ids + [current_user['id']])
    
    query: Dict[str, Any] = {"user_id": {"$nin": list(exclude_ids)}}
    
    # Filter by gender
    if interested_in:
        genders = interested_in.split(',')
        query['gender'] = {"$in": genders}
    elif my_profile.get('interested_in'):
        query['gender'] = {"$in": my_profile['interested_in']}
    
    # Filter by tags
    if tags:
        tag_list = tags.split(',')
        query['first_date_idea.tags'] = {"$in": tag_list}
    
    # Filter by public meetup
    if public_meetup_only:
        query['first_date_idea.is_public_meetup'] = True
    
    skip = (page - 1) * limit
    
    profiles = await db.profiles.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit * 2).to_list(limit * 2)
    
    # Post-filter for distance and verification
    filtered_profiles = []
    my_lat = my_profile.get('latitude')
    my_lng = my_profile.get('longitude')
    distance_limit = max_distance or my_profile.get('distance_preference', 100)
    
    for p in profiles:
        user = await db.users.find_one({"id": p['user_id']}, {"_id": 0})
        if not user:
            continue
        
        # Skip shadow-banned users
        if user.get('shadow_banned'):
            continue
        
        # Skip suspended users
        if user.get('status') == 'suspended':
            continue
        
        # Verified only filter
        if verified_only and not user.get('photo_verified'):
            continue
        
        # Distance filter
        if my_lat and my_lng and p.get('latitude') and p.get('longitude'):
            distance = haversine_distance(my_lat, my_lng, p['latitude'], p['longitude'])
            if distance > distance_limit:
                continue
        
        public_profile = get_public_profile(p, user)
        filtered_profiles.append(public_profile)
        
        if len(filtered_profiles) >= limit:
            break
    
    total = len(filtered_profiles)
    
    return {
        "invites": filtered_profiles,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }

# ==================== LIKE / MATCH ROUTES ====================

@api_router.post("/like/{user_id}")
async def like_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot like yourself")
    
    # Rate limit check
    if not await check_rate_limit(current_user['id'], 'like', RATE_LIMITS['likes_per_minute'], 60):
        raise HTTPException(status_code=429, detail="Too many likes. Slow down!")
    
    # Daily limit check
    if not await check_rate_limit(current_user['id'], 'like_daily', RATE_LIMITS['likes_per_day'], 86400):
        raise HTTPException(status_code=429, detail="Daily like limit reached. Come back tomorrow!")
    
    # Shadow ban check - likes don't create matches
    is_shadow_banned = await check_shadow_ban(current_user['id'])
    
    if await check_blocked(current_user['id'], user_id):
        raise HTTPException(status_code=403, detail="User not available")
    
    existing_like = await db.likes.find_one({
        "liker_id": current_user['id'],
        "liked_id": user_id
    })
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked")
    
    now = datetime.now(timezone.utc).isoformat()
    
    like = {
        "id": str(uuid.uuid4()),
        "liker_id": current_user['id'],
        "liked_id": user_id,
        "created_at": now
    }
    await db.likes.insert_one(like)
    
    # If shadow banned, don't check for mutual match
    if is_shadow_banned:
        return {"message": "Like sent", "is_match": False, "match_id": None}
    
    # Check for mutual like
    mutual_like = await db.likes.find_one({
        "liker_id": user_id,
        "liked_id": current_user['id']
    })
    
    is_match = False
    match_id = None
    
    if mutual_like:
        is_match = True
        match_id = str(uuid.uuid4())
        
        match = {
            "id": match_id,
            "user1_id": current_user['id'],
            "user2_id": user_id,
            "created_at": now
        }
        await db.matches.insert_one(match)
        
        my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        their_profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
        
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
            "message_count": 0,
            "contact_sharing_allowed": False,
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
    result = await db.likes.delete_one({
        "liker_id": current_user['id'],
        "liked_id": user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Like not found")
    return {"message": "Like removed"}

@api_router.get("/vibes")
async def get_vibes(current_user: dict = Depends(get_current_user)):
    likes_on_me = await db.likes.find({"liked_id": current_user['id']}, {"_id": 0}).to_list(1000)
    liker_ids = [like['liker_id'] for like in likes_on_me]
    
    my_likes = await db.likes.find({"liker_id": current_user['id']}, {"_id": 0}).to_list(1000)
    my_liked_ids = set([like['liked_id'] for like in my_likes])
    
    pending_liker_ids = [lid for lid in liker_ids if lid not in my_liked_ids]
    
    blocked_ids = await get_blocked_user_ids(current_user['id'])
    pending_liker_ids = [lid for lid in pending_liker_ids if lid not in blocked_ids]
    
    profiles = []
    for uid in pending_liker_ids:
        user = await db.users.find_one({"id": uid}, {"_id": 0})
        if not user or user.get('shadow_banned') or user.get('status') == 'suspended':
            continue
        profile = await db.profiles.find_one({"user_id": uid}, {"_id": 0})
        if profile:
            profiles.append(get_public_profile(profile, user))
    
    return {"vibes": profiles, "count": len(profiles)}

@api_router.get("/plans")
async def get_plans(current_user: dict = Depends(get_current_user)):
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
        
        other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
        
        result.append({
            "thread_id": thread['id'],
            "match_id": thread.get('match_id'),
            "other_user_id": other_user_id,
            "other_user_name": other_user_name,
            "other_user_photo": other_user_photo,
            "other_user_badges": get_verification_badges(other_user) if other_user else [],
            "matched_on_idea": thread.get('matched_on_idea'),
            "date_plan": thread.get('date_plan'),
            "last_message": thread.get('last_message'),
            "last_message_at": thread.get('last_message_at'),
            "created_at": thread['created_at']
        })
    
    return {"plans": result}

# ==================== PASS / DISLIKE ROUTES ====================

@api_router.post("/pass/{user_id}")
async def pass_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Pass/Dislike a user - they won't appear in discover again"""
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot pass yourself")
    
    existing = await db.passes.find_one({
        "passer_id": current_user['id'],
        "passed_id": user_id
    })
    if existing:
        return {"message": "Already passed", "already_passed": True}
    
    now = datetime.now(timezone.utc).isoformat()
    
    pass_record = {
        "id": str(uuid.uuid4()),
        "passer_id": current_user['id'],
        "passed_id": user_id,
        "created_at": now
    }
    await db.passes.insert_one(pass_record)
    
    return {"message": "Profile passed", "passed": True}

@api_router.delete("/pass/{user_id}")
async def undo_pass(user_id: str, current_user: dict = Depends(get_current_user)):
    """Undo a pass - user will appear in discover again"""
    result = await db.passes.delete_one({
        "passer_id": current_user['id'],
        "passed_id": user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass removed"}

@api_router.get("/passed")
async def get_passed_users(current_user: dict = Depends(get_current_user)):
    """Get list of passed/disliked users"""
    passes = await db.passes.find({"passer_id": current_user['id']}, {"_id": 0}).to_list(500)
    passed_list = []
    for p in passes:
        profile = await db.profiles.find_one({"user_id": p['passed_id']}, {"_id": 0, "first_name": 1, "main_photo": 1})
        if profile:
            passed_list.append({
                "user_id": p['passed_id'],
                "first_name": profile.get('first_name'),
                "main_photo": profile.get('main_photo'),
                "passed_at": p['created_at']
            })
    return {"passed": passed_list, "count": len(passed_list)}

# ==================== DATE FEEDBACK ROUTES ====================

@api_router.post("/feedback")
async def submit_date_feedback(data: DateFeedbackCreate, current_user: dict = Depends(get_current_user)):
    """Submit feedback after a date"""
    thread = await db.chat_threads.find_one({"id": data.thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if date was confirmed
    if not thread.get('date_plan', {}).get('is_confirmed'):
        raise HTTPException(status_code=400, detail="Cannot leave feedback - date not confirmed")
    
    # Check for existing feedback
    existing = await db.date_feedback.find_one({
        "thread_id": data.thread_id,
        "reviewer_id": current_user['id']
    })
    if existing:
        raise HTTPException(status_code=400, detail="You've already submitted feedback for this date")
    
    other_user_id = thread['user2_id'] if thread['user1_id'] == current_user['id'] else thread['user1_id']
    now = datetime.now(timezone.utc).isoformat()
    
    feedback = {
        "id": str(uuid.uuid4()),
        "thread_id": data.thread_id,
        "reviewer_id": current_user['id'],
        "reviewed_user_id": other_user_id,
        "overall_rating": data.overall_rating,
        "safety_rating": data.safety_rating,
        "accuracy_rating": data.accuracy_rating,
        "would_recommend": data.would_recommend,
        "feedback_text": data.feedback_text,
        "tags": data.tags,
        "created_at": now
    }
    await db.date_feedback.insert_one(feedback)
    
    # Update user's average ratings (stored for internal use, not displayed)
    await update_user_ratings(other_user_id)
    
    return {"message": "Thank you for your feedback!", "feedback_id": feedback['id']}

async def update_user_ratings(user_id: str):
    """Update user's aggregate ratings based on all feedback"""
    feedbacks = await db.date_feedback.find({"reviewed_user_id": user_id}, {"_id": 0}).to_list(1000)
    if not feedbacks:
        return
    
    total = len(feedbacks)
    avg_overall = sum(f['overall_rating'] for f in feedbacks) / total
    avg_safety = sum(f['safety_rating'] for f in feedbacks) / total
    avg_accuracy = sum(f['accuracy_rating'] for f in feedbacks) / total
    recommend_rate = sum(1 for f in feedbacks if f['would_recommend']) / total * 100
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "ratings": {
                "overall": round(avg_overall, 2),
                "safety": round(avg_safety, 2),
                "accuracy": round(avg_accuracy, 2),
                "recommend_rate": round(recommend_rate, 1),
                "count": total
            }
        }}
    )

@api_router.get("/feedback/thread/{thread_id}")
async def get_thread_feedback(thread_id: str, current_user: dict = Depends(get_current_user)):
    """Check if feedback has been submitted for a thread"""
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    my_feedback = await db.date_feedback.find_one({
        "thread_id": thread_id,
        "reviewer_id": current_user['id']
    }, {"_id": 0})
    
    return {
        "has_submitted": my_feedback is not None,
        "feedback": my_feedback,
        "can_submit": thread.get('date_plan', {}).get('is_confirmed', False)
    }

# ==================== FILE UPLOAD ROUTES ====================

@api_router.post("/upload/photo")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a photo (profile or verification)"""
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed")
    
    # Validate file size (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB allowed")
    
    # Upload using file storage service
    result = await file_storage.upload_file(content, file.filename, file.content_type)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', 'Upload failed'))
    
    return {
        "success": True,
        "url": result['url'],
        "filename": result['filename'],
        "size": result['size'],
        "mock": result.get('mock', False)
    }

@api_router.post("/verification/photo/upload")
async def upload_verification_photo(
    gesture_type: str = Form(...),
    selfie: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload photo for verification with proper file storage"""
    if current_user.get('photo_verified'):
        raise HTTPException(status_code=400, detail="Already photo verified")
    
    # Check for pending submission
    existing = await db.verification_submissions.find_one({
        "user_id": current_user['id'],
        "type": "photo",
        "status": "PENDING"
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have a pending verification. Please wait for review.")
    
    # Validate file
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if selfie.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed")
    
    content = await selfie.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB allowed")
    
    # Upload file
    upload_result = await file_storage.upload_file(content, selfie.filename, selfie.content_type)
    if not upload_result['success']:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    now = datetime.now(timezone.utc).isoformat()
    submission = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "type": "photo",
        "gesture_type": gesture_type,
        "media_url": upload_result['url'],
        "status": "PENDING",
        "admin_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": now
    }
    await db.verification_submissions.insert_one(submission)
    
    return {
        "message": "Photo verification submitted. You'll be notified once reviewed.",
        "submission_id": submission['id'],
        "mock": upload_result.get('mock', False)
    }

# ==================== CHAT ROUTES ====================

@api_router.get("/chat/{thread_id}")
async def get_chat_thread(thread_id: str, current_user: dict = Depends(get_current_user)):
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    other_user_id = thread['user2_id'] if thread['user1_id'] == current_user['id'] else thread['user1_id']
    
    if await check_blocked(current_user['id'], other_user_id):
        raise HTTPException(status_code=403, detail="Chat not available")
    
    other_profile = await db.profiles.find_one({"user_id": other_user_id}, {"_id": 0})
    other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0})
    
    # Check for active check-in
    active_checkin = await db.safety_checkins.find_one({
        "thread_id": thread_id,
        "user_id": current_user['id'],
        "status": {"$in": ["scheduled", "pending"]}
    }, {"_id": 0})
    
    return {
        "thread": {
            "id": thread['id'],
            "match_id": thread.get('match_id'),
            "matched_on_idea": thread.get('matched_on_idea'),
            "date_plan": thread.get('date_plan'),
            "message_count": thread.get('message_count', 0),
            "contact_sharing_allowed": thread.get('contact_sharing_allowed', False),
            "created_at": thread['created_at']
        },
        "other_user": get_full_profile(other_profile, other_user) if other_profile else None,
        "active_checkin": active_checkin
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
    # Rate limit check
    if not await check_rate_limit(current_user['id'], 'message', RATE_LIMITS['messages_per_minute'], 60):
        raise HTTPException(status_code=429, detail="Too many messages. Slow down!")
    
    # Check if user is restricted
    user = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    if user.get('status') == 'limited':
        raise HTTPException(status_code=403, detail="Your messaging is temporarily restricted")
    
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    other_user_id = thread['user2_id'] if thread['user1_id'] == current_user['id'] else thread['user1_id']
    if await check_blocked(current_user['id'], other_user_id):
        raise HTTPException(status_code=403, detail="Cannot send message")
    
    # Content safety checks
    message_content = data.content
    
    # Profanity filter (soft block)
    profanity_result = check_profanity(message_content)
    if profanity_result['has_profanity']:
        return {
            "warning": "Your message contains inappropriate language. It has been filtered.",
            "filtered_content": profanity_result['censored'],
            "sent": False
        }
    
    # Contact info blocking (first 20 messages or until confirmed)
    message_count = thread.get('message_count', 0)
    date_confirmed = thread.get('date_plan', {}).get('is_confirmed', False)
    
    if message_count < 20 and not date_confirmed:
        if contains_contact_info(message_content):
            return {
                "warning": "For your safety, sharing contact info is blocked until you've exchanged more messages or confirmed a date plan.",
                "sent": False
            }
    
    # Safety concern detection
    safety_prompt = None
    if contains_safety_concern(message_content):
        safety_prompt = {
            "type": "safety_concern",
            "message": "Need help? Visit the Safety Center for resources and support."
        }
    
    my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    
    message = {
        "id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "sender_id": current_user['id'],
        "sender_name": my_profile.get('first_name', 'User') if my_profile else 'User',
        "content": message_content,
        "created_at": now
    }
    
    await db.chat_messages.insert_one(message)
    message.pop('_id', None)
    
    # Update thread
    await db.chat_threads.update_one(
        {"id": thread_id},
        {"$set": {"last_message": message_content[:100], "last_message_at": now},
         "$inc": {"message_count": 1}}
    )
    
    # Broadcast message via WebSocket
    await broadcast_new_message(thread_id, message, current_user['id'])
    
    response = {"message": message, "sent": True}
    if safety_prompt:
        response["safety_prompt"] = safety_prompt
    
    # Safety nudges when proposing meeting spot
    meeting_keywords = ['meet', 'meetup', 'see you', 'pick you up', 'come over', 'my place', 'your place']
    if any(kw in message_content.lower() for kw in meeting_keywords):
        response["safety_nudges"] = [
            "Consider meeting in a public place for your first date",
            "Share your plans with a trusted friend",
            "Have your own transportation"
        ]
    
    return response

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
    
    # If confirming date, allow contact sharing
    if data.is_confirmed:
        update_data["contact_sharing_allowed"] = True
    
    if update_data:
        await db.chat_threads.update_one({"id": thread_id}, {"$set": update_data})
    
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    
    # Broadcast date plan update via WebSocket
    await broadcast_date_plan_update(thread_id, thread.get('date_plan'), current_user['id'])
    
    # Safe meetup suggestions when date is planned
    suggestions = []
    if thread.get('date_plan', {}).get('proposed_location'):
        suggestions = [
            {"type": "public_place", "text": "Great choice! Public places are recommended for first dates."},
            {"type": "tell_friend", "text": "Consider sharing your date plan with a trusted contact."},
            {"type": "daylight", "text": "Daytime dates can feel more comfortable for first meetings."},
            {"type": "own_ride", "text": "Having your own transportation gives you flexibility."}
        ]
    
    return {
        "date_plan": thread.get('date_plan'),
        "safe_meetup_suggestions": suggestions
    }

# ==================== SAFETY FEATURES ====================

@api_router.get("/safety/trusted-contacts")
async def get_trusted_contacts(current_user: dict = Depends(get_current_user)):
    contacts = await db.trusted_contacts.find(
        {"user_id": current_user['id']}, {"_id": 0}
    ).to_list(10)
    return {"contacts": contacts}

@api_router.post("/safety/trusted-contacts")
async def add_trusted_contact(data: TrustedContactCreate, current_user: dict = Depends(get_current_user)):
    # Limit to 3 contacts
    count = await db.trusted_contacts.count_documents({"user_id": current_user['id']})
    if count >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 trusted contacts allowed")
    
    contact = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "name": data.name,
        "email": data.email,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.trusted_contacts.insert_one(contact)
    contact.pop('_id', None)
    return contact

@api_router.delete("/safety/trusted-contacts/{contact_id}")
async def remove_trusted_contact(contact_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.trusted_contacts.delete_one({
        "id": contact_id,
        "user_id": current_user['id']
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact removed"}

@api_router.post("/safety/checkin")
async def create_safety_checkin(data: SafetyCheckInCreate, current_user: dict = Depends(get_current_user)):
    """Schedule a safety check-in for a date"""
    thread = await db.chat_threads.find_one({"id": data.thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check for existing active check-in
    existing = await db.safety_checkins.find_one({
        "thread_id": data.thread_id,
        "user_id": current_user['id'],
        "status": {"$in": ["scheduled", "pending"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active check-in for this date")
    
    checkin = {
        "id": str(uuid.uuid4()),
        "thread_id": data.thread_id,
        "user_id": current_user['id'],
        "scheduled_time": data.scheduled_time,
        "grace_minutes": data.grace_minutes,
        "status": "scheduled",  # scheduled, pending, confirmed_safe, alert_sent
        "notified_at": None,
        "confirmed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.safety_checkins.insert_one(checkin)
    checkin.pop('_id', None)
    
    return {"message": "Check-in scheduled", "checkin": checkin}

@api_router.post("/safety/checkin/{checkin_id}/confirm")
async def confirm_safety(checkin_id: str, current_user: dict = Depends(get_current_user)):
    """Confirm you're safe during check-in"""
    checkin = await db.safety_checkins.find_one({
        "id": checkin_id,
        "user_id": current_user['id']
    }, {"_id": 0})
    
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")
    
    if checkin['status'] not in ['scheduled', 'pending']:
        raise HTTPException(status_code=400, detail="Check-in already completed")
    
    await db.safety_checkins.update_one(
        {"id": checkin_id},
        {"$set": {
            "status": "confirmed_safe",
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Thank you for confirming. Stay safe!"}

@api_router.delete("/safety/checkin/{checkin_id}")
async def cancel_checkin(checkin_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.safety_checkins.delete_one({
        "id": checkin_id,
        "user_id": current_user['id'],
        "status": "scheduled"
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Check-in not found or already active")
    return {"message": "Check-in cancelled"}

@api_router.post("/safety/share-date-plan/{thread_id}")
async def share_date_plan(thread_id: str, contact_id: str = Query(...), current_user: dict = Depends(get_current_user)):
    """Generate and share date plan summary with trusted contact"""
    thread = await db.chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread['user1_id'] != current_user['id'] and thread['user2_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    contact = await db.trusted_contacts.find_one({
        "id": contact_id,
        "user_id": current_user['id']
    }, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Trusted contact not found")
    
    my_profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    other_name = thread['user2_name'] if thread['user1_id'] == current_user['id'] else thread['user1_name']
    date_plan = thread.get('date_plan', {})
    
    # Send email to trusted contact
    email_result = await email_service.send_date_plan_share(
        to_email=contact['email'],
        contact_name=contact['name'],
        user_name=my_profile.get('first_name', 'User'),
        match_name=other_name,
        date_time=date_plan.get('proposed_datetime', 'Not set'),
        location=date_plan.get('proposed_location', 'Not set')
    )
    logger.info(f"Shared date plan with {contact['email']}: {email_result}")
    
    return {
        "message": f"Date plan shared with {contact['name']}",
        "email_sent": email_result.get('success', False),
        "mock": email_result.get('mock', False)
    }

# ==================== BLOCK & REPORT ====================

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
    
    # Remove likes/matches
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
    # Rate limit
    if not await check_rate_limit(current_user['id'], 'report', RATE_LIMITS['reports_per_minute'], 60):
        raise HTTPException(status_code=429, detail="Too many reports. Please wait.")
    
    # Get message evidence if requested
    evidence_messages = []
    if data.include_messages:
        # Find chat thread
        thread = await db.chat_threads.find_one({
            "$or": [
                {"user1_id": current_user['id'], "user2_id": data.reported_user_id},
                {"user1_id": data.reported_user_id, "user2_id": current_user['id']}
            ]
        }, {"_id": 0})
        
        if thread:
            messages = await db.chat_messages.find(
                {"thread_id": thread['id']},
                {"_id": 0}
            ).sort("created_at", -1).limit(20).to_list(20)
            evidence_messages = messages
    
    report = {
        "id": str(uuid.uuid4()),
        "reporter_id": current_user['id'],
        "reported_user_id": data.reported_user_id,
        "reason": data.reason,
        "details": data.details,
        "evidence_messages": evidence_messages,
        "status": "pending",  # pending, reviewed, action_taken, dismissed
        "admin_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reports.insert_one(report)
    
    # Auto-action: if user receives N reports in 24h, restrict them
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(hours=24)).isoformat()
    report_count = await db.reports.count_documents({
        "reported_user_id": data.reported_user_id,
        "created_at": {"$gte": day_ago}
    })
    
    if report_count >= 3:
        await db.users.update_one(
            {"id": data.reported_user_id},
            {"$set": {"status": "limited"}}
        )
        logger.warning(f"User {data.reported_user_id} auto-restricted due to {report_count} reports")
    
    return {"message": "Report submitted. Thank you for helping keep DateFirst safe."}

# Continue in next part...
# ==================== DATE IDEAS LIBRARY ====================
# This file contains templates and admin routes - to be appended to server.py

DATE_IDEA_TEMPLATES_GLOBAL = [
    # Coffee & Chat
    {"title": "Coffee & Deep Conversation", "description": "Meet at a cozy independent coffee shop. Order your favorite drinks and let the conversation flow naturally.", "tags": ["coffee", "chill", "conversation"], "place_type": "Cafe", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Coffee shop entrance"},
    {"title": "Afternoon Tea Discovery", "description": "Explore a charming tea house together. Sample different teas and share stories.", "tags": ["tea", "chill", "culture"], "place_type": "Cafe", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Tea house entrance"},
    {"title": "Bookstore + Coffee Combo", "description": "Browse an indie bookstore, pick books for each other, then discuss over coffee next door.", "tags": ["books", "coffee", "creative"], "place_type": "Bookstore", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Bookstore entrance"},
    {"title": "Morning Espresso Ritual", "description": "Early birds unite! Meet for espresso and pastries at a local roastery.", "tags": ["coffee", "brunch", "morning"], "place_type": "Cafe", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "30-60m", "suggested_meetup_type": "Cafe entrance"},
    {"title": "Dessert & Coffee Date", "description": "Skip dinner, go straight to dessert. Find a cafe with amazing pastries.", "tags": ["dessert", "coffee", "sweet"], "place_type": "Cafe", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Cafe entrance"},
    
    # Food (Brunch/Dinner/Dessert)
    {"title": "Brunch Adventure", "description": "Nothing says weekend like a leisurely brunch. Let's find the best eggs benny in town.", "tags": ["brunch", "food", "weekend"], "place_type": "Restaurant", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "1-2h", "suggested_meetup_type": "Restaurant entrance"},
    {"title": "Food Truck Discovery", "description": "Hit up a local food truck gathering. Sample different cuisines and find a bench to chat.", "tags": ["food", "casual", "adventure"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Food truck area"},
    {"title": "Ice Cream Walking Date", "description": "Get ice cream and walk around a nice neighborhood. Simple and sweet.", "tags": ["dessert", "walk", "casual"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Ice cream shop"},
    {"title": "Farmers Market Feast", "description": "Wander through a farmers market, sample local treats, and people-watch.", "tags": ["food", "outdoors", "local"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Market entrance"},
    {"title": "Bakery Hop", "description": "Visit 2-3 local bakeries and rate their signature items. May the best croissant win!", "tags": ["food", "adventure", "sweet"], "place_type": "Multiple", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "First bakery entrance"},
    
    # Outdoors
    {"title": "Park Stroll & Chat", "description": "Simple and classic. Meet at a nice park, walk the paths, and enjoy nature together.", "tags": ["outdoors", "walk", "chill"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h", "suggested_meetup_type": "Park main entrance"},
    {"title": "Botanical Garden Visit", "description": "Wander through beautiful gardens, discover rare plants, and take in the peaceful vibes.", "tags": ["outdoors", "nature", "peaceful"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Garden entrance"},
    {"title": "Sunset Viewpoint", "description": "Find a scenic overlook and watch the sunset together. Bring a blanket if you want.", "tags": ["outdoors", "romantic", "scenic"], "place_type": "Viewpoint", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h", "suggested_meetup_type": "Parking area"},
    {"title": "Morning Trail Walk", "description": "Early morning hike on an easy trail. Great way to energize and connect.", "tags": ["outdoors", "active", "morning"], "place_type": "Trail", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h", "suggested_meetup_type": "Trailhead parking"},
    {"title": "Waterfront Walk", "description": "Stroll along the waterfront, watch the boats, maybe grab a snack.", "tags": ["outdoors", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h", "suggested_meetup_type": "Waterfront entrance"},
    {"title": "Picnic in the Park", "description": "Pack some snacks or grab takeout and have a casual picnic. Keep it simple and fun.", "tags": ["outdoors", "food", "relaxed"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Park main entrance"},
    
    # Culture (Museum/Gallery/Bookstore)
    {"title": "Museum Wander", "description": "Explore a local museum together. Share your takes on the exhibits.", "tags": ["museum", "culture", "art"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Museum entrance"},
    {"title": "Art Gallery Hop", "description": "Visit local galleries, discuss the art, pretend you understand abstract expressionism.", "tags": ["art", "culture", "creative"], "place_type": "Gallery", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "2-4h", "suggested_meetup_type": "First gallery entrance"},
    {"title": "Photography Walk", "description": "Bring your camera or phone. Walk around a photogenic area and capture the moment.", "tags": ["creative", "outdoors", "art"], "place_type": "Neighborhood", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h", "suggested_meetup_type": "Starting point landmark"},
    {"title": "Local History Tour", "description": "Discover the history of your city with a self-guided walking tour of historic sites.", "tags": ["history", "walk", "culture"], "place_type": "Historic district", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h", "suggested_meetup_type": "Historic landmark"},
    {"title": "Poetry Reading or Open Mic", "description": "Find a cozy venue with live poetry or open mic. Listen, laugh, maybe perform?", "tags": ["culture", "nightlife", "creative"], "place_type": "Cafe/Bar", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Venue entrance"},
    
    # Activities (Mini-golf/Bowling/Trivia)
    {"title": "Mini Golf Challenge", "description": "Friendly competition at mini golf. Loser buys ice cream!", "tags": ["fun", "active", "games"], "place_type": "Entertainment", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Mini golf entrance"},
    {"title": "Bowling Night", "description": "Classic bowling date. No skills required, just good vibes.", "tags": ["fun", "active", "games"], "place_type": "Entertainment", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Bowling alley entrance"},
    {"title": "Trivia Night Team-Up", "description": "Join a bar trivia night as a team of two. See how our combined knowledge stacks up.", "tags": ["games", "fun", "nightlife"], "place_type": "Bar", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Bar entrance"},
    {"title": "Arcade Adventures", "description": "Hit up an arcade. Play some classics, win some tickets, be kids again.", "tags": ["fun", "games", "nostalgia"], "place_type": "Entertainment", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Arcade entrance"},
    {"title": "Board Game Cafe", "description": "Pick a game from the wall, order drinks, and get competitive.", "tags": ["games", "chill", "coffee"], "place_type": "Cafe", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Cafe entrance"},
    {"title": "Escape Room Challenge", "description": "Test our problem-solving skills together. Can we escape in time?", "tags": ["adventure", "games", "active"], "place_type": "Entertainment", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "1-2h", "suggested_meetup_type": "Escape room entrance"},
    {"title": "Karaoke Night", "description": "Belt out some tunes together. Judgment-free zone!", "tags": ["fun", "music", "nightlife"], "place_type": "Bar", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Karaoke bar entrance"},
    
    # Cozy/Low-key
    {"title": "Vinyl Record Shopping", "description": "Browse record stores, share music tastes, discover new sounds together.", "tags": ["music", "creative", "chill"], "place_type": "Shop", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Record store entrance"},
    {"title": "Plant Shopping Date", "description": "Visit a nursery or plant shop. Help each other pick out a new plant friend.", "tags": ["chill", "nature", "creative"], "place_type": "Shop", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Nursery entrance"},
    {"title": "Thrift Store Treasure Hunt", "description": "Set a budget, see who can find the best hidden gem.", "tags": ["fun", "creative", "casual"], "place_type": "Shop", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Store entrance"},
    {"title": "Sunrise Coffee", "description": "Early birds meet for coffee as the city wakes up. Peaceful and intimate.", "tags": ["coffee", "morning", "peaceful"], "place_type": "Cafe", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Cafe entrance"},
    {"title": "Jazz Night", "description": "Find a low-key spot with live jazz. Great music, good conversation.", "tags": ["music", "nightlife", "chill"], "place_type": "Bar", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Venue entrance"},
    
    # Daytime Safe (Recommended)
    {"title": "Weekend Market Wander", "description": "Explore a weekend market together. Vintage finds, local food, good energy.", "tags": ["shopping", "food", "outdoors"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Market entrance"},
    {"title": "Dog Park Hangout", "description": "If you have a dog (or just love them), meet at a dog park. Furry friends included!", "tags": ["outdoors", "animals", "casual"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h", "suggested_meetup_type": "Dog park entrance"},
    {"title": "Smoothie & Walk", "description": "Grab healthy smoothies and walk around a nice area. Light and refreshing.", "tags": ["healthy", "walk", "casual"], "place_type": "Neighborhood", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Smoothie shop entrance"},
    {"title": "Cooking Class", "description": "Learn to make something new together. Teamwork + delicious food.", "tags": ["food", "creative", "active"], "place_type": "Kitchen studio", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Class venue entrance"},
    {"title": "Pottery or Art Class", "description": "Get creative with a pottery or painting class. No skills needed!", "tags": ["creative", "art", "fun"], "place_type": "Studio", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Studio entrance"},
    {"title": "Yoga in the Park", "description": "Join a free outdoor yoga class together. Zen vibes only.", "tags": ["fitness", "outdoors", "wellness"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h", "suggested_meetup_type": "Class gathering spot"},
    {"title": "Comedy Show", "description": "Shared laughter is the best icebreaker. Find a local comedy night.", "tags": ["fun", "nightlife", "entertainment"], "place_type": "Venue", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Venue entrance"},
    {"title": "Live Music Discovery", "description": "Check out a local band or open mic night. New music, new memories.", "tags": ["music", "nightlife", "adventure"], "place_type": "Venue", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Venue entrance"},
    
    # More variety
    {"title": "Bike Ride Together", "description": "Rent bikes and explore the city's bike paths. Active and adventurous.", "tags": ["active", "outdoors", "adventure"], "place_type": "Trail/Path", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Bike rental spot"},
    {"title": "Beach Day (if applicable)", "description": "Walk along the beach, dip your toes in the water, enjoy the views.", "tags": ["outdoors", "beach", "relaxed"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h", "suggested_meetup_type": "Beach entrance"},
    {"title": "Paddleboarding or Kayaking", "description": "Get on the water together! Rentals available at most waterfronts.", "tags": ["active", "outdoors", "adventure"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Rental shop"},
    {"title": "Rock Climbing (Indoor)", "description": "Try indoor climbing together. Great for building trust and having fun.", "tags": ["active", "adventure", "fun"], "place_type": "Gym", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Climbing gym entrance"},
    {"title": "Wine Tasting", "description": "Visit a local wine bar or vineyard. Sample, sip, and savor.", "tags": ["wine", "romantic", "chill"], "place_type": "Bar/Vineyard", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Venue entrance"},
    {"title": "Street Food Tour", "description": "Walk through the best street food spots in the city. Eat your way through!", "tags": ["food", "adventure", "walk"], "place_type": "Multiple", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h", "suggested_meetup_type": "Starting point"},
    {"title": "Stargazing", "description": "Find a dark spot away from city lights. Bring a blanket and look up.", "tags": ["romantic", "outdoors", "peaceful"], "place_type": "Viewpoint", "safety_level": "Mixed", "cost_hint": "Free", "duration_hint": "2-4h", "suggested_meetup_type": "Parking area (daytime meet)"},
    {"title": "Aquarium Visit", "description": "Wander through underwater worlds. Jellyfish are surprisingly good conversation starters.", "tags": ["museum", "fun", "peaceful"], "place_type": "Aquarium", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Aquarium entrance"},
    {"title": "Zoo Day", "description": "Channel your inner kid at the zoo. Rate animals on cuteness.", "tags": ["fun", "animals", "outdoors"], "place_type": "Zoo", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h", "suggested_meetup_type": "Zoo entrance"},
    {"title": "Meditation or Sound Bath", "description": "Try something different. Join a group meditation or sound healing session.", "tags": ["wellness", "peaceful", "creative"], "place_type": "Studio", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h", "suggested_meetup_type": "Studio entrance"},
]

# City-specific templates
CITY_TEMPLATES = {
    # United States
    "New York City": [
        {"title": "Central Park Stroll + Hot Chocolate", "description": "Walk through the iconic park, find a bench with a view, and warm up with hot chocolate from a nearby cafe.", "locality_label": "Central Park", "tags": ["outdoors", "classic", "romantic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "High Line Walk + Chelsea Market", "description": "Stroll the elevated park with amazing city views, then explore the food options at Chelsea Market.", "locality_label": "Chelsea", "tags": ["outdoors", "food", "scenic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Brooklyn Bridge Sunset Walk", "description": "Cross the iconic bridge at golden hour. Start in Manhattan, end with pizza in Brooklyn.", "locality_label": "Brooklyn Bridge", "tags": ["outdoors", "scenic", "romantic"], "place_type": "Bridge", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "MoMA Quick Tour + Coffee", "description": "Hit the highlights at the Museum of Modern Art, then discuss favorites over coffee nearby.", "locality_label": "Midtown", "tags": ["art", "culture", "coffee"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Greenwich Village Wander", "description": "Get lost in the charming streets of the Village. Discover hidden cafes and bookstores.", "locality_label": "Greenwich Village", "tags": ["walk", "chill", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "DUMBO Waterfront Views", "description": "Take in the stunning Manhattan skyline from Brooklyn's DUMBO area. Great photo spots.", "locality_label": "DUMBO", "tags": ["scenic", "outdoors", "romantic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Washington Square Park Hangout", "description": "People-watch at this iconic park. Musicians, chess players, and good energy.", "locality_label": "Greenwich Village", "tags": ["outdoors", "chill", "culture"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "The Met Museum Exploration", "description": "Pick a section of the massive museum and explore together. Temple of Dendur is a must.", "locality_label": "Upper East Side", "tags": ["art", "culture", "history"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "SoHo Art Gallery Hop", "description": "Browse the galleries of SoHo, then grab coffee on a cobblestone street.", "locality_label": "SoHo", "tags": ["art", "culture", "walk"], "place_type": "Gallery", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Hudson River Park Walk", "description": "Walk along the river with great views. Stop for snacks along the way.", "locality_label": "West Side", "tags": ["outdoors", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
    ],
    "Los Angeles": [
        {"title": "Griffith Observatory Views", "description": "Watch the sunset over LA from Griffith Observatory. Iconic views of the Hollywood sign.", "locality_label": "Griffith Park", "tags": ["scenic", "outdoors", "romantic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Santa Monica Pier Daytime", "description": "Classic LA beach vibes. Walk the pier, ride the ferris wheel, enjoy the ocean.", "locality_label": "Santa Monica", "tags": ["beach", "fun", "classic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "The Grove Stroll", "description": "Walk around The Grove, window shop, grab a coffee, enjoy the pleasant atmosphere.", "locality_label": "Fairfax", "tags": ["walk", "shopping", "chill"], "place_type": "Shopping area", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Venice Beach Boardwalk", "description": "Experience the unique Venice vibe. Street performers, art, and people-watching.", "locality_label": "Venice", "tags": ["beach", "culture", "fun"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "LACMA Art & Lights", "description": "Explore the LA County Museum of Art, then take photos at the iconic Urban Light installation.", "locality_label": "Miracle Mile", "tags": ["art", "culture", "creative"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Grand Central Market Snack Crawl", "description": "Sample diverse cuisines at this historic downtown market. Something for every taste.", "locality_label": "Downtown LA", "tags": ["food", "culture", "adventure"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Runyon Canyon Hike", "description": "Easy hike with great city views. Popular with locals and dogs.", "locality_label": "Hollywood Hills", "tags": ["active", "outdoors", "scenic"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Arts District Walk", "description": "Explore LA's creative hub. Murals, galleries, and trendy cafes.", "locality_label": "Arts District", "tags": ["art", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Malibu Beach Day", "description": "Escape to Malibu for beach time and ocean views. Worth the drive.", "locality_label": "Malibu", "tags": ["beach", "scenic", "relaxed"], "place_type": "Beach", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Silver Lake Reservoir Walk", "description": "Walk around the scenic reservoir in one of LA's coolest neighborhoods.", "locality_label": "Silver Lake", "tags": ["outdoors", "walk", "chill"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
    ],
    "San Francisco": [
        {"title": "Golden Gate Viewpoint + Coffee", "description": "Take in views of the iconic bridge from Baker Beach or Crissy Field, then warm up with coffee.", "locality_label": "Presidio", "tags": ["scenic", "outdoors", "classic"], "place_type": "Viewpoint", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Ferry Building Snack Crawl", "description": "Explore the artisan food stalls at the Ferry Building. Sample local treats.", "locality_label": "Embarcadero", "tags": ["food", "local", "waterfront"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Crissy Field Waterfront Walk", "description": "Flat, easy walk along the water with Golden Gate views. Perfect for conversation.", "locality_label": "Marina", "tags": ["outdoors", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Mission District Murals", "description": "Explore the vibrant murals of Clarion Alley and Balmy Alley. Art meets culture.", "locality_label": "Mission District", "tags": ["art", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Dolores Park Hangout", "description": "San Francisco's favorite park. Great views, good vibes, perfect for a casual date.", "locality_label": "Mission", "tags": ["outdoors", "chill", "scenic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Chinatown Walking Tour", "description": "Explore the oldest Chinatown in North America. Dim sum stops encouraged.", "locality_label": "Chinatown", "tags": ["food", "culture", "history"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Lands End Coastal Trail", "description": "Easy hike with ocean views and ruins of the Sutro Baths. Magical fog included.", "locality_label": "Lands End", "tags": ["outdoors", "scenic", "nature"], "place_type": "Trail", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Hayes Valley Stroll", "description": "Walk through this trendy neighborhood. Boutiques, cafes, and good vibes.", "locality_label": "Hayes Valley", "tags": ["walk", "shopping", "chill"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Japanese Tea Garden", "description": "Find serenity in Golden Gate Park's beautiful tea garden. Tea ceremony optional.", "locality_label": "Golden Gate Park", "tags": ["peaceful", "nature", "culture"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Pier 39 & Fisherman's Wharf", "description": "Touristy but fun! See the sea lions, grab clam chowder in a bread bowl.", "locality_label": "Fisherman's Wharf", "tags": ["waterfront", "food", "fun"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Chicago": [
        {"title": "Millennium Park + Riverwalk", "description": "See Cloud Gate (The Bean), then walk along the Chicago Riverwalk. Classic Chicago.", "locality_label": "Loop", "tags": ["outdoors", "scenic", "classic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Lakefront Trail Stroll", "description": "Walk along Lake Michigan with stunning skyline views. 18 miles of options.", "locality_label": "Lakefront", "tags": ["outdoors", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Art Institute Highlights", "description": "Explore world-class art, from Seurat to Hopper. Don't miss the lion statues.", "locality_label": "Loop", "tags": ["art", "culture", "museum"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Lincoln Park Zoo (Free!)", "description": "One of the few free zoos in the country. Penguins, lions, and a conservatory.", "locality_label": "Lincoln Park", "tags": ["animals", "outdoors", "fun"], "place_type": "Zoo", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Wicker Park Exploration", "description": "Hip neighborhood with vintage shops, cafes, and street art. Great for wandering.", "locality_label": "Wicker Park", "tags": ["walk", "culture", "creative"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Navy Pier at Sunset", "description": "Watch the sunset over the lake, ride the Centennial Wheel, enjoy the carnival atmosphere.", "locality_label": "Streeterville", "tags": ["waterfront", "fun", "romantic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Chicago Architecture Boat Tour", "description": "Learn about Chicago's amazing architecture from the river. Worth every penny.", "locality_label": "River", "tags": ["culture", "scenic", "classic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "1-2h"},
        {"title": "Pilsen Arts District", "description": "Explore the vibrant murals and galleries of this Mexican-American neighborhood.", "locality_label": "Pilsen", "tags": ["art", "culture", "food"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "606 Trail Walk", "description": "Walk the elevated trail through four neighborhoods. Like a mini High Line.", "locality_label": "Bucktown/Wicker Park", "tags": ["outdoors", "walk", "active"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Chicago Pizza Debate", "description": "Deep dish vs. tavern style. Pick a famous spot and settle the debate together.", "locality_label": "Various", "tags": ["food", "fun", "classic"], "place_type": "Restaurant", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "1-2h"},
    ],
    "Boston": [
        {"title": "Freedom Trail Mini-Walk", "description": "Follow the red line through historic sites. Pick a section and learn some history together.", "locality_label": "Downtown", "tags": ["history", "walk", "culture"], "place_type": "Historic district", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Public Garden Swan Boats", "description": "Ride the swan boats in summer, or just stroll through the beautiful garden.", "locality_label": "Back Bay", "tags": ["outdoors", "romantic", "classic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Seaport Waterfront Walk", "description": "Explore Boston's modern waterfront district. Harborwalk, public art, and ocean views.", "locality_label": "Seaport", "tags": ["waterfront", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "North End Italian Walk", "description": "Wander through Boston's Italian neighborhood. Cannoli stop mandatory.", "locality_label": "North End", "tags": ["food", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Harvard Yard Visit", "description": "Walk through Harvard's historic campus. Feel smart by association.", "locality_label": "Cambridge", "tags": ["history", "walk", "culture"], "place_type": "Campus", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Charles River Esplanade", "description": "Walk or bike along the Charles with views of Back Bay and Cambridge.", "locality_label": "Back Bay", "tags": ["outdoors", "scenic", "walk"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Museum of Fine Arts", "description": "Explore one of the country's best art museums. Free admission on Wednesday evenings.", "locality_label": "Fenway", "tags": ["art", "culture", "museum"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Newbury Street Stroll", "description": "Walk Boston's famous shopping street. Boutiques, cafes, and brownstone beauty.", "locality_label": "Back Bay", "tags": ["walk", "shopping", "chill"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Beacon Hill Walk", "description": "Explore the charming brick sidewalks and gas lamps of historic Beacon Hill.", "locality_label": "Beacon Hill", "tags": ["walk", "history", "romantic"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Arnold Arboretum", "description": "265 acres of beautiful trees and plants. Free and peaceful.", "locality_label": "Jamaica Plain", "tags": ["nature", "outdoors", "peaceful"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "2-4h"},
    ],
    "Washington DC": [
        {"title": "National Mall Monuments at Sunset", "description": "Walk the Mall as the sun sets. Lincoln Memorial, Washington Monument, reflecting pools.", "locality_label": "National Mall", "tags": ["scenic", "history", "romantic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Smithsonian Museum Day", "description": "Pick a Smithsonian (all free!) - Air & Space, Natural History, American History. Endless options.", "locality_label": "National Mall", "tags": ["museum", "culture", "history"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Georgetown Waterfront Walk", "description": "Stroll along the Potomac in historic Georgetown. Beautiful any season.", "locality_label": "Georgetown", "tags": ["waterfront", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Eastern Market Saturday", "description": "DC's beloved weekend market. Local food, art, and community vibes.", "locality_label": "Capitol Hill", "tags": ["market", "food", "local"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "National Gallery of Art", "description": "World-class art collection, completely free. Don't miss the underground walkway.", "locality_label": "National Mall", "tags": ["art", "culture", "museum"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Tidal Basin Walk", "description": "Beautiful any time, spectacular during cherry blossom season. Jefferson Memorial views.", "locality_label": "Tidal Basin", "tags": ["outdoors", "scenic", "romantic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Adams Morgan Exploration", "description": "Diverse neighborhood with international food, murals, and vintage shops.", "locality_label": "Adams Morgan", "tags": ["food", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "U Street Corridor", "description": "Historic neighborhood with music venues, restaurants, and Black history.", "locality_label": "U Street", "tags": ["culture", "food", "nightlife"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "National Zoo", "description": "Free zoo! Giant pandas, elephants, and beautiful Rock Creek Park setting.", "locality_label": "Woodley Park", "tags": ["animals", "outdoors", "fun"], "place_type": "Zoo", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Dumbarton Oaks Gardens", "description": "Stunning historic gardens in Georgetown. Like stepping into another world.", "locality_label": "Georgetown", "tags": ["garden", "peaceful", "romantic"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
    ],
    "Seattle": [
        {"title": "Pike Place Snack Crawl", "description": "Explore the iconic market. Watch fish fly, sample local treats, find hidden gems.", "locality_label": "Pike Place", "tags": ["food", "classic", "adventure"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Gas Works Park Views", "description": "Unique park with industrial ruins and the best skyline views of Seattle.", "locality_label": "Wallingford", "tags": ["scenic", "outdoors", "unique"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Waterfront Ferries + Coffee", "description": "Ride the ferry to Bainbridge or just along the water. Grab coffee at Pike Place first.", "locality_label": "Waterfront", "tags": ["scenic", "coffee", "adventure"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Discovery Park Trails", "description": "Seattle's largest park with trails, beach access, and lighthouse views.", "locality_label": "Magnolia", "tags": ["outdoors", "nature", "scenic"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Capitol Hill Coffee & Walk", "description": "Explore Seattle's vibrant, artsy neighborhood. Great coffee shops everywhere.", "locality_label": "Capitol Hill", "tags": ["coffee", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Ballard Locks & Gardens", "description": "Watch boats pass through the locks and explore the botanical garden.", "locality_label": "Ballard", "tags": ["outdoors", "unique", "nature"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Olympic Sculpture Park", "description": "Free outdoor art with stunning water and mountain views. SAM's best kept secret.", "locality_label": "Belltown", "tags": ["art", "outdoors", "scenic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Fremont Troll & Quirky Walk", "description": "Visit the famous Fremont Troll, then explore the 'Center of the Universe.'", "locality_label": "Fremont", "tags": ["unique", "walk", "fun"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Kerry Park Sunset", "description": "The postcard view of Seattle. Space Needle, skyline, Mt. Rainier on clear days.", "locality_label": "Queen Anne", "tags": ["scenic", "romantic", "classic"], "place_type": "Viewpoint", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "30-60m"},
        {"title": "Museum of Pop Culture", "description": "Music, sci-fi, and pop culture in a Frank Gehry building. Interactive and fun.", "locality_label": "Seattle Center", "tags": ["museum", "fun", "culture"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Austin": [
        {"title": "Lady Bird Lake Trail + Tacos", "description": "Walk or bike the scenic trail, then refuel at one of Austin's legendary taco spots.", "locality_label": "Lady Bird Lake", "tags": ["outdoors", "food", "active"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "South Congress Stroll", "description": "Austin's iconic strip. Vintage shops, food trucks, and great people-watching.", "locality_label": "SoCo", "tags": ["walk", "shopping", "fun"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Zilker Park Picnic", "description": "Austin's beloved park. Barton Springs nearby for brave swimmers.", "locality_label": "Zilker", "tags": ["outdoors", "relaxed", "nature"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Mount Bonnell Sunset", "description": "Climb the steps for panoramic views of Lake Austin and the Hill Country.", "locality_label": "West Austin", "tags": ["scenic", "outdoors", "romantic"], "place_type": "Viewpoint", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "East Austin Art Walk", "description": "Galleries, murals, and creative spaces in Austin's hippest area.", "locality_label": "East Austin", "tags": ["art", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Food Truck Park Hop", "description": "Austin has amazing food truck parks. Pick one and eat your way through.", "locality_label": "Various", "tags": ["food", "casual", "fun"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Congress Avenue Bat Bridge", "description": "Watch 1.5 million bats emerge at sunset (March-October). Uniquely Austin.", "locality_label": "Downtown", "tags": ["nature", "unique", "evening"], "place_type": "Bridge", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Barton Springs Pool", "description": "Take a refreshing dip in the natural spring-fed pool. Very Austin.", "locality_label": "Zilker", "tags": ["active", "nature", "fun"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Live Music on 6th Street", "description": "Austin is the Live Music Capital. Find a venue, grab a drink, enjoy the show.", "locality_label": "Downtown", "tags": ["music", "nightlife", "fun"], "place_type": "Venue", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Rainey Street Walk", "description": "Historic bungalows turned into bars and eateries. Laid-back Austin vibes.", "locality_label": "Rainey Street", "tags": ["food", "nightlife", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Miami": [
        {"title": "South Beach Daytime Walk", "description": "Walk the iconic beach boardwalk. Art Deco buildings, ocean views, and people-watching.", "locality_label": "South Beach", "tags": ["beach", "walk", "classic"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Wynwood Walls & Murals", "description": "Explore the famous outdoor street art museum. Vibrant, colorful, and Instagram-worthy.", "locality_label": "Wynwood", "tags": ["art", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Bayside Waterfront Hang", "description": "Walk along Biscayne Bay at Bayside Marketplace. Views, music, and good energy.", "locality_label": "Downtown", "tags": ["waterfront", "chill", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Little Havana Exploration", "description": "Experience Cuban culture on Calle Ocho. Coffee, cigars, and domino park.", "locality_label": "Little Havana", "tags": ["culture", "food", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Vizcaya Museum & Gardens", "description": "Stunning Italian Renaissance-style villa with beautiful gardens on Biscayne Bay.", "locality_label": "Coconut Grove", "tags": ["museum", "garden", "romantic"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Design District Walk", "description": "Upscale neighborhood with galleries, luxury shopping, and great architecture.", "locality_label": "Design District", "tags": ["art", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Key Biscayne Beach Day", "description": "Escape to the key for calmer beaches and beautiful park trails.", "locality_label": "Key Biscayne", "tags": ["beach", "nature", "relaxed"], "place_type": "Beach", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Coral Gables Stroll", "description": "Beautiful Mediterranean-style architecture. Walk around the Biltmore area.", "locality_label": "Coral Gables", "tags": ["walk", "history", "scenic"], "place_type": "Neighborhood walk", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Coconut Grove Village", "description": "Bohemian neighborhood with cafes, shops, and waterfront parks.", "locality_label": "Coconut Grove", "tags": ["walk", "chill", "nature"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Pérez Art Museum Miami", "description": "Contemporary art with stunning bay views. Beautiful building by Herzog & de Meuron.", "locality_label": "Downtown", "tags": ["art", "museum", "scenic"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Houston": [
        {"title": "Buffalo Bayou Park Walk", "description": "Houston's award-winning urban park. 160 acres of trails, gardens, and public art.", "locality_label": "Downtown", "tags": ["outdoors", "walk", "scenic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Museum District Day", "description": "19 museums in one area! Many free. Pick one or two and explore together.", "locality_label": "Museum District", "tags": ["museum", "culture", "art"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "Free-$$", "duration_hint": "2-4h"},
        {"title": "Discovery Green Hangout", "description": "Downtown's beloved urban park. Events, food, and a great central meeting spot.", "locality_label": "Downtown", "tags": ["outdoors", "chill", "events"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Heights Food Crawl", "description": "Walk 19th Street in the Heights. Antique shops, restaurants, and historic charm.", "locality_label": "The Heights", "tags": ["food", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Rice University Campus Walk", "description": "Beautiful campus with stunning architecture. Free and open to the public.", "locality_label": "Rice Village", "tags": ["walk", "culture", "peaceful"], "place_type": "Campus", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Montrose Art & Coffee", "description": "Explore Houston's creative neighborhood. Galleries, murals, and indie coffee shops.", "locality_label": "Montrose", "tags": ["art", "coffee", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Space Center Houston", "description": "Explore NASA! See real spacecraft, touch a moon rock, and nerd out together.", "locality_label": "Clear Lake", "tags": ["museum", "fun", "unique"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Hermann Park & Zoo", "description": "Beautiful park with a free zoo, Japanese Garden, and pedal boats.", "locality_label": "Museum District", "tags": ["outdoors", "animals", "relaxed"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free-$", "duration_hint": "2-4h"},
        {"title": "East End Mexican Food Trail", "description": "Explore authentic Mexican food in Houston's East End. Tacos al pastor are a must.", "locality_label": "East End", "tags": ["food", "culture", "adventure"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Memorial Park Trails", "description": "1,500 acres of trails and nature in the heart of Houston. Great for a morning walk.", "locality_label": "Memorial", "tags": ["outdoors", "nature", "active"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
    ],
    "Dallas": [
        {"title": "Dallas Arboretum Walk", "description": "66 acres of stunning gardens on White Rock Lake. Beautiful any season.", "locality_label": "East Dallas", "tags": ["garden", "nature", "romantic"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Bishop Arts District Stroll", "description": "Dallas's artsy neighborhood. Boutiques, galleries, and diverse restaurants.", "locality_label": "Oak Cliff", "tags": ["walk", "art", "food"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Klyde Warren Park Hangout", "description": "Deck park over a freeway with food trucks, games, and events.", "locality_label": "Downtown", "tags": ["outdoors", "food", "chill"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Dallas Museum of Art", "description": "Free admission! World-class collection in the Arts District.", "locality_label": "Arts District", "tags": ["art", "museum", "culture"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "White Rock Lake Trail", "description": "9-mile loop around the lake. Walk, bike, or just find a bench and chat.", "locality_label": "White Rock", "tags": ["outdoors", "active", "scenic"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Deep Ellum Art & Music", "description": "Murals, live music venues, and creative energy. Dallas's most vibrant neighborhood.", "locality_label": "Deep Ellum", "tags": ["art", "music", "nightlife"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Perot Museum of Nature and Science", "description": "Interactive science museum. Touch a dinosaur bone, play with physics.", "locality_label": "Downtown", "tags": ["museum", "fun", "science"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Trinity Groves Food Hall", "description": "Restaurant incubator with diverse cuisines. Pick a spot, or share multiple.", "locality_label": "West Dallas", "tags": ["food", "adventure", "casual"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "1-2h"},
        {"title": "Lower Greenville Walk", "description": "Walkable strip with bars, restaurants, and neighborhood charm.", "locality_label": "Greenville", "tags": ["walk", "food", "nightlife"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Nasher Sculpture Center", "description": "Indoor/outdoor sculpture museum with a serene garden. Part of the Arts District.", "locality_label": "Arts District", "tags": ["art", "garden", "peaceful"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "1-2h"},
    ],
    "Atlanta": [
        {"title": "Piedmont Park Stroll", "description": "Atlanta's Central Park. Skyline views, beautiful grounds, and great people-watching.", "locality_label": "Midtown", "tags": ["outdoors", "walk", "scenic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "BeltLine Eastside Trail", "description": "Walk or bike the famous BeltLine. Murals, restaurants, and urban energy.", "locality_label": "BeltLine", "tags": ["walk", "art", "active"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Ponce City Market", "description": "Food hall, shops, and rooftop amusement park in a historic Sears building.", "locality_label": "BeltLine", "tags": ["food", "fun", "shopping"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Krog Street Market", "description": "Trendy food hall right on the BeltLine. Great variety and industrial-chic vibes.", "locality_label": "Inman Park", "tags": ["food", "culture", "casual"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "High Museum of Art", "description": "Southeast's leading art museum. Beautiful building, great collection.", "locality_label": "Midtown", "tags": ["art", "museum", "culture"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Little Five Points Exploration", "description": "Atlanta's alternative neighborhood. Vintage shops, street art, and unique character.", "locality_label": "Little Five Points", "tags": ["walk", "culture", "unique"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Oakland Cemetery Walk", "description": "Historic garden cemetery with stunning Victorian monuments. Peaceful and beautiful.", "locality_label": "Grant Park", "tags": ["history", "walk", "peaceful"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Centennial Olympic Park", "description": "Downtown's gathering place. Fountain of Rings, World of Coca-Cola nearby.", "locality_label": "Downtown", "tags": ["outdoors", "fun", "classic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Georgia Aquarium", "description": "One of the world's largest aquariums. Whale sharks, beluga whales, and more.", "locality_label": "Downtown", "tags": ["animals", "fun", "museum"], "place_type": "Aquarium", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Westside Provisions District", "description": "Upscale area with great restaurants, shops, and the famous Star Provisions.", "locality_label": "Westside", "tags": ["food", "shopping", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Denver": [
        {"title": "City Park + Museum Row", "description": "Beautiful park with lake views. Zoo and Natural History Museum right there.", "locality_label": "City Park", "tags": ["outdoors", "museum", "nature"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free-$$", "duration_hint": "2-4h"},
        {"title": "Union Station Meet", "description": "Denver's beautiful renovated station. Great restaurants and bars inside.", "locality_label": "LoDo", "tags": ["food", "architecture", "classic"], "place_type": "Station", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "RiNo Art District Walk", "description": "Denver's creative hub. Murals, galleries, breweries, and good energy.", "locality_label": "RiNo", "tags": ["art", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Cherry Creek Trail", "description": "40 miles of paved trail. Pick a section and walk or bike together.", "locality_label": "Various", "tags": ["outdoors", "active", "scenic"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Denver Art Museum", "description": "World-class museum with distinctive architecture. Western and contemporary art.", "locality_label": "Golden Triangle", "tags": ["art", "museum", "culture"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Larimer Square Stroll", "description": "Denver's oldest and most iconic block. Shops, restaurants, and string lights.", "locality_label": "LoDo", "tags": ["walk", "shopping", "romantic"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "1-2h"},
        {"title": "Red Rocks Amphitheatre", "description": "Hike the trails and take in views at this iconic venue. No concert required.", "locality_label": "Morrison", "tags": ["outdoors", "scenic", "unique"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Denver Botanic Gardens", "description": "23 acres of beautiful gardens in the heart of the city.", "locality_label": "Cheesman Park", "tags": ["garden", "nature", "peaceful"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "16th Street Mall Walk", "description": "Mile-long pedestrian mall downtown. Free shuttle, shops, and restaurants.", "locality_label": "Downtown", "tags": ["walk", "shopping", "casual"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "South Pearl Street", "description": "Charming neighborhood street with antiques, cafes, and local shops.", "locality_label": "Platt Park", "tags": ["walk", "shopping", "chill"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
    ],
    "San Diego": [
        {"title": "Balboa Park Exploration", "description": "1,200 acres of gardens, museums, and the famous zoo. Pick your adventure.", "locality_label": "Balboa Park", "tags": ["outdoors", "museum", "garden"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free-$$", "duration_hint": "2-4h"},
        {"title": "La Jolla Cove Walk", "description": "Stunning coastline, sea lions, and some of the best views in California.", "locality_label": "La Jolla", "tags": ["beach", "scenic", "nature"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Gaslamp Quarter Stroll", "description": "Downtown's historic neighborhood. Victorian architecture, restaurants, nightlife.", "locality_label": "Gaslamp Quarter", "tags": ["walk", "food", "nightlife"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Coronado Beach Day", "description": "Cross the bridge to the island for beautiful beaches and the iconic Hotel del Coronado.", "locality_label": "Coronado", "tags": ["beach", "relaxed", "scenic"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Little Italy Food Tour", "description": "Walk through Little Italy sampling Italian food, coffee, and gelato.", "locality_label": "Little Italy", "tags": ["food", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Sunset Cliffs Sunset", "description": "Watch the sunset from these dramatic coastal cliffs. Bring a blanket.", "locality_label": "Ocean Beach", "tags": ["scenic", "romantic", "nature"], "place_type": "Viewpoint", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Old Town Historic Walk", "description": "Explore California's birthplace. Mexican food, history, and colorful markets.", "locality_label": "Old Town", "tags": ["history", "food", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Mission Beach Boardwalk", "description": "Classic beach boardwalk. Belmont Park amusement rides nearby.", "locality_label": "Mission Beach", "tags": ["beach", "fun", "casual"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Torrey Pines Hike", "description": "Easy coastal hike with stunning ocean views. One of San Diego's natural treasures.", "locality_label": "Torrey Pines", "tags": ["outdoors", "nature", "scenic"], "place_type": "Trail", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "North Park Craft Beer Walk", "description": "Explore San Diego's craft beer capital. Dozens of breweries within walking distance.", "locality_label": "North Park", "tags": ["beer", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Philadelphia": [
        {"title": "Reading Terminal Market", "description": "Historic indoor market with incredible food diversity. Get there early on weekends.", "locality_label": "Center City", "tags": ["food", "classic", "market"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Rittenhouse Square Hangout", "description": "Philly's most elegant park. Pack a coffee and people-watch.", "locality_label": "Rittenhouse", "tags": ["outdoors", "chill", "classic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Philadelphia Museum of Art", "description": "World-class art collection. Yes, run the Rocky steps first if you must.", "locality_label": "Fairmount", "tags": ["art", "museum", "classic"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Schuylkill River Trail Walk", "description": "Scenic trail along the river. Great for walking or biking.", "locality_label": "Schuylkill River", "tags": ["outdoors", "walk", "scenic"], "place_type": "Trail", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Old City Historic Walk", "description": "Independence Hall, Liberty Bell, and cobblestone streets. History everywhere.", "locality_label": "Old City", "tags": ["history", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Spruce Street Harbor Park", "description": "Waterfront park with hammocks, food, and river views. Summer only.", "locality_label": "Penn's Landing", "tags": ["waterfront", "chill", "fun"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Fishtown Exploration", "description": "Philly's hippest neighborhood. Coffee shops, breweries, and creative energy.", "locality_label": "Fishtown", "tags": ["walk", "culture", "food"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Italian Market Walk", "description": "America's oldest outdoor market. Fresh produce, cheese shops, and cannoli.", "locality_label": "South Philly", "tags": ["food", "market", "culture"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Fairmount Park Stroll", "description": "One of the largest urban parks in the US. Historic houses, Japanese garden, zoo.", "locality_label": "Fairmount", "tags": ["outdoors", "nature", "peaceful"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "East Passyunk Food Tour", "description": "Walk this hip South Philly strip and sample restaurants along the way.", "locality_label": "South Philly", "tags": ["food", "walk", "adventure"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    # India
    "Mumbai": [
        {"title": "Marine Drive Sunset Stroll", "description": "Walk the iconic Queen's Necklace as the sun sets over the Arabian Sea.", "locality_label": "Marine Drive", "tags": ["scenic", "outdoors", "romantic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Bandra Bandstand Walk + Chai", "description": "Explore the Bandstand promenade, spot celebrity homes, and enjoy chai.", "locality_label": "Bandra", "tags": ["walk", "chai", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Gateway of India + Colaba Walk", "description": "Meet at the iconic Gateway, then explore the charming Colaba Causeway.", "locality_label": "Colaba", "tags": ["history", "walk", "classic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Kala Ghoda Art Walk", "description": "Explore Mumbai's art district. Galleries, cafes, and heritage buildings.", "locality_label": "Fort", "tags": ["art", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Worli Seaface Evening", "description": "Walk along Worli seaface with views of the Bandra-Worli Sea Link.", "locality_label": "Worli", "tags": ["outdoors", "scenic", "walk"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "NCPA Gardens + Promenade", "description": "Cultural center with beautiful gardens and sea views. Often has outdoor events.", "locality_label": "Nariman Point", "tags": ["culture", "peaceful", "scenic"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Elephanta Caves Ferry Trip", "description": "Take the ferry to Elephanta Island. Ancient caves with historic sculptures.", "locality_label": "Gateway of India", "tags": ["history", "adventure", "scenic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Girgaon Chowpatty Beach", "description": "Classic Mumbai beach vibes. Bhel puri, kulfi, and local atmosphere.", "locality_label": "Girgaon", "tags": ["beach", "food", "local"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Crawford Market Exploration", "description": "Historic market with fruits, flowers, and unique finds. A Mumbai institution.", "locality_label": "CST", "tags": ["market", "local", "unique"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Versova Beach Sunset", "description": "Less crowded beach perfect for sunset. Great seafood nearby.", "locality_label": "Versova", "tags": ["beach", "scenic", "relaxed"], "place_type": "Beach", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
    ],
    "Delhi": [
        {"title": "India Gate Evening Walk", "description": "Stroll around India Gate at sunset. Ice cream vendors, families, and monuments.", "locality_label": "India Gate", "tags": ["outdoors", "classic", "evening"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Hauz Khas Village Vibes", "description": "Historic ruins meets trendy cafes. Walk around the lake, explore the fort.", "locality_label": "Hauz Khas", "tags": ["culture", "food", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Lodhi Garden Stroll", "description": "Beautiful gardens with 15th century tombs. Popular with walkers and couples.", "locality_label": "Lodhi Colony", "tags": ["outdoors", "history", "peaceful"], "place_type": "Garden", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Chandni Chowk Food Walk", "description": "Delhi's oldest food street. Parathas, jalebis, and street food heaven.", "locality_label": "Old Delhi", "tags": ["food", "culture", "adventure"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Humayun's Tomb Visit", "description": "Stunning Mughal architecture. Precursor to the Taj Mahal. UNESCO site.", "locality_label": "Nizamuddin", "tags": ["history", "architecture", "peaceful"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Khan Market Cafe Hop", "description": "Delhi's upscale market. Great cafes, bookstores, and shopping.", "locality_label": "Khan Market", "tags": ["coffee", "shopping", "chill"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Connaught Place Circle Walk", "description": "Delhi's colonial-era center. Great architecture, restaurants, and Central Park.", "locality_label": "Connaught Place", "tags": ["walk", "food", "classic"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Qutub Minar Complex", "description": "Ancient minaret and ruins. UNESCO World Heritage Site with beautiful grounds.", "locality_label": "Mehrauli", "tags": ["history", "architecture", "culture"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "National Gallery of Modern Art", "description": "India's premier modern art museum. Beautiful building and collection.", "locality_label": "India Gate", "tags": ["art", "museum", "culture"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Sunder Nursery Garden Walk", "description": "Beautifully restored heritage park. Gardens, tombs, and peaceful vibes.", "locality_label": "Nizamuddin", "tags": ["garden", "peaceful", "nature"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Bengaluru": [
        {"title": "Cubbon Park Morning Walk", "description": "Green lung of the city. Beautiful trees, joggers, and peaceful mornings.", "locality_label": "Cubbon Park", "tags": ["outdoors", "peaceful", "classic"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "MG Road / Church Street Cafe Hop", "description": "Bangalore's classic hangout strip. Cafes, bookstores, and great energy.", "locality_label": "MG Road", "tags": ["coffee", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Lalbagh Botanical Stroll", "description": "Historic botanical garden with 1,000+ plant species. Glass house is iconic.", "locality_label": "Lalbagh", "tags": ["garden", "nature", "peaceful"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Indiranagar 12th Main Walk", "description": "Hip neighborhood with cafes, boutiques, and restaurants. Very walkable.", "locality_label": "Indiranagar", "tags": ["food", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Ulsoor Lake Evening", "description": "Peaceful lake in the middle of the city. Boating available.", "locality_label": "Ulsoor", "tags": ["outdoors", "peaceful", "water"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Koramangala Food Trail", "description": "Bangalore's food capital. Every cuisine imaginable within a few blocks.", "locality_label": "Koramangala", "tags": ["food", "adventure", "casual"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "National Gallery of Modern Art", "description": "Beautiful mansion turned museum. Contemporary Indian art.", "locality_label": "Palace Road", "tags": ["art", "museum", "culture"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Sankey Tank Walk", "description": "Lesser-known but beautiful lake. Great for morning or evening walks.", "locality_label": "Malleswaram", "tags": ["outdoors", "peaceful", "walk"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Jayanagar 4th Block Walk", "description": "Traditional Bangalore charm. Shopping complex, parks, and local joints.", "locality_label": "Jayanagar", "tags": ["walk", "local", "chill"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Nandi Hills Day Trip", "description": "Short trip for sunrise views and pleasant weather. Book the drive!", "locality_label": "Nandi Hills", "tags": ["scenic", "outdoors", "adventure"], "place_type": "Viewpoint", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Hyderabad": [
        {"title": "Hussain Sagar Lakeside", "description": "Walk around the iconic lake. Buddha statue views, boat rides available.", "locality_label": "Tank Bund", "tags": ["waterfront", "scenic", "classic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Charminar Area Evening", "description": "Explore the historic old city. Bustling markets, chai stalls, and culture.", "locality_label": "Charminar", "tags": ["culture", "history", "food"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Durgam Cheruvu Park Walk", "description": "Secret lake in the tech corridor. Peaceful escape from city chaos.", "locality_label": "Hitech City", "tags": ["outdoors", "peaceful", "nature"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Birla Mandir Sunset", "description": "Temple on a hilltop with panoramic city views. Beautiful at sunset.", "locality_label": "Naubath Pahad", "tags": ["spiritual", "scenic", "peaceful"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Golconda Fort Morning", "description": "Massive historic fort with amazing acoustics. Beat the heat, go early.", "locality_label": "Golconda", "tags": ["history", "adventure", "culture"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Jubilee Hills Road No. 36 Cafes", "description": "Trendy stretch with popular cafes and restaurants. Good for cafe hopping.", "locality_label": "Jubilee Hills", "tags": ["coffee", "food", "trendy"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Shilparamam Arts Village", "description": "Open-air museum showcasing traditional arts and crafts. Peaceful and cultural.", "locality_label": "Hitech City", "tags": ["art", "culture", "peaceful"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "KBR National Park", "description": "Green oasis in the city. Jogging trails, birdwatching, and nature.", "locality_label": "Banjara Hills", "tags": ["nature", "outdoors", "peaceful"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Necklace Road Walk", "description": "Evening promenade along Hussain Sagar. Street food and illuminated views.", "locality_label": "NTR Gardens", "tags": ["walk", "food", "evening"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Banjara Hills Shopping Walk", "description": "Upscale area with boutiques, galleries, and restaurants.", "locality_label": "Banjara Hills", "tags": ["shopping", "walk", "trendy"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Chennai": [
        {"title": "Marina Beach Early Evening", "description": "World's second-longest urban beach. Iconic Chennai experience.", "locality_label": "Marina Beach", "tags": ["beach", "classic", "local"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Besant Nagar Beach Walk", "description": "Quieter beach with good cafes nearby. Popular with locals.", "locality_label": "Besant Nagar", "tags": ["beach", "walk", "chill"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Semmozhi Poonga Garden", "description": "Beautiful botanical garden in the heart of the city. Peaceful and green.", "locality_label": "Nungambakkam", "tags": ["garden", "nature", "peaceful"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Mylapore Temple Walk", "description": "Historic neighborhood with ancient temples and traditional culture.", "locality_label": "Mylapore", "tags": ["culture", "history", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Government Museum Visit", "description": "One of India's oldest museums. Great bronze gallery.", "locality_label": "Egmore", "tags": ["museum", "history", "culture"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "San Thome Cathedral Area", "description": "Historic cathedral and peaceful neighborhood. Good evening walk.", "locality_label": "San Thome", "tags": ["history", "walk", "peaceful"], "place_type": "Neighborhood walk", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Nungambakkam Cafe Trail", "description": "Chennai's cafe central. Multiple coffee and food options.", "locality_label": "Nungambakkam", "tags": ["coffee", "food", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Guindy National Park", "description": "National park within the city. Deer, blackbucks, and nature trails.", "locality_label": "Guindy", "tags": ["nature", "outdoors", "peaceful"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "T Nagar Shopping District", "description": "Chennai's famous shopping area. Silk sarees, gold, and everything else.", "locality_label": "T Nagar", "tags": ["shopping", "culture", "local"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "ECR Drive + Cafe Stop", "description": "Scenic coastal drive with beachside cafes. Perfect for weekend morning.", "locality_label": "ECR", "tags": ["scenic", "coffee", "adventure"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Kolkata": [
        {"title": "Victoria Memorial Grounds", "description": "Stunning white marble monument with beautiful gardens. Quintessential Kolkata.", "locality_label": "Maidan", "tags": ["history", "garden", "classic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Princep Ghat Riverside", "description": "Beautiful colonial ghat on the Hooghly. Popular evening hangout.", "locality_label": "Princep Ghat", "tags": ["waterfront", "scenic", "romantic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Park Street Cafe Culture", "description": "Kolkata's most famous street. Historic cafes, restaurants, and nightlife.", "locality_label": "Park Street", "tags": ["food", "culture", "classic"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "College Street Book Walk", "description": "Largest secondhand book market in the world. Paradise for book lovers.", "locality_label": "College Street", "tags": ["books", "culture", "unique"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Indian Museum Visit", "description": "Asia's oldest museum. Egyptian mummies, Gandhara sculptures, and more.", "locality_label": "Park Street", "tags": ["museum", "history", "culture"], "place_type": "Museum", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Rabindra Sarobar Lake", "description": "Peaceful lake surrounded by trees. Morning walkers' paradise.", "locality_label": "South Kolkata", "tags": ["nature", "peaceful", "walk"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Kumartuli Artisan Walk", "description": "Watch artists create clay idols in their workshops. Unique and fascinating.", "locality_label": "Kumartuli", "tags": ["art", "culture", "unique"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Howrah Bridge Walk", "description": "Walk across the iconic cantilever bridge. Best at sunrise or sunset.", "locality_label": "Howrah Bridge", "tags": ["landmark", "walk", "scenic"], "place_type": "Bridge", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "30-60m"},
        {"title": "South City Mall Area", "description": "Modern Kolkata with mall, cafes, and restaurants.", "locality_label": "South Kolkata", "tags": ["shopping", "food", "modern"], "place_type": "Mall", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Sundarbans Day Trip", "description": "Boat ride through the mangroves. Royal Bengal tiger territory.", "locality_label": "Sundarbans", "tags": ["nature", "adventure", "unique"], "place_type": "Nature", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Pune": [
        {"title": "FC Road / JM Road Stroll", "description": "Pune's youth corridor. Cafes, restaurants, and college vibes.", "locality_label": "Deccan", "tags": ["walk", "food", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Vetal Tekdi Viewpoint", "description": "Hill in the city with trekking trails and city views. Go during daytime.", "locality_label": "Vetal Tekdi", "tags": ["outdoors", "scenic", "active"], "place_type": "Viewpoint", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Koregaon Park Cafe Street", "description": "Pune's upscale neighborhood. German Bakery area, cafes, and boutiques.", "locality_label": "Koregaon Park", "tags": ["coffee", "food", "trendy"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Aga Khan Palace Gardens", "description": "Beautiful historic palace with Gandhi museum. Peaceful grounds.", "locality_label": "Nagar Road", "tags": ["history", "garden", "peaceful"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Pashan Lake Evening", "description": "Serene lake on the city outskirts. Great for quiet evening walks.", "locality_label": "Pashan", "tags": ["nature", "peaceful", "walk"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Shaniwar Wada Evening", "description": "Historic Maratha fortress ruins. Light and sound show in evenings.", "locality_label": "Kasba Peth", "tags": ["history", "culture", "classic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Camp Area Food Trail", "description": "Pune's oldest cantonment area. Bakeries, restaurants, and history.", "locality_label": "Camp", "tags": ["food", "history", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Okayama Friendship Garden", "description": "Japanese-style garden. Peaceful and beautiful.", "locality_label": "Sinhagad Road", "tags": ["garden", "peaceful", "nature"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Pune-Okayama Riverfront", "description": "Riverside walk with gardens and open spaces.", "locality_label": "Riverfront", "tags": ["walk", "outdoors", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Sinhagad Fort Day Trip", "description": "Historic fort with stunning views. Pack snacks, enjoy the trek.", "locality_label": "Sinhagad", "tags": ["adventure", "history", "scenic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Ahmedabad": [
        {"title": "Sabarmati Riverfront Walk", "description": "Beautifully developed riverfront. Evening walks with good vibes.", "locality_label": "Sabarmati", "tags": ["waterfront", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Kankaria Lake Loop", "description": "Popular lake with gardens, zoo, and activities. Great evening spot.", "locality_label": "Kankaria", "tags": ["water", "fun", "walk"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Heritage Walk Old Ahmedabad", "description": "Walk through the historic walled city. Pols, havelis, and culture.", "locality_label": "Old City", "tags": ["history", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Sabarmati Ashram Visit", "description": "Gandhi's historic ashram. Peaceful and inspiring.", "locality_label": "Sabarmati", "tags": ["history", "peaceful", "culture"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Law Garden Night Market", "description": "Famous for handicrafts and street food. Vibrant evening atmosphere.", "locality_label": "Law Garden", "tags": ["shopping", "food", "local"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Adalaj Stepwell", "description": "Stunning historic stepwell with intricate carvings.", "locality_label": "Adalaj", "tags": ["history", "architecture", "unique"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "SG Highway Cafe Hop", "description": "Modern Ahmedabad with trendy cafes and restaurants.", "locality_label": "SG Highway", "tags": ["coffee", "food", "modern"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Sarkhej Roza", "description": "Beautiful mosque and tomb complex. Stunning architecture.", "locality_label": "Sarkhej", "tags": ["history", "architecture", "peaceful"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Science City Visit", "description": "Interactive science center with IMAX and lots of exhibits.", "locality_label": "Science City Road", "tags": ["museum", "fun", "science"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Vastrapur Lake", "description": "Pleasant lake with walking paths. Good for evening strolls.", "locality_label": "Vastrapur", "tags": ["nature", "walk", "peaceful"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
    ],
    "Jaipur": [
        {"title": "Hawa Mahal Area Meet", "description": "Meet near the iconic Pink City landmark. Explore the bustling old city.", "locality_label": "Hawa Mahal", "tags": ["history", "culture", "classic"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Jal Mahal Viewpoint", "description": "See the beautiful water palace from the shore. Great photos at sunset.", "locality_label": "Jal Mahal", "tags": ["scenic", "romantic", "iconic"], "place_type": "Viewpoint", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Albert Hall Museum + Gardens", "description": "Beautiful museum with lovely gardens. Great for evening walks.", "locality_label": "Ram Niwas Garden", "tags": ["museum", "garden", "culture"], "place_type": "Museum", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Nahargarh Fort Sunset", "description": "Fort overlooking the city. Best sunset views in Jaipur.", "locality_label": "Nahargarh", "tags": ["scenic", "history", "romantic"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "City Palace Complex", "description": "Grand royal palace in the heart of the Pink City.", "locality_label": "City Palace", "tags": ["history", "architecture", "culture"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Johari Bazaar Walk", "description": "Famous jewelry market. Window shop gems and explore old city lanes.", "locality_label": "Pink City", "tags": ["shopping", "culture", "walk"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Central Park Morning", "description": "Jaipur's beautiful central green space. Great for morning walks.", "locality_label": "C-Scheme", "tags": ["outdoors", "peaceful", "walk"], "place_type": "Park", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Amer Fort Day Trip", "description": "Majestic hill fort. A must-see when in Jaipur.", "locality_label": "Amer", "tags": ["history", "architecture", "adventure"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Sisodia Rani Garden", "description": "Beautiful terraced garden with fountains and pavilions.", "locality_label": "Agra Road", "tags": ["garden", "peaceful", "romantic"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "C-Scheme Cafe Trail", "description": "Modern Jaipur with trendy cafes and restaurants.", "locality_label": "C-Scheme", "tags": ["coffee", "food", "modern"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
    ],
    "Goa": [
        {"title": "Miramar Beach Daytime", "description": "Calm beach near Panjim. Good for relaxed walks and snacks.", "locality_label": "Miramar", "tags": ["beach", "relaxed", "scenic"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Fontainhas Latin Quarter Walk", "description": "Explore Goa's Portuguese heritage. Colorful houses and quiet lanes.", "locality_label": "Panjim", "tags": ["culture", "walk", "history"], "place_type": "Neighborhood walk", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Dona Paula Viewpoint", "description": "Scenic viewpoint where two rivers meet the sea. Peaceful and romantic.", "locality_label": "Dona Paula", "tags": ["scenic", "romantic", "peaceful"], "place_type": "Viewpoint", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Anjuna Flea Market", "description": "Wednesday market with everything. Hippie vibes and unique finds.", "locality_label": "Anjuna", "tags": ["shopping", "culture", "fun"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Old Goa Churches", "description": "UNESCO World Heritage churches. Beautiful architecture and history.", "locality_label": "Old Goa", "tags": ["history", "architecture", "culture"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Calangute Beach Walk", "description": "Popular beach with shacks and activities. Busy but fun.", "locality_label": "Calangute", "tags": ["beach", "fun", "popular"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Palolem Beach Day", "description": "Crescent-shaped beach in South Goa. Calmer and more scenic.", "locality_label": "Palolem", "tags": ["beach", "scenic", "relaxed"], "place_type": "Beach", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Chapora Fort Sunset", "description": "Famous Dil Chahta Hai fort. Great views and sunset vibes.", "locality_label": "Chapora", "tags": ["scenic", "history", "iconic"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Reis Magos Fort", "description": "Lesser-known but beautiful fort with river views.", "locality_label": "Reis Magos", "tags": ["history", "scenic", "peaceful"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Panjim Waterfront Walk", "description": "Walk along the Mandovi River. Church, casino views, and cafes.", "locality_label": "Panjim", "tags": ["waterfront", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
    ],
    "Kochi": [
        {"title": "Fort Kochi Promenade", "description": "Walk through colonial streets. Portuguese, Dutch, and British heritage.", "locality_label": "Fort Kochi", "tags": ["history", "walk", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "2-4h"},
        {"title": "Chinese Fishing Nets Sunset", "description": "Iconic Kochi landmark. Watch fishermen at work during golden hour.", "locality_label": "Fort Kochi", "tags": ["scenic", "iconic", "culture"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Marine Drive Walk", "description": "Waterfront promenade in the city. Evening lights and good food.", "locality_label": "Marine Drive", "tags": ["waterfront", "walk", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Mattancherry Palace Area", "description": "Dutch Palace with murals, then explore the spice markets.", "locality_label": "Mattancherry", "tags": ["history", "culture", "local"], "place_type": "Monument", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Kochi Biennale Art Walk", "description": "During biennale, or anytime - Fort Kochi galleries and street art.", "locality_label": "Fort Kochi", "tags": ["art", "culture", "walk"], "place_type": "Gallery", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Jew Town & Synagogue", "description": "Historic area with antique shops and India's oldest synagogue.", "locality_label": "Mattancherry", "tags": ["history", "shopping", "culture"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Princess Street Cafe Walk", "description": "Charming street with cafes in heritage buildings.", "locality_label": "Fort Kochi", "tags": ["coffee", "culture", "walk"], "place_type": "Neighborhood walk", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Bolgatty Island", "description": "Short ferry ride to peaceful island with palace and gardens.", "locality_label": "Bolgatty", "tags": ["nature", "peaceful", "adventure"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Cherai Beach Day Trip", "description": "Less crowded beach near Kochi. Good for a relaxed day out.", "locality_label": "Cherai", "tags": ["beach", "relaxed", "nature"], "place_type": "Beach", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Sunset Cruise Backwaters", "description": "Short backwater cruise at sunset. Peaceful and beautiful.", "locality_label": "Ernakulam", "tags": ["scenic", "romantic", "adventure"], "place_type": "Waterfront", "safety_level": "Public & Calm", "cost_hint": "$$", "duration_hint": "2-4h"},
    ],
    "Chandigarh": [
        {"title": "Sukhna Lake Stroll", "description": "Beautiful artificial lake. Morning walks, boating, and peaceful vibes.", "locality_label": "Sukhna Lake", "tags": ["waterfront", "peaceful", "scenic"], "place_type": "Waterfront", "safety_level": "Public & Busy", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Rock Garden Tour", "description": "Unique sculpture garden made from industrial waste. Must-see Chandigarh.", "locality_label": "Rock Garden", "tags": ["art", "unique", "culture"], "place_type": "Garden", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Sector 17 Plaza Meet", "description": "The city center. Shopping, restaurants, and evening energy.", "locality_label": "Sector 17", "tags": ["shopping", "food", "walk"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Rose Garden Morning", "description": "Asia's largest rose garden. 50,000 roses in blooming season.", "locality_label": "Sector 16", "tags": ["garden", "nature", "romantic"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Capitol Complex", "description": "Le Corbusier's UNESCO masterpiece. Book advance if visiting buildings.", "locality_label": "Capitol Complex", "tags": ["architecture", "culture", "unique"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "1-2h"},
        {"title": "Elante Mall & Surrounds", "description": "Modern mall with entertainment and dining options.", "locality_label": "Industrial Area", "tags": ["shopping", "food", "modern"], "place_type": "Mall", "safety_level": "Public & Busy", "cost_hint": "$$", "duration_hint": "2-4h"},
        {"title": "Leisure Valley Walk", "description": "Chain of gardens running through the city. Green and peaceful.", "locality_label": "Various Sectors", "tags": ["outdoors", "walk", "peaceful"], "place_type": "Park", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "1-2h"},
        {"title": "Pinjore Gardens Day Trip", "description": "Beautiful Mughal gardens nearby. Fountains and terraced gardens.", "locality_label": "Pinjore", "tags": ["garden", "history", "scenic"], "place_type": "Garden", "safety_level": "Public & Calm", "cost_hint": "$", "duration_hint": "2-4h"},
        {"title": "Open Hand Monument", "description": "Iconic Le Corbusier sculpture. Symbol of the city.", "locality_label": "Capitol Complex", "tags": ["art", "architecture", "iconic"], "place_type": "Monument", "safety_level": "Public & Calm", "cost_hint": "Free", "duration_hint": "30-60m"},
        {"title": "Sector 26 Food Street", "description": "Chandigarh's food hub. Street food and restaurants.", "locality_label": "Sector 26", "tags": ["food", "local", "evening"], "place_type": "Market", "safety_level": "Public & Busy", "cost_hint": "$", "duration_hint": "1-2h"},
    ],
}
# ==================== TEMPLATES API ====================
# Routes for Date Idea Templates

# Templates already defined above

# Helper to normalize city names
CITY_NAME_MAP = {
    "nyc": "New York City", "new york": "New York City", "new york city": "New York City",
    "la": "Los Angeles", "los angeles": "Los Angeles",
    "sf": "San Francisco", "san francisco": "San Francisco",
    "dc": "Washington DC", "washington dc": "Washington DC", "washington d.c.": "Washington DC",
    "chicago": "Chicago", "boston": "Boston", "seattle": "Seattle", "austin": "Austin",
    "miami": "Miami", "houston": "Houston", "dallas": "Dallas", "atlanta": "Atlanta",
    "denver": "Denver", "san diego": "San Diego", "philadelphia": "Philadelphia",
    "mumbai": "Mumbai", "delhi": "Delhi", "new delhi": "Delhi",
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru",
    "hyderabad": "Hyderabad", "chennai": "Chennai", "kolkata": "Kolkata",
    "pune": "Pune", "ahmedabad": "Ahmedabad", "jaipur": "Jaipur",
    "goa": "Goa", "kochi": "Kochi", "chandigarh": "Chandigarh",
}

def normalize_city(city: str) -> str:
    if not city:
        return None
    return CITY_NAME_MAP.get(city.lower().strip(), city.title())

@api_router.get("/templates")
async def get_templates(
    city: Optional[str] = None,
    tags: Optional[str] = None,
    place_type: Optional[str] = None,
    safety_level: Optional[str] = None,
    cost_hint: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get date idea templates - global + city-specific"""
    results = []
    
    # Add global templates
    for idx, template in enumerate(DATE_IDEA_TEMPLATES_GLOBAL):
        t = {
            "id": f"global_{idx}",
            "city": None,
            "is_global": True,
            **template
        }
        results.append(t)
    
    # Add city-specific templates
    normalized_city = normalize_city(city) if city else None
    
    if normalized_city and normalized_city in CITY_TEMPLATES:
        for idx, template in enumerate(CITY_TEMPLATES[normalized_city]):
            t = {
                "id": f"{normalized_city.lower().replace(' ', '_')}_{idx}",
                "city": normalized_city,
                "is_global": False,
                **template
            }
            results.append(t)
    
    # Apply filters
    if tags:
        tag_list = tags.lower().split(',')
        results = [r for r in results if any(t.lower() in r.get('tags', []) for t in tag_list)]
    
    if place_type:
        results = [r for r in results if r.get('place_type', '').lower() == place_type.lower()]
    
    if safety_level:
        results = [r for r in results if r.get('safety_level', '').lower() == safety_level.lower()]
    
    if cost_hint:
        results = [r for r in results if r.get('cost_hint', '').lower() == cost_hint.lower()]
    
    if search:
        search_lower = search.lower()
        results = [r for r in results if search_lower in r.get('title', '').lower() or search_lower in r.get('description', '').lower()]
    
    # Separate global and city templates
    global_templates = [r for r in results if r.get('is_global')]
    city_templates = [r for r in results if not r.get('is_global')]
    
    return {
        "templates": results[:limit],
        "global_count": len(global_templates),
        "city_count": len(city_templates),
        "total": len(results),
        "available_cities": list(CITY_TEMPLATES.keys())
    }

@api_router.get("/templates/cities")
async def get_available_cities():
    """Get list of cities with templates"""
    cities = []
    for city in CITY_TEMPLATES.keys():
        coords = get_city_coords(city.lower())
        cities.append({
            "name": city,
            "template_count": len(CITY_TEMPLATES[city]),
            "country": coords.get('country', 'Unknown') if coords else 'Unknown'
        })
    return {"cities": sorted(cities, key=lambda x: x['name'])}

@api_router.get("/templates/suggest")
async def suggest_templates(
    tags: Optional[str] = None,
    city: Optional[str] = None,
    surprise_me: bool = False,
    limit: int = Query(10, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """Smart template suggestions based on preferences"""
    profile = await db.profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    user_city = normalize_city(city or (profile.get('city') if profile else None))
    user_tags = tags.split(',') if tags else (profile.get('date_preferences', []) if profile else [])
    
    all_templates = []
    
    # Add global templates
    for idx, template in enumerate(DATE_IDEA_TEMPLATES_GLOBAL):
        all_templates.append({
            "id": f"global_{idx}",
            "city": None,
            "is_global": True,
            **template
        })
    
    # Add user's city templates
    if user_city and user_city in CITY_TEMPLATES:
        for idx, template in enumerate(CITY_TEMPLATES[user_city]):
            all_templates.append({
                "id": f"{user_city.lower().replace(' ', '_')}_{idx}",
                "city": user_city,
                "is_global": False,
                **template
            })
    
    if surprise_me:
        # Return random safe templates
        import random
        safe_templates = [t for t in all_templates if 'Public & Busy' in t.get('safety_level', '')]
        random.shuffle(safe_templates)
        return {"suggestions": safe_templates[:limit], "method": "surprise"}
    
    # Score templates based on tag overlap
    scored = []
    for template in all_templates:
        score = 0
        template_tags = [t.lower() for t in template.get('tags', [])]
        
        # Tag overlap
        for tag in user_tags:
            if tag.lower() in template_tags:
                score += 3
        
        # City match bonus
        if template.get('city') == user_city:
            score += 5
        
        # Safety bonus
        if 'Public & Busy' in template.get('safety_level', ''):
            score += 2
        elif 'Public & Calm' in template.get('safety_level', ''):
            score += 1
        
        scored.append((score, template))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    suggestions = [t for _, t in scored[:limit]]
    
    return {"suggestions": suggestions, "method": "scored", "user_city": user_city}

@api_router.post("/templates/{template_id}/favorite")
async def favorite_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Save a template to favorites"""
    existing = await db.favorite_templates.find_one({
        "user_id": current_user['id'],
        "template_id": template_id
    })
    if existing:
        # Unfavorite
        await db.favorite_templates.delete_one({"id": existing['id']})
        return {"message": "Removed from favorites", "favorited": False}
    
    favorite = {
        "id": str(uuid.uuid4()),
        "user_id": current_user['id'],
        "template_id": template_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.favorite_templates.insert_one(favorite)
    return {"message": "Added to favorites", "favorited": True}

@api_router.get("/templates/favorites")
async def get_favorite_templates(current_user: dict = Depends(get_current_user)):
    """Get user's favorite templates"""
    favorites = await db.favorite_templates.find(
        {"user_id": current_user['id']}, {"_id": 0}
    ).to_list(100)
    
    template_ids = [f['template_id'] for f in favorites]
    
    # Reconstruct template data
    templates = []
    for template_id in template_ids:
        if template_id.startswith('global_'):
            idx = int(template_id.replace('global_', ''))
            if idx < len(DATE_IDEA_TEMPLATES_GLOBAL):
                templates.append({
                    "id": template_id,
                    "is_global": True,
                    **DATE_IDEA_TEMPLATES_GLOBAL[idx]
                })
        else:
            # City template
            parts = template_id.rsplit('_', 1)
            if len(parts) == 2:
                city_key = parts[0].replace('_', ' ').title()
                idx = int(parts[1])
                if city_key in CITY_TEMPLATES and idx < len(CITY_TEMPLATES[city_key]):
                    templates.append({
                        "id": template_id,
                        "city": city_key,
                        "is_global": False,
                        **CITY_TEMPLATES[city_key][idx]
                    })
    
    return {"favorites": templates}

# ==================== ADMIN ROUTES ====================

@api_router.get("/admin/verifications")
async def admin_get_verifications(
    status: Optional[str] = "PENDING",
    type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get verification submissions for review"""
    query = {}
    if status:
        query['status'] = status
    if type:
        query['type'] = type
    
    submissions = await db.verification_submissions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Add user info
    for sub in submissions:
        user = await db.users.find_one({"id": sub['user_id']}, {"_id": 0, "email": 1})
        profile = await db.profiles.find_one({"user_id": sub['user_id']}, {"_id": 0, "first_name": 1, "main_photo": 1})
        sub['user_email'] = user.get('email') if user else None
        sub['user_name'] = profile.get('first_name') if profile else None
        sub['user_photo'] = profile.get('main_photo') if profile else None
    
    return {"submissions": submissions}

@api_router.put("/admin/verifications/{submission_id}")
async def admin_review_verification(
    submission_id: str,
    data: AdminVerificationAction,
    admin_user: dict = Depends(get_admin_user)
):
    """Approve or reject a verification submission"""
    submission = await db.verification_submissions.find_one({"id": submission_id}, {"_id": 0})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.verification_submissions.update_one(
        {"id": submission_id},
        {"$set": {
            "status": data.status,
            "admin_notes": data.notes,
            "reviewed_by": admin_user['id'],
            "reviewed_at": now
        }}
    )
    
    # Update user verification status if approved
    if data.status == "APPROVED":
        update_field = f"{submission['type']}_verified"
        await db.users.update_one(
            {"id": submission['user_id']},
            {"$set": {update_field: True}}
        )
    
    # Log moderation action
    await db.moderation_actions.insert_one({
        "id": str(uuid.uuid4()),
        "admin_id": admin_user['id'],
        "target_user_id": submission['user_id'],
        "action_type": f"verification_{data.status.lower()}",
        "details": {"submission_id": submission_id, "type": submission['type'], "notes": data.notes},
        "created_at": now
    })
    
    return {"message": f"Verification {data.status.lower()}", "submission_id": submission_id}

@api_router.get("/admin/reports")
async def admin_get_reports(
    status: Optional[str] = "pending",
    reason: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get user reports for review"""
    query = {}
    if status:
        query['status'] = status
    if reason:
        query['reason'] = reason
    
    reports = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Add user info
    for report in reports:
        reporter = await db.users.find_one({"id": report['reporter_id']}, {"_id": 0, "email": 1})
        reporter_profile = await db.profiles.find_one({"user_id": report['reporter_id']}, {"_id": 0, "first_name": 1})
        reported = await db.users.find_one({"id": report['reported_user_id']}, {"_id": 0, "email": 1, "status": 1, "shadow_banned": 1})
        reported_profile = await db.profiles.find_one({"user_id": report['reported_user_id']}, {"_id": 0, "first_name": 1, "main_photo": 1})
        
        report['reporter_email'] = reporter.get('email') if reporter else None
        report['reporter_name'] = reporter_profile.get('first_name') if reporter_profile else None
        report['reported_email'] = reported.get('email') if reported else None
        report['reported_name'] = reported_profile.get('first_name') if reported_profile else None
        report['reported_photo'] = reported_profile.get('main_photo') if reported_profile else None
        report['reported_status'] = reported.get('status') if reported else None
        report['reported_shadow_banned'] = reported.get('shadow_banned') if reported else None
    
    return {"reports": reports}

@api_router.put("/admin/reports/{report_id}")
async def admin_review_report(
    report_id: str,
    status: str = Query(...),  # reviewed, action_taken, dismissed
    notes: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """Update report status"""
    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.reports.update_one(
        {"id": report_id},
        {"$set": {
            "status": status,
            "admin_notes": notes,
            "reviewed_by": admin_user['id'],
            "reviewed_at": now
        }}
    )
    
    return {"message": "Report updated", "report_id": report_id}

@api_router.get("/admin/users/{user_id}")
async def admin_get_user(user_id: str, admin_user: dict = Depends(get_admin_user)):
    """Get detailed user info for admin"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
    reports_against = await db.reports.count_documents({"reported_user_id": user_id})
    reports_made = await db.reports.count_documents({"reporter_id": user_id})
    verifications = await db.verification_submissions.find({"user_id": user_id}, {"_id": 0}).to_list(10)
    moderation_history = await db.moderation_actions.find({"target_user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(20)
    
    return {
        "user": user,
        "profile": profile,
        "reports_against": reports_against,
        "reports_made": reports_made,
        "verifications": verifications,
        "moderation_history": moderation_history
    }

@api_router.post("/admin/users/{user_id}/action")
async def admin_user_action(
    user_id: str,
    data: AdminUserAction,
    admin_user: dict = Depends(get_admin_user)
):
    """Take moderation action on a user"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.now(timezone.utc).isoformat()
    update_data = {}
    
    if data.action == "warn":
        # Just log the warning
        pass
    elif data.action == "restrict_messaging":
        update_data['status'] = 'limited'
    elif data.action == "shadow_ban":
        update_data['shadow_banned'] = True
    elif data.action == "suspend":
        update_data['status'] = 'suspended'
    elif data.action == "unsuspend":
        update_data['status'] = 'active'
        update_data['shadow_banned'] = False
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Log action
    await db.moderation_actions.insert_one({
        "id": str(uuid.uuid4()),
        "admin_id": admin_user['id'],
        "target_user_id": user_id,
        "action_type": data.action,
        "reason": data.reason,
        "created_at": now
    })
    
    return {"message": f"Action '{data.action}' taken on user", "user_id": user_id}

@api_router.get("/admin/audit-log")
async def admin_audit_log(
    action_type: Optional[str] = None,
    admin_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    admin_user: dict = Depends(get_admin_user)
):
    """Get moderation audit log"""
    query = {}
    if action_type:
        query['action_type'] = action_type
    if admin_id:
        query['admin_id'] = admin_id
    
    actions = await db.moderation_actions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Add admin names
    for action in actions:
        admin = await db.users.find_one({"id": action['admin_id']}, {"_id": 0, "email": 1})
        action['admin_email'] = admin.get('email') if admin else None
    
    return {"actions": actions}

@api_router.get("/admin/stats")
async def admin_stats(admin_user: dict = Depends(get_admin_user)):
    """Get admin dashboard stats"""
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(hours=24)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    
    stats = {
        "total_users": await db.users.count_documents({}),
        "new_users_24h": await db.users.count_documents({"created_at": {"$gte": day_ago}}),
        "new_users_7d": await db.users.count_documents({"created_at": {"$gte": week_ago}}),
        "total_matches": await db.matches.count_documents({}),
        "pending_verifications": await db.verification_submissions.count_documents({"status": "PENDING"}),
        "pending_reports": await db.reports.count_documents({"status": "pending"}),
        "suspended_users": await db.users.count_documents({"status": "suspended"}),
        "shadow_banned_users": await db.users.count_documents({"shadow_banned": True}),
        "limited_users": await db.users.count_documents({"status": "limited"}),
        "verified_users_email": await db.users.count_documents({"email_verified": True}),
        "verified_users_photo": await db.users.count_documents({"photo_verified": True}),
        "verified_users_phone": await db.users.count_documents({"phone_verified": True}),
    }
    
    return stats

@api_router.get("/admin/feedback-analytics")
async def admin_feedback_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_user: dict = Depends(get_admin_user)
):
    """Get aggregated date feedback analytics"""
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()
    
    # Get all feedback in the time period
    feedbacks = await db.date_feedback.find(
        {"created_at": {"$gte": since}},
        {"_id": 0}
    ).to_list(10000)
    
    if not feedbacks:
        return {
            "total_feedbacks": 0,
            "avg_overall_rating": 0,
            "avg_safety_rating": 0,
            "avg_accuracy_rating": 0,
            "recommend_rate": 0,
            "tag_counts": {},
            "rating_distribution": {},
            "recent_feedbacks": []
        }
    
    total = len(feedbacks)
    avg_overall = sum(f.get('overall_rating', 0) for f in feedbacks) / total
    avg_safety = sum(f.get('safety_rating', 0) for f in feedbacks) / total
    avg_accuracy = sum(f.get('accuracy_rating', 0) for f in feedbacks) / total
    recommend_count = sum(1 for f in feedbacks if f.get('would_recommend', False))
    recommend_rate = (recommend_count / total) * 100
    
    # Count tags
    tag_counts = {}
    for f in feedbacks:
        for tag in f.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Rating distribution (1-5 stars)
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for f in feedbacks:
        rating = f.get('overall_rating', 0)
        if 1 <= rating <= 5:
            rating_distribution[rating] += 1
    
    # Get recent feedbacks with user details
    recent = sorted(feedbacks, key=lambda x: x.get('created_at', ''), reverse=True)[:20]
    recent_feedbacks = []
    for f in recent:
        reviewer = await db.profiles.find_one({"user_id": f.get('reviewer_id')}, {"_id": 0, "first_name": 1})
        reviewed = await db.profiles.find_one({"user_id": f.get('reviewed_user_id')}, {"_id": 0, "first_name": 1})
        recent_feedbacks.append({
            "id": f.get('id'),
            "reviewer_name": reviewer.get('first_name') if reviewer else 'Unknown',
            "reviewed_name": reviewed.get('first_name') if reviewed else 'Unknown',
            "overall_rating": f.get('overall_rating'),
            "safety_rating": f.get('safety_rating'),
            "would_recommend": f.get('would_recommend'),
            "tags": f.get('tags', []),
            "feedback_text": f.get('feedback_text', '')[:100],
            "created_at": f.get('created_at')
        })
    
    # Identify users with concerning feedback (avg safety < 3 with 2+ feedbacks)
    user_safety_scores = {}
    for f in feedbacks:
        user_id = f.get('reviewed_user_id')
        if user_id:
            if user_id not in user_safety_scores:
                user_safety_scores[user_id] = []
            user_safety_scores[user_id].append(f.get('safety_rating', 5))
    
    flagged_users = []
    for user_id, scores in user_safety_scores.items():
        if len(scores) >= 2:
            avg_score = sum(scores) / len(scores)
            if avg_score < 3:
                profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0, "first_name": 1, "main_photo": 1})
                flagged_users.append({
                    "user_id": user_id,
                    "name": profile.get('first_name') if profile else 'Unknown',
                    "photo": profile.get('main_photo') if profile else None,
                    "avg_safety_rating": round(avg_score, 1),
                    "feedback_count": len(scores)
                })
    
    return {
        "total_feedbacks": total,
        "avg_overall_rating": round(avg_overall, 2),
        "avg_safety_rating": round(avg_safety, 2),
        "avg_accuracy_rating": round(avg_accuracy, 2),
        "recommend_rate": round(recommend_rate, 1),
        "tag_counts": tag_counts,
        "rating_distribution": rating_distribution,
        "recent_feedbacks": recent_feedbacks,
        "flagged_users": flagged_users,
        "period_days": days
    }

# ==================== HEALTH & SEED ====================

@api_router.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "features": ["safety", "verification", "templates"]}

# Include the router
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

# Export the socket-wrapped app for uvicorn
# Use: uvicorn server:socket_app --host 0.0.0.0 --port 8001
# Or for FastAPI only: uvicorn server:app --host 0.0.0.0 --port 8001
