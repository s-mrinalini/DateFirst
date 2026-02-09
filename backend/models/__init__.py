"""
Pydantic models for DateFirst API
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime, date


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


class PassCreate(BaseModel):
    passed_user_id: str


class DateFeedbackCreate(BaseModel):
    thread_id: str
    overall_rating: int = Field(..., ge=1, le=5)  # 1-5 stars
    safety_rating: int = Field(..., ge=1, le=5)  # How safe did you feel?
    accuracy_rating: int = Field(..., ge=1, le=5)  # Did the date match the idea?
    would_recommend: bool = True
    feedback_text: Optional[str] = None
    tags: List[str] = []  # "great_conversation", "felt_safe", "punctual", "respectful", etc.


class FileUploadResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None
