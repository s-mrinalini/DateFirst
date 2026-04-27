# DateFirst v3 - Product Requirements Document

## Original Problem Statement
Extend the existing "DateFirst" app with a robust Safety/Trust layer, geolocation handling, profile verification, and an optional First Date Ideas Library (templates). Implement end-to-end full-stack. Make DateFirst safer than typical swipe apps because matches are formed around "first date ideas". Maintain strict privacy: pre-match only show name + main photo + first date idea. Add proactive safety features.

## Core Requirements

### A) Security / Abuse Prevention (MUST)
- [x] Password hashing (Argon2)
- [x] Email verification required before Discover
- [x] Rate limiting: likes/min, messages/min, reports/min, profile edits/hour
- [x] Daily caps: likes/day, messages to new matches/day
- [x] Shadow-ban capability for abusive accounts
- [x] Active session tracking, logout all devices
- [x] Fraud signals: IP hash, user agent, signup timestamp
- [x] Profanity filter for date idea title/description, bio, chat
- [x] Contact info blocking in first 20 messages

### B) Geolocation / Location Privacy (MUST)
- [x] City-based location during onboarding
- [x] Internal city->lat/lng mapping for 27 major cities
- [x] Haversine distance calculation
- [x] Pre-match: show only city (no exact distance)
- [x] Distance filtering slider (1-100 miles)
- [x] Safe meeting nudges in chat

### C) Profile Verification (MUST)
- [x] Email verified (required) - Badge
- [x] Photo verification flow - Admin review UI
- [x] Phone verification (mock OTP)
- [x] ID verification placeholder (Phase 2)
- [x] Badges visible pre-match

### D) User Safety Toolkit (MUST)
- [x] Block & Report with reasons
- [x] Evidence snapshot (last 20 messages)
- [x] Auto-restriction after N reports
- [x] Trusted Contacts (1-3 email contacts)
- [x] Date Check-In scheduling
- [x] Share Date Plan summary
- [x] Safety prompts in chat
- [x] Age verification (18+ only)

### E) First Date Ideas Library (MUST)
- [x] 60+ global templates
- [x] 10 templates per city (27 cities)
- [x] City-aware browsing
- [x] Template fields: title, description, tags, place_type, safety_level, cost_hint, duration_hint
- [x] Favorites system
- [x] Smart suggestions based on tags
- [x] "Surprise Me" button

### F) Admin Panel (MVP-LITE)
- [x] Review photo verifications (approve/reject)
- [x] Review reports with evidence
- [x] User actions: warn, restrict, shadow-ban, suspend
- [x] Audit log

## What's Been Implemented (Jan 2026)

### Backend (2479 lines)
- Complete FastAPI server with all endpoints
- MongoDB collections: users, profiles, likes, matches, chat_threads, chat_messages, blocks, reports, verification_submissions, moderation_actions, trusted_contacts, safety_checkins, rate_limit_events, favorite_templates
- Rate limiting middleware
- Content safety filters (profanity, contact info detection)
- City geocoding for 27 cities
- Haversine distance calculation
- Template library with 320+ templates

### Frontend
- SafetyCenterPage - Verification badges, trusted contacts, blocked users, emergency resources
- TemplateLibraryPage - City filtering, search, favorites, "Surprise Me"
- AdminPage - Stats dashboard, verification review, report management
- Updated ProfilePage - Links to Safety Center and Templates
- Updated AuthContext - Email/photo/phone verification state

### Seed Data
- 12 users across Austin, NYC, Mumbai
- 3 matched pairs with chat history
- 4 pending likes
- 2 pending photo verifications
- 2 pending reports
- 1 admin user

## User Personas

1. **Safety-Conscious Single (Primary)**
   - Values: Public meetups, verified profiles, trusted contact features
   - Pain point: Feels unsafe on traditional dating apps

2. **Creative Dater**
   - Values: Unique date ideas, not just swiping
   - Pain point: Bored of generic "coffee?" conversations

3. **Admin/Moderator**
   - Values: Efficient tools to maintain community safety
   - Needs: Quick verification review, report handling

## Backlog / Phase 2 Features

### P0 (Critical)
- [ ] Real SMS integration (Twilio)
- [x] Real email sending (Resend)
- [ ] WebSocket for real-time chat
- [ ] Push notifications for check-ins

### P1 (Important)
- [ ] ID verification vendor integration
- [ ] 2FA (TOTP)
- [ ] Photo upload to S3
- [ ] User-generated templates
- [ ] Template ratings/reviews

### P2 (Nice to Have)
- [ ] AI-powered photo verification
- [ ] Sentiment analysis for safety concerns
- [ ] Date feedback/ratings
- [ ] Group dates feature
- [ ] Premium subscription

## Technical Debt
- Move templates to database for admin editing
- Add proper caching for templates
- Implement proper error boundaries in React
- Add comprehensive E2E test suite

## Next Tasks
1. Deploy to production
2. Set up real email/SMS providers
3. Add WebSocket for real-time messaging
4. Implement file upload for photo verification
5. Add analytics dashboard

## Success Metrics
- User verification rate > 80%
- Report resolution time < 24h
- Template usage rate > 50%
- Date plan confirmation rate > 30%
