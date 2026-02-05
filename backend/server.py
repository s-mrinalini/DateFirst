from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

app = FastAPI(title="DateFirst API v3 - Safety Enhanced")
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
    
    # In production, send email with verification code
    logger.info(f"Email verification code for {data.email}: {verification_code}")
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "profile_complete": False,
            "email_verified": False
        },
        "message": f"Please verify your email. Code: {verification_code}"  # Remove in production
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
    
    logger.info(f"New verification code for {current_user['email']}: {verification_code}")
    return {"message": f"Verification code sent. Code: {verification_code}"}  # Remove in production

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
    """Start phone verification - sends OTP (mock for MVP)"""
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
    
    # TODO: In production, integrate with SMS provider (Twilio, etc.)
    logger.info(f"Phone OTP for {current_user['id']}: {otp}")
    
    return {"message": f"OTP sent to {data.phone_number}. Code: {otp}"}  # Remove code in production

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
    my_likes = await db.likes.find({"liker_id": current_user['id']}, {"_id": 0}).to_list(1000)
    liked_ids = [like['liked_id'] for like in my_likes]
    
    my_matches = await db.matches.find({
        "$or": [{"user1_id": current_user['id']}, {"user2_id": current_user['id']}]
    }, {"_id": 0}).to_list(1000)
    matched_ids = []
    for m in my_matches:
        matched_ids.append(m['user1_id'] if m['user2_id'] == current_user['id'] else m['user2_id'])
    
    exclude_ids = set(blocked_ids + liked_ids + matched_ids + [current_user['id']])
    
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
    
    summary = f"""
Date Plan Summary for {my_profile.get('first_name', 'User')}

Meeting: {other_name}
When: {date_plan.get('proposed_datetime', 'Not set')}
Where: {date_plan.get('proposed_location', 'Not set')}

Safety Tips:
- Meet in a public place
- Tell someone when you arrive and leave
- Trust your instincts

This message was shared via DateFirst Safety Center.
"""
    
    # TODO: In production, send email to contact
    logger.info(f"Sharing date plan with {contact['email']}")
    
    return {
        "message": f"Date plan shared with {contact['name']}",
        "summary": summary
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
