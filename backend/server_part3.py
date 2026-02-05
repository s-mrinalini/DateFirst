# ==================== TEMPLATES API ====================
# Routes for Date Idea Templates

from server_part2 import DATE_IDEA_TEMPLATES_GLOBAL, CITY_TEMPLATES

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
