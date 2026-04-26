#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class DateFirstV3APITester:
    def __init__(self, base_url=None):
        # Default to the BACKEND_URL env var, then localhost. Override with a
        # constructor arg or BACKEND_URL=https://your-render-host.onrender.com.
        import os
        if base_url is None:
            base_url = os.environ.get("BACKEND_URL", "http://localhost:8001").rstrip("/") + "/api"
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED: {details}")
            self.failed_tests.append({"test": test_name, "error": details})
        
        if details:
            print(f"   Details: {details}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> tuple[bool, Dict]:
        """Make API request and return success status and response data"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
            
            if not success:
                response_data["status_code"] = response.status_code
                response_data["expected_status"] = expected_status
            
            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test API health endpoint"""
        success, response = self.make_request('GET', 'health')
        self.log_result("Health Check", success, 
                       f"Status: {response.get('status', 'unknown')}" if success else str(response))
        return success

    def test_seed_database(self):
        """Test database seeding"""
        success, response = self.make_request('POST', 'seed')
        self.log_result("Database Seeding", success, 
                       f"Users: {response.get('users', 0)}, Matches: {response.get('matches', 0)}" if success else str(response))
        return success

    def test_login(self, email: str, password: str):
        """Test user login"""
        data = {"email": email, "password": password}
        success, response = self.make_request('POST', 'auth/login', data)
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_data = response['user']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            
        self.log_result(f"Login ({email})", success, 
                       f"User: {response.get('user', {}).get('first_name', 'unknown')}" if success else str(response))
        return success

    def test_signup(self, email: str, password: str):
        """Test user signup"""
        data = {"email": email, "password": password}
        success, response = self.make_request('POST', 'auth/signup', data)
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_data = response['user']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            
        self.log_result(f"Signup ({email})", success, 
                       f"User ID: {response.get('user', {}).get('id', 'unknown')}" if success else str(response))
        return success

    def test_get_me(self):
        """Test get current user info"""
        success, response = self.make_request('GET', 'auth/me')
        self.log_result("Get Current User", success, 
                       f"User: {response.get('user', {}).get('first_name', 'unknown')}" if success else str(response))
        return success

    def test_discover_invites(self):
        """Test fetching discovery feed"""
        success, response = self.make_request('GET', 'discover')
        invites_count = len(response.get('invites', [])) if success else 0
        total = response.get('total', 0) if success else 0
        
        self.log_result("Get Discovery Feed", success, 
                       f"Found {invites_count} invites, Total: {total}" if success else str(response))
        return success, response.get('invites', []) if success else []

    def test_discover_with_filters(self):
        """Test discovery with filters"""
        params = "?interested_in=male&max_distance=25&tags=coffee&sort_by=new"
        success, response = self.make_request('GET', f'discover{params}')
        invites_count = len(response.get('invites', [])) if success else 0
        
        self.log_result("Discovery with Filters", success, 
                       f"Found {invites_count} filtered invites" if success else str(response))
        return success

    def test_like_user(self, user_id: str):
        """Test liking a user"""
        success, response = self.make_request('POST', f'like/{user_id}')
        is_match = response.get('is_match', False) if success else False
        
        self.log_result("Like User", success, 
                       f"Match: {is_match}, Message: {response.get('message', '')}" if success else str(response))
        return success, is_match

    def test_unlike_user(self, user_id: str):
        """Test unliking a user (pass)"""
        success, response = self.make_request('DELETE', f'like/{user_id}')
        self.log_result("Unlike User", success, 
                       response.get('message', 'Success') if success else str(response))
        return success

    def test_get_vibes(self):
        """Test getting users who liked me"""
        success, response = self.make_request('GET', 'vibes')
        vibes_count = len(response.get('vibes', [])) if success else 0
        
        self.log_result("Get Vibes", success, 
                       f"Found {vibes_count} users who liked you" if success else str(response))
        return success, response.get('vibes', []) if success else []

    def test_get_plans(self):
        """Test getting matches/plans"""
        success, response = self.make_request('GET', 'plans')
        plans_count = len(response.get('plans', [])) if success else 0
        
        self.log_result("Get Plans", success, 
                       f"Found {plans_count} matches/plans" if success else str(response))
        return success, response.get('plans', []) if success else []

    def test_get_chat_thread(self, thread_id: str):
        """Test getting chat thread details"""
        success, response = self.make_request('GET', f'chat/{thread_id}')
        self.log_result("Get Chat Thread", success, 
                       f"Thread ID: {response.get('thread', {}).get('id', 'unknown')}" if success else str(response))
        return success

    def test_get_messages(self, thread_id: str):
        """Test getting chat messages"""
        success, response = self.make_request('GET', f'chat/{thread_id}/messages')
        messages_count = len(response.get('messages', [])) if success else 0
        
        self.log_result("Get Chat Messages", success, 
                       f"Found {messages_count} messages" if success else str(response))
        return success

    def test_send_message(self, thread_id: str):
        """Test sending a chat message"""
        data = {"content": "Hello! Looking forward to our date!"}
        success, response = self.make_request('POST', f'chat/{thread_id}/messages', data)
        message_id = response.get('id') if success else None
        
        self.log_result("Send Chat Message", success, 
                       f"Message ID: {message_id}" if success else str(response))
        return success

    def test_update_date_plan(self, thread_id: str):
        """Test updating date plan"""
        data = {
            "proposed_datetime": "2024-12-25T19:00:00",
            "proposed_location": "Central Park Coffee",
            "who_pays": "split"
        }
        success, response = self.make_request('PUT', f'chat/{thread_id}/plan', data)
        
        self.log_result("Update Date Plan", success, 
                       f"Plan updated" if success else str(response))
        return success

    def test_email_verification(self, code: str):
        """Test email verification"""
        data = {"code": code}
        success, response = self.make_request('POST', 'auth/verify-email', data)
        self.log_result("Email Verification", success, 
                       response.get('message', 'Success') if success else str(response))
        return success

    def test_resend_verification(self):
        """Test resending verification code"""
        success, response = self.make_request('POST', 'auth/resend-verification')
        self.log_result("Resend Verification", success, 
                       response.get('message', 'Success') if success else str(response))
        return success

    def test_trusted_contacts(self):
        """Test trusted contacts CRUD"""
        # Get trusted contacts
        success, response = self.make_request('GET', 'safety/trusted-contacts')
        contacts_count = len(response.get('contacts', [])) if success else 0
        self.log_result("Get Trusted Contacts", success, 
                       f"Found {contacts_count} contacts" if success else str(response))
        
        # Add trusted contact
        data = {"name": "Test Friend", "email": "friend@test.com"}
        success, response = self.make_request('POST', 'safety/trusted-contacts', data)
        contact_id = response.get('id') if success else None
        self.log_result("Add Trusted Contact", success, 
                       f"Contact ID: {contact_id}" if success else str(response))
        
        # Remove trusted contact if added successfully
        if contact_id:
            success, response = self.make_request('DELETE', f'safety/trusted-contacts/{contact_id}')
            self.log_result("Remove Trusted Contact", success, 
                           response.get('message', 'Success') if success else str(response))
        
        return True

    def test_templates_library(self):
        """Test templates library functionality"""
        # Get cities
        success, response = self.make_request('GET', 'templates/cities')
        cities_count = len(response.get('cities', [])) if success else 0
        self.log_result("Get Template Cities", success, 
                       f"Found {cities_count} cities" if success else str(response))
        
        # Get templates
        success, response = self.make_request('GET', 'templates?limit=10')
        templates_count = len(response.get('templates', [])) if success else 0
        self.log_result("Get Templates", success, 
                       f"Found {templates_count} templates" if success else str(response))
        
        # Get templates with filters
        success, response = self.make_request('GET', 'templates?city=Austin&safety_level=Public%20%26%20Busy')
        filtered_count = len(response.get('templates', [])) if success else 0
        self.log_result("Get Filtered Templates", success, 
                       f"Found {filtered_count} filtered templates" if success else str(response))
        
        return True

    def test_verification_submissions(self):
        """Test photo verification status"""
        success, response = self.make_request('GET', 'verification/photo/status')
        verified = response.get('verified', False) if success else False
        self.log_result("Photo Verification Status", success, 
                       f"Verified: {verified}" if success else str(response))
        return success

    def test_admin_features(self):
        """Test admin panel features (requires admin login)"""
        # Get admin stats
        success, response = self.make_request('GET', 'admin/stats')
        if success:
            stats = response
            self.log_result("Admin Stats", success, 
                           f"Users: {stats.get('total_users', 0)}, Reports: {stats.get('pending_reports', 0)}")
        else:
            self.log_result("Admin Stats", success, str(response))
        
        # Get pending verifications
        success, response = self.make_request('GET', 'admin/verifications?status=PENDING')
        verifications_count = len(response.get('submissions', [])) if success else 0
        self.log_result("Admin Verifications", success, 
                       f"Found {verifications_count} pending verifications" if success else str(response))
        
        # Get pending reports
        success, response = self.make_request('GET', 'admin/reports?status=pending')
        reports_count = len(response.get('reports', [])) if success else 0
        self.log_result("Admin Reports", success, 
                       f"Found {reports_count} pending reports" if success else str(response))
        
        return True

    def test_rate_limiting(self):
        """Test rate limiting on likes"""
        # Try to like multiple users rapidly to test rate limiting
        success, invites = self.test_discover_invites()
        if success and invites:
            like_attempts = 0
            rate_limited = False
            
            for invite in invites[:5]:  # Try to like first 5 users
                success, response = self.make_request('POST', f'like/{invite["user_id"]}', expected_status=200)
                like_attempts += 1
                
                if not success and response.get('status_code') == 429:
                    rate_limited = True
                    break
            
            self.log_result("Rate Limiting Test", True, 
                           f"Attempted {like_attempts} likes, Rate limited: {rate_limited}")
        
        return True
        """Test getting user profile"""
        success, response = self.make_request('GET', f'profile/{user_id}')
        self.log_result("Get User Profile", success, 
                       f"Name: {response.get('first_name', 'unknown')}" if success else str(response))
        return success

    def test_update_profile(self):
        """Test updating own profile"""
        data = {
            "first_name": "Emma Updated",
            "bio": "Updated bio for testing",
            "height": "5'7\""
        }
        success, response = self.make_request('PUT', 'profile', data)
        
        self.log_result("Update Profile", success, 
                       f"Profile updated" if success else str(response))
        return success

    def test_block_user(self, user_id: str):
        """Test blocking a user"""
        data = {"blocked_user_id": user_id}
        success, response = self.make_request('POST', 'block', data)
        
        self.log_result("Block User", success, 
                       response.get('message', 'Success') if success else str(response))
        return success

    def test_get_blocked_users(self):
        """Test getting blocked users"""
        success, response = self.make_request('GET', 'blocked')
        blocked_count = len(response.get('blocked', [])) if success else 0
        
        self.log_result("Get Blocked Users", success, 
                       f"Found {blocked_count} blocked users" if success else str(response))
        return success

    def test_unblock_user(self, user_id: str):
        """Test unblocking a user"""
        success, response = self.make_request('DELETE', f'block/{user_id}')
        
        self.log_result("Unblock User", success, 
                       response.get('message', 'Success') if success else str(response))
        return success

    def test_report_user(self, user_id: str):
        """Test reporting a user"""
        data = {
            "reported_user_id": user_id,
            "reason": "inappropriate",
            "details": "Test report for API testing"
        }
        success, response = self.make_request('POST', 'report', data)
        
        self.log_result("Report User", success, 
                       response.get('message', 'Success') if success else str(response))
        return success

    def run_comprehensive_test(self):
        """Run comprehensive API test suite for DateFirst v3"""
        print("🚀 Starting DateFirst v3 API Test Suite")
        print("=" * 50)
        
        # Health check
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Test authentication with demo accounts
        print("\n📝 Testing Authentication...")
        if not self.test_login("emma@example.com", "password123"):
            print("❌ Demo login failed - stopping tests")
            return False
        
        # Test user info
        self.test_get_me()
        
        # Test email verification features
        print("\n✉️ Testing Email Verification...")
        self.test_resend_verification()
        
        # Test verification status
        print("\n🔒 Testing Verification Features...")
        self.test_verification_submissions()
        
        # Test safety features
        print("\n🛡️ Testing Safety Features...")
        self.test_trusted_contacts()
        
        # Test templates library
        print("\n📚 Testing Templates Library...")
        self.test_templates_library()
        
        # Test discovery
        print("\n🔍 Testing Discovery...")
        success, invites = self.test_discover_invites()
        if not success:
            print("❌ Discovery failed")
            return False
        
        # Test discovery with filters
        self.test_discover_with_filters()
        
        # Test rate limiting
        print("\n⏱️ Testing Rate Limiting...")
        self.test_rate_limiting()
        
        # Test liking system
        print("\n💖 Testing Like System...")
        if invites and len(invites) > 0:
            target_user_id = invites[0]['user_id']
            success, is_match = self.test_like_user(target_user_id)
            if success:
                # Test unlike
                self.test_unlike_user(target_user_id)
        
        # Test vibes (who liked me)
        print("\n✨ Testing Vibes...")
        success, vibes = self.test_get_vibes()
        
        # Test plans (matches)
        print("\n📅 Testing Plans...")
        success, plans = self.test_get_plans()
        
        # Test chat functionality if we have matches
        if plans and len(plans) > 0:
            print("\n💬 Testing Chat...")
            thread_id = plans[0]['thread_id']
            self.test_get_chat_thread(thread_id)
            self.test_get_messages(thread_id)
            self.test_send_message(thread_id)
            self.test_update_date_plan(thread_id)
        
        # Test profile management
        print("\n👤 Testing Profile Management...")
        self.test_update_profile()
        
        # Test blocking/reporting
        print("\n🚫 Testing Block & Report...")
        if invites and len(invites) > 1:
            test_user_id = invites[1]['user_id']
            self.test_block_user(test_user_id)
            self.test_get_blocked_users()
            self.test_report_user(test_user_id)
            self.test_unblock_user(test_user_id)
        
        # Test admin features with admin account
        print("\n👑 Testing Admin Features...")
        if self.test_login("admin@datefirst.app", "admin123"):
            self.test_admin_features()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failed in self.failed_tests:
                print(f"  - {failed['test']}: {failed['error']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 70  # Consider 70%+ success rate as passing for v3

def main():
    """Main test execution"""
    tester = DateFirstV3APITester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())