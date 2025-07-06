import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        if self.account_sid and self.auth_token and self.phone_number:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                logger.info("SMS Service initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Twilio client", exc_info=e)
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio credentials not found. SMS functionality disabled.")
    
    def send_admin_alert(self, admin_phone, request_type, username):
        """Send SMS alert to admin about new request"""
        if not self.enabled or not self.client:
            logger.warning("SMS service not enabled, skipping admin alert")
            return False
        
        try:
            message_body = f"New {request_type} submitted by {username}. Please review in admin panel."
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.phone_number,
                to=admin_phone
            )
            
            logger.info(f"Admin alert SMS sent: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send admin alert SMS: {str(e)}")
            return False
    
    def send_approval_notification(self, user_phone, request_type, status):
        """Send SMS notification to user about request approval/rejection"""
        if not self.enabled or not self.client:
            logger.warning("SMS service not enabled, skipping approval notification")
            return False
        
        try:
            message_body = f"Your {request_type} has been {status.lower()}. Check your dashboard for details."
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.phone_number,
                to=user_phone
            )
            
            logger.info(f"Approval notification SMS sent: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send approval notification SMS: {str(e)}")
            return False

# Initialize SMS service
sms_service = SMSService()
