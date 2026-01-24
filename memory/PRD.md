# DateFirst - Product Requirements Document

## Overview
DateFirst is a dating app where users post date ideas and others apply to join them. Users browse date plans, not profiles - focusing on shared experiences rather than appearances.

## Core Philosophy
"The best dates start with a great idea, not a swipe."

## User Personas

### 1. Date Creator (Host)
- Wants to plan meaningful experiences
- Values quality over quantity in matches
- Prefers to evaluate applicants based on shared interests

### 2. Date Applicant (Guest)
- Discovers dates that genuinely interest them
- Applies to experiences that match their preferences
- Can see what they're signing up for before matching

### 3. Premium User
- Wants deeper insights into applicants
- Values compatibility scoring and detailed profiles
- Willing to pay for enhanced decision-making

## Core Requirements (Static)

### Authentication & Profiles
- [x] Email/password JWT authentication
- [x] User profile with: name, age, gender, city, bio, photo
- [x] Premium profile fields: extra photos, job title, interests, intent
- [x] Secure session management

### Date Posts
- [x] Create with: title, description, location, date/time, who pays, tags
- [x] Status flow: OPEN → SELECTED → COMPLETED/CANCELLED
- [x] Edit/delete own posts
- [x] Max applicants limit

### Browse & Discovery
- [x] Feed of date posts (not profiles)
- [x] Filters: city, tags, time, who pays
- [x] Search by keyword
- [x] Sort: newest, soonest, most popular

### Application System
- [x] Apply with message (can't apply to own)
- [x] Withdraw pending applications
- [x] Rate limiting (10/day)
- [x] Profanity filter

### Matching
- [x] Host views applicant list
- [x] Accept one applicant (declines others)
- [x] Creates private chat on acceptance

### Chat
- [x] Private 1:1 messaging
- [x] Date confirmation panel
- [x] Block/report from chat

### Premium Features
- [x] Full applicant details (job, interests, intent)
- [x] Compatibility scoring
- [x] Premium badge display
- [x] Placeholder payment flow

### Safety & Trust
- [x] Block users (hides content both ways)
- [x] Report users/posts
- [x] Profanity filter
- [x] Rate limiting

## What's Been Implemented

### January 24, 2025
- Full MVP implementation complete
- Backend: FastAPI with MongoDB
- Frontend: React with Tailwind CSS, Shadcn/UI
- 10 seeded users, 20 date posts, 2 chat threads
- All core features working

### Key Features Delivered
1. Authentication (login/signup/logout)
2. Profile management (view/edit)
3. Date post CRUD with status management
4. Browse feed with filters and search
5. Like/unlike dates
6. Apply/withdraw applications
7. Accept applicant (creates chat)
8. Private messaging
9. Premium upgrade (MOCKED - no real payment)
10. Block/report functionality
11. Settings page with blocked users management

## Prioritized Backlog

### P0 (Critical) - Done
- [x] Authentication
- [x] Create/browse dates
- [x] Apply/accept flow
- [x] Chat functionality

### P1 (Important) - Done
- [x] Premium gating
- [x] Block/report
- [x] Profile editing
- [x] Filters and search

### P2 (Nice to Have) - Future
- [ ] Real payment integration (Stripe)
- [ ] WebSocket real-time chat
- [ ] Push notifications
- [ ] Photo upload (currently URL-based)
- [ ] Email verification
- [ ] Password reset
- [ ] Google OAuth
- [ ] Admin dashboard for moderation
- [ ] Read receipts in chat
- [ ] Advanced matching algorithm

## Technical Architecture

### Backend (FastAPI + MongoDB)
- `/api/auth/*` - Authentication endpoints
- `/api/profile` - Profile management
- `/api/dates` - Date post CRUD
- `/api/dates/{id}/apply` - Application system
- `/api/applications/{id}/accept` - Accept applicant
- `/api/chat/*` - Messaging system
- `/api/block`, `/api/report` - Safety features
- `/api/upgrade` - Premium toggle (mocked)

### Frontend (React + Tailwind)
- Single-page application
- JWT stored in localStorage
- Polling-based chat (5s interval)
- Responsive mobile-first design
- Shadcn/UI component library

### Database Collections
- users, profiles
- date_posts, applications, likes
- chat_threads, chat_messages
- blocks, reports

## Demo Accounts
- emma@example.com / password123 (Standard)
- liam@example.com / password123 (Premium)
- All demo passwords: password123

## Notes
- Premium payment is MOCKED (no real charges)
- Chat uses polling, not WebSockets
- Photos are URL-based, no upload functionality
