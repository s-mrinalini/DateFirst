# DateFirst v3 - Safety-Enhanced Dating App

> Browse date ideas, not just faces. Match on experiences that excite you both.

DateFirst is a unique dating app where users create and share "First Date Ideas" instead of traditional profiles. This version (v3) includes comprehensive safety features, profile verification, geolocation handling, and a city-aware date ideas library.

## Features

### Core Dating Features
- **Date Ideas First**: Users see date ideas (title, description, tags, city) before profiles
- **Vibes & Plans**: Like system ("vibes") creates matches when mutual
- **Real-time Chat**: Message matches with date planning features
- **Privacy-First**: Full profiles visible only after matching

### Safety & Trust Layer (NEW in v3)

#### Account Security
- Password hashing (Argon2)
- Email verification required before browsing
- Session management (logout all devices)
- Rate limiting on likes, messages, reports, profile edits

#### Profile Verification
- **Email Verified** (required) - Badge displayed on profile
- **Photo Verified** - Selfie with gesture matching
- **Phone Verified** - OTP verification (mock for MVP)
- **ID Verified** - Placeholder for future vendor integration

#### Safety Features
- **Trusted Contacts**: Add up to 3 emergency contacts
- **Date Check-In**: Schedule safety check-ins during dates
- **Block & Report**: Report harassment, spam, impersonation, etc.
- **Content Filters**: Profanity filter, contact info blocking
- **Safe Meeting Nudges**: Prompts for public places, daylight dates

### Date Ideas Library (NEW in v3)
- **60+ Global Templates**: Coffee, food, outdoors, culture, activities, etc.
- **City-Specific Ideas**: 10 templates per city for 27 major cities
  - US: NYC, LA, SF, Chicago, Boston, DC, Seattle, Austin, Miami, Houston, Dallas, Atlanta, Denver, San Diego, Philadelphia
  - India: Mumbai, Delhi, Bengaluru, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Jaipur, Goa, Kochi, Chandigarh
- **Smart Suggestions**: Filter by tags, safety level, cost
- **Favorites**: Save templates for later

### Admin Panel
- Dashboard with user stats
- Review photo verification submissions
- Review user reports with evidence
- User moderation actions (warn, restrict, shadow-ban, suspend)
- Audit log of all moderation actions

## Tech Stack

- **Frontend**: React 18, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Auth**: JWT with session management

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- MongoDB

### Installation

1. Clone the repository
```bash
git clone <repo-url>
cd datefirst-v3
```

2. Backend setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure MongoDB URL
```

3. Frontend setup
```bash
cd frontend
yarn install
cp .env.example .env  # Configure API URL
```

4. Seed the database
```bash
cd backend
python seed.py
```

5. Start the servers
```bash
# Backend
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend && yarn start
```

### Environment Variables

**Backend (.env)**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=datefirst_v3
JWT_SECRET=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env)**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Demo Accounts

After running the seed script:

| User | Email | Password | City | Verified |
|------|-------|----------|------|----------|
| Admin | admin@datefirst.app | admin123 | - | All |
| Emma | emma@example.com | password123 | Austin | Email, Photo |
| James | james@example.com | password123 | Austin | Email, Photo, Phone |
| Sofia | sofia@example.com | password123 | NYC | Email, Photo, Phone |
| Priya | priya@example.com | password123 | Mumbai | Email, Photo, Phone |

## API Documentation

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/verify-email` - Verify email with code
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout-all` - Logout all devices

### Profile
- `POST /api/profile/setup` - Initial profile setup
- `PUT /api/profile` - Update profile
- `GET /api/profile/{user_id}` - Get profile (public/full based on match status)

### Discovery
- `GET /api/discover` - Get date ideas feed with filters
- `POST /api/like/{user_id}` - Like a user
- `GET /api/vibes` - Get users who liked you
- `GET /api/plans` - Get matches

### Chat
- `GET /api/chat/{thread_id}` - Get chat thread
- `GET /api/chat/{thread_id}/messages` - Get messages
- `POST /api/chat/{thread_id}/messages` - Send message
- `PUT /api/chat/{thread_id}/plan` - Update date plan

### Safety
- `GET /api/safety/trusted-contacts` - Get trusted contacts
- `POST /api/safety/trusted-contacts` - Add trusted contact
- `DELETE /api/safety/trusted-contacts/{id}` - Remove contact
- `POST /api/safety/checkin` - Create date check-in
- `POST /api/block` - Block user
- `POST /api/report` - Report user

### Verification
- `POST /api/verification/photo/submit` - Submit photo verification
- `POST /api/verification/phone/start` - Start phone verification
- `POST /api/verification/phone/verify` - Verify phone OTP

### Templates
- `GET /api/templates` - Browse templates with filters
- `GET /api/templates/cities` - Get available cities
- `GET /api/templates/suggest` - Get smart suggestions
- `POST /api/templates/{id}/favorite` - Toggle favorite

### Admin (requires admin role)
- `GET /api/admin/stats` - Dashboard stats
- `GET /api/admin/verifications` - Pending verifications
- `PUT /api/admin/verifications/{id}` - Approve/reject
- `GET /api/admin/reports` - Pending reports
- `POST /api/admin/users/{id}/action` - Take moderation action

## License

MIT
