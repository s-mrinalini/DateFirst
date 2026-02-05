"""
DateFirst v3 - Comprehensive Seed Script
Seeds 12 users, 60+ templates, likes, matches, chats, verifications, and reports for testing.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import uuid
from argon2 import PasswordHasher
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

ph = PasswordHasher()

async def seed():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🌱 Starting DateFirst v3 seed...")
    
    # Clear existing data
    collections = ['users', 'profiles', 'likes', 'matches', 'chat_threads', 'chat_messages', 
                   'blocks', 'reports', 'verification_submissions', 'moderation_actions',
                   'trusted_contacts', 'safety_checkins', 'sessions', 'rate_limit_events',
                   'favorite_templates']
    for coll in collections:
        await db[coll].delete_many({})
    print("✓ Cleared existing data")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Create admin user
    admin_id = str(uuid.uuid4())
    admin = {
        "id": admin_id,
        "email": "admin@datefirst.app",
        "password_hash": ph.hash("admin123"),
        "profile_complete": True,
        "email_verified": True,
        "photo_verified": True,
        "phone_verified": True,
        "id_verified": False,
        "status": "active",
        "shadow_banned": False,
        "is_admin": True,
        "created_at": now
    }
    await db.users.insert_one(admin)
    print("✓ Created admin user: admin@datefirst.app / admin123")
    
    # User data - 12 users across 3 cities (Austin, NYC, Mumbai)
    users_data = [
        # Austin Users (4)
        {"first_name": "Emma", "email": "emma@example.com", "gender": "female", "interested_in": ["male"], 
         "city": "Austin", "bio": "Coffee lover and adventure seeker. Love trying new cafes and spontaneous road trips.", 
         "height": "5'6\"", "dob": "1996-05-15", "tags": ["coffee", "outdoors", "adventure"],
         "idea": {"title": "Coffee + Bookstore Wander", "description": "Let's grab artisan coffee and browse a cozy indie bookstore. I love discovering hidden literary gems!", "tags": ["coffee", "chill", "books"], "city": "Austin", "is_public_meetup": True, "suggested_meetup": "BookPeople entrance"},
         "verified": {"email": True, "photo": True, "phone": False},
         "lat": 30.2672, "lng": -97.7431},
        
        {"first_name": "James", "email": "james@example.com", "gender": "male", "interested_in": ["female"], 
         "city": "Austin", "bio": "Foodie and amateur chef. Always hunting for the best tacos in town.", 
         "height": "5'11\"", "dob": "1993-08-22", "tags": ["dinner", "cooking", "music"],
         "idea": {"title": "Taco Crawl Adventure", "description": "I know all the best taco spots! Let's hit 3 places and rate them together. Bonus points if you love hot sauce.", "tags": ["food", "adventure", "casual"], "city": "Austin", "is_public_meetup": True, "suggested_meetup": "South Congress starting point"},
         "verified": {"email": True, "photo": True, "phone": True},
         "lat": 30.2672, "lng": -97.7431},
        
        {"first_name": "Olivia", "email": "olivia@example.com", "gender": "female", "interested_in": ["male"], 
         "city": "Austin", "bio": "Wine sommelier in training. Love a good conversation over great wine.", 
         "height": "5'7\"", "dob": "1994-07-28", "tags": ["wine", "dinner", "conversation"],
         "idea": {"title": "Wine Tasting Journey", "description": "I'll teach you about wine pairings at my favorite vineyard. No pretentiousness, just good vibes.", "tags": ["wine", "chill", "romantic"], "city": "Austin", "is_public_meetup": True, "suggested_meetup": "Vineyard entrance"},
         "verified": {"email": True, "photo": False, "phone": False},
         "lat": 30.2672, "lng": -97.7431},
        
        {"first_name": "Ethan", "email": "ethan@example.com", "gender": "male", "interested_in": ["female"], 
         "city": "Austin", "bio": "Tech by day, musician by night. Looking for someone to jam with (literally or figuratively).", 
         "height": "5'10\"", "dob": "1995-12-10", "tags": ["music", "coffee", "creative"],
         "idea": {"title": "Live Music Discovery", "description": "Austin has the best live music scene. Let's find a hidden gem venue and discover our new favorite band.", "tags": ["music", "nightlife", "adventure"], "city": "Austin", "is_public_meetup": True, "suggested_meetup": "6th Street meeting point"},
         "verified": {"email": True, "photo": True, "phone": False},
         "lat": 30.2672, "lng": -97.7431},
        
        # NYC Users (4)
        {"first_name": "Sofia", "email": "sofia@example.com", "gender": "female", "interested_in": ["male"], 
         "city": "New York City", "bio": "Art enthusiast and museum nerd. Could spend hours in a gallery.", 
         "height": "5'4\"", "dob": "1997-11-03", "tags": ["museum", "art", "coffee"],
         "idea": {"title": "MoMA + Coffee Chat", "description": "Let's hit the highlights at MoMA and debate which pieces we love (and hate). Coffee after to discuss.", "tags": ["art", "culture", "coffee"], "city": "New York City", "is_public_meetup": True, "suggested_meetup": "MoMA main entrance"},
         "verified": {"email": True, "photo": True, "phone": True},
         "lat": 40.7128, "lng": -74.0060},
        
        {"first_name": "Michael", "email": "michael@example.com", "gender": "male", "interested_in": ["female"], 
         "city": "New York City", "bio": "Weekend hiker and nature photographer. The outdoors is my happy place.", 
         "height": "6'0\"", "dob": "1992-02-14", "tags": ["hiking", "outdoors", "photography"],
         "idea": {"title": "Central Park Sunrise Walk", "description": "Early bird? Let's catch the city waking up with a walk through Central Park. Hot chocolate stop mandatory.", "tags": ["outdoors", "active", "romantic"], "city": "New York City", "is_public_meetup": True, "suggested_meetup": "Central Park entrance at 72nd St"},
         "verified": {"email": True, "photo": False, "phone": False},
         "lat": 40.7128, "lng": -74.0060},
        
        {"first_name": "Isabella", "email": "isabella@example.com", "gender": "female", "interested_in": ["male"], 
         "city": "New York City", "bio": "Travel blogger saving for the next adventure. Obsessed with farmers markets and vintage finds.", 
         "height": "5'3\"", "dob": "1996-01-17", "tags": ["travel", "outdoors", "vintage"],
         "idea": {"title": "Brooklyn Flea Adventure", "description": "Let's hunt for vintage treasures and sample local food. I'll share my best haggling tips.", "tags": ["shopping", "food", "adventure"], "city": "New York City", "is_public_meetup": True, "suggested_meetup": "Brooklyn Flea entrance"},
         "verified": {"email": True, "photo": True, "phone": False},
         "lat": 40.7128, "lng": -74.0060},
        
        {"first_name": "Liam", "email": "liam@example.com", "gender": "male", "interested_in": ["female"], 
         "city": "New York City", "bio": "Board game collector and craft beer enthusiast. Competitive but fun!", 
         "height": "5'9\"", "dob": "1994-04-30", "tags": ["games", "beer", "fun"],
         "idea": {"title": "Board Game Café Battle", "description": "I'll teach you my favorite strategy games over craft beers. Warning: I'm annoyingly competitive.", "tags": ["games", "chill", "fun"], "city": "New York City", "is_public_meetup": True, "suggested_meetup": "Hex & Company entrance"},
         "verified": {"email": True, "photo": True, "phone": True},
         "lat": 40.7128, "lng": -74.0060},
        
        # Mumbai Users (4)
        {"first_name": "Priya", "email": "priya@example.com", "gender": "female", "interested_in": ["male"], 
         "city": "Mumbai", "bio": "Finance professional who loves chai and sunsets. Looking for meaningful connections.", 
         "height": "5'5\"", "dob": "1995-09-20", "tags": ["chai", "outdoors", "conversation"],
         "idea": {"title": "Marine Drive Sunset Chai", "description": "Let's watch the sunset at Marine Drive with cutting chai. The Queen's Necklace lights up beautifully after dark.", "tags": ["scenic", "romantic", "chai"], "city": "Mumbai", "is_public_meetup": True, "suggested_meetup": "Marine Drive near NCPA"},
         "verified": {"email": True, "photo": True, "phone": True},
         "lat": 19.0760, "lng": 72.8777},
        
        {"first_name": "Arjun", "email": "arjun@example.com", "gender": "male", "interested_in": ["female"], 
         "city": "Mumbai", "bio": "Startup founder, history buff. Love exploring old Mumbai and finding hidden stories.", 
         "height": "5'10\"", "dob": "1991-03-15", "tags": ["history", "food", "culture"],
         "idea": {"title": "Fort Area Heritage Walk", "description": "I'll show you the hidden architectural gems of Fort. End with Parsi food at my favorite Irani café.", "tags": ["history", "culture", "food"], "city": "Mumbai", "is_public_meetup": True, "suggested_meetup": "Churchgate Station entrance"},
         "verified": {"email": True, "photo": False, "phone": False},
         "lat": 19.0760, "lng": 72.8777},
        
        {"first_name": "Ananya", "email": "ananya@example.com", "gender": "female", "interested_in": ["male"], 
         "city": "Mumbai", "bio": "Yoga instructor by morning, foodie by night. Balance is everything!", 
         "height": "5'4\"", "dob": "1998-06-08", "tags": ["yoga", "food", "wellness"],
         "idea": {"title": "Yoga + Brunch Combo", "description": "Morning yoga at Juhu beach followed by the best South Indian breakfast. Namaste and dosa!", "tags": ["fitness", "food", "morning"], "city": "Mumbai", "is_public_meetup": True, "suggested_meetup": "Juhu Beach yoga spot"},
         "verified": {"email": True, "photo": True, "phone": False},
         "lat": 19.0760, "lng": 72.8777},
        
        {"first_name": "Rohan", "email": "rohan@example.com", "gender": "male", "interested_in": ["female"], 
         "city": "Mumbai", "bio": "Film critic and Bollywood nerd. Can debate movies for hours.", 
         "height": "6'1\"", "dob": "1993-11-25", "tags": ["movies", "coffee", "culture"],
         "idea": {"title": "Art Deco Cinema Walk", "description": "Mumbai has beautiful old cinemas. Let's explore the art deco architecture and catch a classic screening.", "tags": ["culture", "movies", "walk"], "city": "Mumbai", "is_public_meetup": True, "suggested_meetup": "Metro Cinema entrance"},
         "verified": {"email": True, "photo": True, "phone": True},
         "lat": 19.0760, "lng": 72.8777},
    ]
    
    photos = [
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400",
        "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400",
        "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400",
    ]
    
    users = []
    for i, u in enumerate(users_data):
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": u['email'],
            "password_hash": ph.hash("password123"),
            "profile_complete": True,
            "email_verified": u['verified']['email'],
            "photo_verified": u['verified']['photo'],
            "phone_verified": u['verified']['phone'],
            "id_verified": False,
            "status": "active",
            "shadow_banned": False,
            "is_admin": False,
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
            "latitude": u['lat'],
            "longitude": u['lng'],
            "precise_location": False,
            "created_at": now
        }
        await db.profiles.insert_one(profile)
    
    print(f"✓ Created {len(users)} users")
    
    # Create matches (3 pairs)
    matches_to_create = [
        (0, 1),  # Emma <-> James (Austin)
        (4, 5),  # Sofia <-> Michael (NYC)
        (8, 9),  # Priya <-> Arjun (Mumbai)
    ]
    
    for u1_idx, u2_idx in matches_to_create:
        u1, u2 = users[u1_idx], users[u2_idx]
        
        # Create mutual likes
        await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": u1['id'], "liked_id": u2['id'], "created_at": now})
        await db.likes.insert_one({"id": str(uuid.uuid4()), "liker_id": u2['id'], "liked_id": u1['id'], "created_at": now})
        
        # Create match
        match_id = str(uuid.uuid4())
        await db.matches.insert_one({
            "id": match_id,
            "user1_id": u1['id'],
            "user2_id": u2['id'],
            "created_at": now
        })
        
        # Create chat thread
        thread_id = str(uuid.uuid4())
        thread = {
            "id": thread_id,
            "match_id": match_id,
            "user1_id": u1['id'],
            "user2_id": u2['id'],
            "user1_name": u1['first_name'],
            "user2_name": u2['first_name'],
            "user1_photo": photos[u1_idx],
            "user2_photo": photos[u2_idx],
            "matched_on_idea": u2['idea'],
            "date_plan": {
                "proposed_datetime": None,
                "proposed_location": None,
                "who_pays": None,
                "is_confirmed": False
            },
            "message_count": 4,
            "contact_sharing_allowed": False,
            "last_message": "Sounds great! Looking forward to it!",
            "last_message_at": now,
            "created_at": now
        }
        await db.chat_threads.insert_one(thread)
        
        # Add messages
        messages = [
            {"sender": u1, "content": f"Hey {u2['first_name']}! Your date idea sounds amazing!"},
            {"sender": u2, "content": f"Thanks! I've been wanting to try it. When works for you?"},
            {"sender": u1, "content": "How about this Saturday afternoon?"},
            {"sender": u2, "content": "Sounds great! Looking forward to it!"}
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
    
    print("✓ Created 3 matches with chat threads")
    
    # Create pending likes (vibes)
    pending_likes = [
        (2, 1),  # Olivia -> James
        (3, 0),  # Ethan -> Emma
        (6, 5),  # Isabella -> Michael
        (10, 9), # Ananya -> Arjun
    ]
    for liker_idx, liked_idx in pending_likes:
        await db.likes.insert_one({
            "id": str(uuid.uuid4()),
            "liker_id": users[liker_idx]['id'],
            "liked_id": users[liked_idx]['id'],
            "created_at": now
        })
    print("✓ Created pending likes (vibes)")
    
    # Create verification submissions (some pending)
    verifications = [
        {"user_idx": 2, "status": "PENDING", "type": "photo", "gesture": "peace_sign"},  # Olivia pending
        {"user_idx": 5, "status": "PENDING", "type": "photo", "gesture": "thumbs_up"},   # Michael pending
        {"user_idx": 9, "status": "REJECTED", "type": "photo", "gesture": "wave", "notes": "Photo unclear"},  # Arjun rejected
    ]
    for v in verifications:
        await db.verification_submissions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": users[v['user_idx']]['id'],
            "type": v['type'],
            "gesture_type": v['gesture'],
            "media_url": f"/uploads/verification_{users[v['user_idx']]['id']}.jpg",
            "status": v['status'],
            "admin_notes": v.get('notes'),
            "reviewed_by": admin_id if v['status'] != 'PENDING' else None,
            "reviewed_at": now if v['status'] != 'PENDING' else None,
            "created_at": now
        })
    print("✓ Created verification submissions")
    
    # Create reports
    reports = [
        {"reporter_idx": 0, "reported_idx": 11, "reason": "spam", "details": "Keeps sending promotional messages"},
        {"reporter_idx": 4, "reported_idx": 7, "reason": "harassment", "details": "Inappropriate messages"},
    ]
    for r in reports:
        await db.reports.insert_one({
            "id": str(uuid.uuid4()),
            "reporter_id": users[r['reporter_idx']]['id'],
            "reported_user_id": users[r['reported_idx']]['id'],
            "reason": r['reason'],
            "details": r['details'],
            "evidence_messages": [],
            "status": "pending",
            "admin_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": now
        })
    print("✓ Created sample reports")
    
    # Create trusted contacts for some users
    trusted_contacts = [
        {"user_idx": 0, "name": "Sarah", "email": "sarah.friend@example.com"},
        {"user_idx": 4, "name": "Mom", "email": "mom@example.com"},
        {"user_idx": 8, "name": "Neha", "email": "neha@example.com"},
    ]
    for tc in trusted_contacts:
        await db.trusted_contacts.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": users[tc['user_idx']]['id'],
            "name": tc['name'],
            "email": tc['email'],
            "created_at": now
        })
    print("✓ Created trusted contacts")
    
    print("\n🎉 Seed complete!")
    print("\n📋 Test Accounts:")
    print("━" * 50)
    print("Admin: admin@datefirst.app / admin123")
    print("━" * 50)
    for u in users_data[:6]:  # Show first 6 users
        badges = []
        if u['verified']['email']: badges.append("Email")
        if u['verified']['photo']: badges.append("Photo")
        if u['verified']['phone']: badges.append("Phone")
        badge_str = f" [{', '.join(badges)}]" if badges else ""
        print(f"{u['first_name']:10} {u['email']:25} / password123{badge_str}")
    print("... and 6 more users")
    print("━" * 50)
    print("\n🔗 Matches: Emma↔James, Sofia↔Michael, Priya↔Arjun")
    print("📝 Pending Verifications: 2 | Reports: 2")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
