import os
import logging
from flask import flash

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manage API keys and service status"""
    
    @staticmethod
    def check_services_status():
        """Check status of all external services"""
        status = {
            'sms_enabled': bool(os.environ.get("TWILIO_ACCOUNT_SID") and 
                              os.environ.get("TWILIO_AUTH_TOKEN") and 
                              os.environ.get("TWILIO_PHONE_NUMBER")),
            'ai_enabled': bool(os.environ.get("OPENAI_API_KEY")),
            'database_enabled': bool(os.environ.get("DATABASE_URL"))
        }
        return status
    
    @staticmethod
    def get_missing_keys():
        """Get list of missing API keys"""
        missing = []
        
        if not os.environ.get("TWILIO_ACCOUNT_SID"):
            missing.append("TWILIO_ACCOUNT_SID")
        if not os.environ.get("TWILIO_AUTH_TOKEN"):
            missing.append("TWILIO_AUTH_TOKEN")
        if not os.environ.get("TWILIO_PHONE_NUMBER"):
            missing.append("TWILIO_PHONE_NUMBER")
        if not os.environ.get("OPENAI_API_KEY"):
            missing.append("OPENAI_API_KEY")
            
        return missing
    
    @staticmethod
    def generate_setup_message():
        """Generate setup message for missing services"""
        missing = APIKeyManager.get_missing_keys()
        status = APIKeyManager.check_services_status()
        
        messages = []
        
        if not status['sms_enabled']:
            messages.append("SMS notifications are disabled. Configure Twilio credentials to enable SMS alerts for admins and approval notifications.")
        
        if not status['ai_enabled']:
            messages.append("AI Assistant is disabled. Add OpenAI API key to enable automatic urgency analysis and approval note generation.")
        
        if missing:
            messages.append(f"Missing API keys: {', '.join(missing)}")
        
        return messages

api_key_manager = APIKeyManager()