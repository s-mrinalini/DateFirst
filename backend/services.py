"""
Service integrations for DateFirst.

These wrap SendGrid (email), Twilio (SMS), and AWS S3 (file storage). Each
service auto-selects between a real provider and a mock based on whether the
required env vars are present.

Real-provider env vars:
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
- SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, AWS_REGION

The SendGrid and Twilio Python SDKs are synchronous; we wrap calls in
asyncio.to_thread so they don't block the event loop.
"""

import os
import logging
import uuid
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import aiofiles

from config import APP_URL

logger = logging.getLogger(__name__)


# ==================== SMS SERVICE (Twilio) ====================

class SMSService:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = os.environ.get("TWILIO_PHONE_NUMBER")
        self.is_mock = not all([self.account_sid, self.auth_token, self.from_number])

        if not self.is_mock:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS service initialized")
            except ImportError:
                logger.warning("Twilio package not installed; falling back to mock.")
                self.is_mock = True
        else:
            logger.info("SMS service running in MOCK mode (no Twilio env vars).")

    def _send_sync(self, to: str, body: str) -> str:
        msg = self.client.messages.create(body=body, from_=self.from_number, to=to)
        return msg.sid

    async def send_otp(self, phone_number: str, otp_code: str) -> dict:
        message = (
            f"Your DateFirst verification code is: {otp_code}. "
            f"Valid for 10 minutes."
        )
        if self.is_mock:
            logger.info("[MOCK SMS] To: %s | %s", phone_number, message)
            return {
                "success": True,
                "mock": True,
                "message_id": f"mock_{uuid.uuid4().hex[:12]}",
                "phone": phone_number,
                "otp": otp_code,  # mock-only convenience
            }
        try:
            sid = await asyncio.to_thread(self._send_sync, phone_number, message)
            return {"success": True, "mock": False, "message_id": sid, "phone": phone_number}
        except Exception as e:
            logger.error("Twilio SMS error: %s", e)
            return {"success": False, "error": str(e)}

    async def send_safety_alert(self, phone_number: str, user_name: str) -> dict:
        message = (
            f"DateFirst Safety Alert: Please check in with {user_name}. "
            f"They set up a safety check-in and haven't confirmed they're okay."
        )
        if self.is_mock:
            logger.info("[MOCK SMS ALERT] To: %s | %s", phone_number, message)
            return {"success": True, "mock": True}
        try:
            sid = await asyncio.to_thread(self._send_sync, phone_number, message)
            return {"success": True, "mock": False, "message_id": sid}
        except Exception as e:
            logger.error("Twilio SMS error: %s", e)
            return {"success": False, "error": str(e)}


# ==================== EMAIL SERVICE (SendGrid) ====================

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get("SENDGRID_API_KEY")
        self.from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@datefirst.app")
        self.is_mock = not self.api_key

        if not self.is_mock:
            try:
                from sendgrid import SendGridAPIClient
                self.client = SendGridAPIClient(self.api_key)
                logger.info("SendGrid email service initialized")
            except ImportError:
                logger.warning("SendGrid package not installed; falling back to mock.")
                self.is_mock = True
        else:
            logger.info("Email service running in MOCK mode (no SENDGRID_API_KEY).")

    def _send_sync(self, to_email: str, subject: str, html: str) -> int:
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html,
        )
        response = self.client.send(message)
        return response.status_code

    async def _send(self, to_email: str, subject: str, html: str) -> dict:
        if self.is_mock:
            logger.info("[MOCK EMAIL] To: %s | Subject: %s", to_email, subject)
            return {"success": True, "mock": True, "message_id": f"mock_{uuid.uuid4().hex[:12]}"}
        try:
            status = await asyncio.to_thread(self._send_sync, to_email, subject, html)
            return {"success": True, "mock": False, "status_code": status}
        except Exception as e:
            logger.error("SendGrid error: %s", e)
            return {"success": False, "error": str(e)}

    async def send_verification_email(self, to_email: str, code: str, user_name: str = "there") -> dict:
        subject = "Verify your DateFirst email"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #E76F51;">Welcome to DateFirst!</h1>
            <p>Hi {user_name},</p>
            <p>Your verification code is:</p>
            <div style="background:#f5f5f5;padding:20px;text-align:center;font-size:32px;
                        letter-spacing:8px;font-weight:bold;color:#1C1917;">
                {code}
            </div>
            <p>This code expires in 24 hours.</p>
            <p>If you didn't create a DateFirst account, you can ignore this email.</p>
        </div>
        """
        result = await self._send(to_email, subject, html)
        if self.is_mock:
            result["code"] = code  # mock-only convenience
        return result

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> dict:
        subject = "Reset your DateFirst password"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #E76F51;">Reset your password</h1>
            <p>We received a request to reset your DateFirst password. Click the
               button below within the next 30 minutes to set a new password:</p>
            <p style="text-align:center;margin:30px 0;">
              <a href="{reset_url}"
                 style="background:#E76F51;color:#fff;padding:12px 24px;
                        border-radius:8px;text-decoration:none;font-weight:bold;">
                 Reset password
              </a>
            </p>
            <p style="color:#666;font-size:13px;">
              If the button doesn't work, paste this URL into your browser:<br>
              <span style="word-break:break-all;">{reset_url}</span>
            </p>
            <p style="color:#666;font-size:13px;">
              If you didn't request this, ignore this email — your password
              hasn't been changed.
            </p>
        </div>
        """
        result = await self._send(to_email, subject, html)
        if self.is_mock:
            result["reset_url"] = reset_url  # mock-only convenience
        return result

    async def send_safety_alert_email(self, to_email: str, user_name: str, contact_name: str) -> dict:
        subject = f"DateFirst: Please check in with {user_name}"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #E76F51;">Safety Check-In Alert</h1>
            <p>Hi {contact_name},</p>
            <p><strong>{user_name}</strong> added you as a trusted contact and
               set up a safety check-in. They haven't confirmed they're okay
               within the expected time. Please reach out to check on them.</p>
        </div>
        """
        return await self._send(to_email, subject, html)

    async def send_date_plan_share(self, to_email: str, contact_name: str, user_name: str,
                                    match_name: str, date_time: str, location: str) -> dict:
        subject = f"{user_name}'s Date Plan"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #2A9D8F;">Date Plan Shared</h1>
            <p>Hi {contact_name},</p>
            <p><strong>{user_name}</strong> wanted to share their date plan with you:</p>
            <div style="background:#f8f9fa;padding:20px;border-radius:8px;margin:20px 0;">
                <p><strong>Meeting:</strong> {match_name}</p>
                <p><strong>When:</strong> {date_time or 'Not specified'}</p>
                <p><strong>Where:</strong> {location or 'Not specified'}</p>
            </div>
        </div>
        """
        return await self._send(to_email, subject, html)


# ==================== FILE STORAGE (S3 private + presigned URLs) ====================

class FileStorageService:
    """
    S3 mode: bucket is private; we return a presigned GET URL with a 7-day
    expiry. The DB stores that URL. Re-upload to refresh.
    Local mode (dev): files are written to UPLOAD_DIR and served via the
    /uploads StaticFiles mount.
    """

    SIGNED_URL_TTL = 7 * 24 * 3600  # 7 days

    def __init__(self, local_upload_dir: str = "/app/uploads"):
        self.access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.bucket = os.environ.get("AWS_S3_BUCKET")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.is_mock = not all([self.access_key, self.secret_key, self.bucket])

        self.local_dir = Path(local_upload_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)

        if not self.is_mock:
            try:
                import boto3
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region,
                )
                logger.info("S3 file storage initialized (private bucket + presigned URLs)")
            except ImportError:
                logger.warning("boto3 not installed; falling back to local storage.")
                self.is_mock = True
        else:
            logger.info("File storage running in LOCAL mode (no AWS env vars).")

    def _generate_signed_url_sync(self, key: str) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.SIGNED_URL_TTL,
        )

    def _put_object_sync(self, key: str, body: bytes, content_type: str) -> None:
        # Private object — no ACL. Bucket policy enforces access.
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def _delete_object_sync(self, key: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket, Key=key)

    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> dict:
        file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        if file_ext not in ("jpg", "jpeg", "png", "webp"):
            file_ext = "jpg"
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"

        if self.is_mock:
            file_path = self.local_dir / unique_name
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)
            url = f"/uploads/{unique_name}"
            logger.info("[LOCAL STORAGE] Saved: %s", url)
            return {
                "success": True, "mock": True, "url": url,
                "filename": unique_name, "key": unique_name, "size": len(file_content),
            }

        key = f"uploads/{unique_name}"
        try:
            await asyncio.to_thread(self._put_object_sync, key, file_content, content_type)
            url = await asyncio.to_thread(self._generate_signed_url_sync, key)
            return {
                "success": True, "mock": False, "url": url,
                "filename": unique_name, "key": key, "size": len(file_content),
            }
        except Exception as e:
            logger.error("S3 upload error: %s", e)
            return {"success": False, "error": str(e)}

    async def delete_file(self, filename: str) -> dict:
        if self.is_mock:
            file_path = self.local_dir / filename
            if file_path.exists():
                file_path.unlink()
                return {"success": True, "mock": True}
            return {"success": False, "error": "File not found"}
        try:
            key = filename if filename.startswith("uploads/") else f"uploads/{filename}"
            await asyncio.to_thread(self._delete_object_sync, key)
            return {"success": True, "mock": False}
        except Exception as e:
            logger.error("S3 delete error: %s", e)
            return {"success": False, "error": str(e)}

    async def refresh_signed_url(self, key: str) -> str:
        """Re-sign a stored S3 key. No-op for local mode."""
        if self.is_mock:
            return f"/uploads/{key}" if not key.startswith("/") else key
        return await asyncio.to_thread(self._generate_signed_url_sync, key)


# Singletons
sms_service = SMSService()
email_service = EmailService()
file_storage = FileStorageService()
