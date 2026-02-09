"""
Utility functions for DateFirst API
"""
import re
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Any, Optional
from better_profanity import profanity

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
