# DateFirst v2 - Product Requirements Document

## Overview
DateFirst is a dating app where users browse **date ideas**, not profiles. Before matching, users only see a person's first name, photo, and their "First Date Idea." Full profiles are revealed only after mutual matching.

## Core Philosophy
"Browse ideas, not just faces. Match on experiences that excite you both."

## User Flow

### Pre-Match Experience
Users see limited information:
- First name
- Main photo
- First Date Idea (title, description, tags, city)
- General vibes/preferences

**NOT visible pre-match:**
- Date of birth / age (stored but hidden)
- Full bio
- Height
- Extra details

### Post-Match Experience
Upon mutual like:
- Full profile unlocked
- Private 1:1 chat opens
- "Plan the date" panel available

## Core Requirements

### 1. Authentication
- [x] Email/password signup/login
- [x] JWT session management
- [x] Redirect to onboarding for new users

### 2. Onboarding Wizard (8 Steps)
- [x] Step 1: Name + Main Photo URL
- [x] Step 2: City + Distance Preference (1-100 miles)
- [x] Step 3: Date of Birth
- [x] Step 4: Gender + Interested In (Men/Women/Both)
- [x] Step 5: Height (optional)
- [x] Step 6: Bio (optional, hidden pre-match)
- [x] Step 7: Date Preferences (multi-select tags)
- [x] Step 8: First Date Idea (REQUIRED - title, description, tags, city)

### 3. Navigation (4 Tabs)
- [x] **Discover**: Swipe through date invites
- [x] **Vibes**: Users who liked you
- [x] **Plans**: Matches and conversations
- [x] **Profile**: View/edit your profile

### 4. Discover Feed
- [x] Card-based UI (photo + name + date idea)
- [x] Like (heart) and Pass (X) actions
- [x] Quick tag filters (horizontal chips)
- [x] Filter drawer with:
  - Gender preference
  - Distance slider
  - Sort by (For You / New)

### 5. Matching System
- [x] Like action creates a "like" record
- [x] Mutual likes create a "match"
- [x] Match triggers chat thread creation
- [x] Notification on match

### 6. Chat
- [x] Private 1:1 messaging
- [x] "Matched on" banner showing the date idea
- [x] "Plan the date" collapsible panel:
  - Proposed date/time
  - Meeting location
  - Who pays (I pay / Split / They pay / Decide later)
  - Confirm button

### 7. Safety Features
- [x] Block users (removes from all views)
- [x] Report users
- [x] Unblock from settings

## Technical Architecture

### Backend (FastAPI + MongoDB)
- `/api/auth/*` - Authentication
- `/api/profile/setup` - Onboarding
- `/api/profile` - Profile updates
- `/api/discover` - Discovery feed with filters
- `/api/like/{user_id}` - Like/match system
- `/api/vibes` - Users who liked you
- `/api/plans` - Matches list
- `/api/chat/*` - Messaging

### Privacy Enforcement (Server-Side)
- `get_public_profile()` - Returns only name, photo, city, date idea
- `get_full_profile()` - Returns all fields (post-match only)
- `are_matched()` helper checks match status before revealing details

### Frontend (React + Tailwind)
- Mobile-first design
- 4-tab bottom navigation
- Swipe-style cards on Discover
- Polling-based chat (5s interval)

### Data Model
- User (auth info)
- Profile (with first_date_idea embedded)
- Like (liker_id, liked_id)
- Match (user1_id, user2_id)
- ChatThread (with date_plan embedded)
- ChatMessage
- Block, Report

## What's Been Implemented

### January 24, 2025
- Complete v2 rewrite from scratch
- New privacy-first concept
- 8-step onboarding wizard
- Tinder-like swipe cards
- Filter drawer
- "Plan the date" chat feature
- 12 seeded users, 3 matches

## Demo Accounts
- emma@example.com / password123 (matched with James)
- james@example.com / password123 (matched with Emma)
- All demo passwords: password123

## Prioritized Backlog

### P0 (Done)
- [x] Core auth + onboarding
- [x] Discovery with filters
- [x] Like/match system
- [x] Chat with date planning

### P1 (Future)
- [ ] Photo upload (currently URL-based)
- [ ] Real-time WebSocket chat
- [ ] Push notifications
- [ ] Geolocation for distance

### P2 (Nice to Have)
- [ ] Video intro clips
- [ ] Voice messages
- [ ] "Super like" feature
- [ ] Date idea templates
