"""
Mock/Placeholder Service Integrations for DateFirst v3
These are production-ready interfaces that can be swapped with real providers.

To enable real providers, set environment variables:
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
- SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
import aiofiles
import hashlib

logger = logging.getLogger(__name__)

# ==================== SMS SERVICE (Twilio Mock) ====================

class SMSService:
    """
    SMS Service - Mock implementation
    To use real Twilio:
    1. pip install twilio
    2. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    3. Replace mock methods with twilio client calls
    """
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        self.is_mock = not all([self.account_sid, self.auth_token, self.from_number])
        
        if not self.is_mock:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS service initialized")
            except ImportError:
                logger.warning("Twilio package not installed, using mock")
                self.is_mock = True
        else:
            logger.info("SMS Service running in MOCK mode")
    
    async def send_otp(self, phone_number: str, otp_code: str) -> dict:
        """Send OTP code via SMS"""
        message = f"Your DateFirst verification code is: {otp_code}. Valid for 10 minutes."
        
        if self.is_mock:
            logger.info(f"[MOCK SMS] To: {phone_number} | Message: {message}")
            return {
                "success": True,
                "mock": True,
                "message_id": f"mock_{uuid.uuid4().hex[:12]}",
                "phone": phone_number,
                "otp": otp_code  # Only in mock mode for testing
            }
        
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            return {
                "success": True,
                "mock": False,
                "message_id": msg.sid,
                "phone": phone_number
            }
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_safety_alert(self, phone_number: str, user_name: str) -> dict:
        """Send safety check-in alert"""
        message = f"DateFirst Safety Alert: Please check in with {user_name}. They set up a safety check-in and haven't confirmed they're okay."
        
        if self.is_mock:
            logger.info(f"[MOCK SMS ALERT] To: {phone_number} | Message: {message}")
            return {"success": True, "mock": True}
        
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            return {"success": True, "mock": False, "message_id": msg.sid}
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return {"success": False, "error": str(e)}


# ==================== EMAIL SERVICE (SendGrid Mock) ====================

class EmailService:
    """
    Email Service - Mock implementation
    To use real SendGrid:
    1. pip install sendgrid
    2. Set SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
    3. Replace mock methods with sendgrid client calls
    """
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@datefirst.app')
        self.is_mock = not self.api_key
        
        if not self.is_mock:
            try:
                from sendgrid import SendGridAPIClient
                self.client = SendGridAPIClient(self.api_key)
                logger.info("SendGrid email service initialized")
            except ImportError:
                logger.warning("SendGrid package not installed, using mock")
                self.is_mock = True
        else:
            logger.info("Email Service running in MOCK mode")
    
    async def send_verification_email(self, to_email: str, code: str, user_name: str = "there") -> dict:
        """Send email verification code"""
        subject = "Verify your DateFirst email"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #E76F51;">Welcome to DateFirst!</h1>
            <p>Hi {user_name},</p>
            <p>Your verification code is:</p>
            <div style="background: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #1C1917;">
                {code}
            </div>
            <p>This code expires in 24 hours.</p>
            <p>If you didn't create a DateFirst account, you can ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">DateFirst - Where first dates come first</p>
        </div>
        """
        
        if self.is_mock:
            logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject} | Code: {code}")
            return {
                "success": True,
                "mock": True,
                "message_id": f"mock_{uuid.uuid4().hex[:12]}",
                "email": to_email,
                "code": code  # Only in mock mode for testing
            }
        
        try:
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.client.send(message)
            return {
                "success": True,
                "mock": False,
                "status_code": response.status_code
            }
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_safety_alert_email(self, to_email: str, user_name: str, contact_name: str) -> dict:
        """Send safety check-in alert to trusted contact"""
        subject = f"DateFirst: Please check in with {user_name}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #E76F51;">Safety Check-In Alert</h1>
            <p>Hi {contact_name},</p>
            <p><strong>{user_name}</strong> added you as a trusted contact on DateFirst and set up a safety check-in for a date.</p>
            <p style="background: #fff3cd; padding: 15px; border-left: 4px solid #E76F51;">
                They haven't confirmed they're okay within the expected time. Please reach out to check on them.
            </p>
            <p>This is an automated safety feature. If you've confirmed they're safe, no further action is needed.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">DateFirst Safety Center</p>
        </div>
        """
        
        if self.is_mock:
            logger.info(f"[MOCK SAFETY EMAIL] To: {to_email} | User: {user_name}")
            return {"success": True, "mock": True}
        
        try:
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.client.send(message)
            return {"success": True, "mock": False, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_date_plan_share(self, to_email: str, contact_name: str, user_name: str, 
                                    match_name: str, date_time: str, location: str) -> dict:
        """Send date plan details to trusted contact"""
        subject = f"{user_name}'s Date Plan"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #2A9D8F;">Date Plan Shared</h1>
            <p>Hi {contact_name},</p>
            <p><strong>{user_name}</strong> wanted to share their date plan with you:</p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Meeting:</strong> {match_name}</p>
                <p><strong>When:</strong> {date_time or 'Not specified'}</p>
                <p><strong>Where:</strong> {location or 'Not specified'}</p>
            </div>
            <h3 style="color: #2A9D8F;">Safety Tips</h3>
            <ul>
                <li>Meet in a public place</li>
                <li>Tell someone when you arrive and leave</li>
                <li>Trust your instincts</li>
            </ul>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Shared via DateFirst Safety Center</p>
        </div>
        """
        
        if self.is_mock:
            logger.info(f"[MOCK DATE PLAN EMAIL] To: {to_email} | From: {user_name}")
            return {"success": True, "mock": True}
        
        try:
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.client.send(message)
            return {"success": True, "mock": False, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return {"success": False, "error": str(e)}


# ==================== FILE STORAGE SERVICE (S3 Mock) ====================

class FileStorageService:
    """
    File Storage Service - Local storage with S3-compatible interface
    To use real S3:
    1. pip install boto3
    2. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, AWS_REGION
    3. Replace local methods with S3 client calls
    """
    
    def __init__(self, local_upload_dir: str = "/app/uploads"):
        self.access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.bucket = os.environ.get('AWS_S3_BUCKET')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.is_mock = not all([self.access_key, self.secret_key, self.bucket])
        
        self.local_dir = Path(local_upload_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.is_mock:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                logger.info("S3 file storage initialized")
            except ImportError:
                logger.warning("boto3 not installed, using local storage")
                self.is_mock = True
        else:
            logger.info("File Storage running in LOCAL mode")
    
    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> dict:
        """Upload file and return URL"""
        # Generate unique filename
        file_ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        
        if self.is_mock:
            # Save locally
            file_path = self.local_dir / unique_name
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Return local URL
            url = f"/uploads/{unique_name}"
            logger.info(f"[LOCAL STORAGE] Saved: {url}")
            return {
                "success": True,
                "mock": True,
                "url": url,
                "filename": unique_name,
                "size": len(file_content)
            }
        
        try:
            # Upload to S3
            key = f"uploads/{unique_name}"
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'
            )
            
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            return {
                "success": True,
                "mock": False,
                "url": url,
                "filename": unique_name,
                "size": len(file_content)
            }
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_file(self, filename: str) -> dict:
        """Delete file"""
        if self.is_mock:
            file_path = self.local_dir / filename
            if file_path.exists():
                file_path.unlink()
                return {"success": True, "mock": True}
            return {"success": False, "error": "File not found"}
        
        try:
            key = f"uploads/{filename}"
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return {"success": True, "mock": False}
        except Exception as e:
            logger.error(f"S3 delete error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_file_url(self, filename: str) -> str:
        """Get public URL for file"""
        if self.is_mock:
            return f"/uploads/{filename}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/uploads/{filename}"


# Initialize services (singleton pattern)
sms_service = SMSService()
email_service = EmailService()
file_storage = FileStorageService()
