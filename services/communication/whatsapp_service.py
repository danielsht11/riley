"""
WhatsApp Service Module

Handles WhatsApp communication using Twilio.
"""

from typing import Dict, Any
from twilio.rest import Client
from core.config.settings import settings
from core.config.logging_config import get_logger

logger = get_logger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages using Twilio"""
    
    def __init__(self):
        self.client = None
        self.whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER
        
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            logger.info("✅ Twilio WhatsApp service initialized")
        else:
            logger.warning("Twilio credentials not configured")
    
    # WhatsApp templates
    templates = {
        'customer_data': """🎯 *New Customer Contact*
        
📅 Time: {timestamp}
👤 Name: {client_name}
📱 Phone: {phone_number}
🏠 Address: {address}
💭 Reason: {reason_calling}
📞 Preferred: {preferred_contact_method}
    
✅ Data validated successfully
        """,
        
        'high_priority': """🚨 *HIGH PRIORITY CUSTOMER*

👤 {client_name}
📱 {phone_number}
⚡ Urgency: *{urgency}*

💭 {reason_calling}

*IMMEDIATE ACTION REQUIRED!*
        """,
        
        'meeting_scheduled': """📅 *Meeting Scheduled*

👤 Client: {client_name}
📅 Date: {preferred_date}
🕐 Time: {preferred_time}
📹 Type: {meeting_type}

⚠️ Please confirm with client before meeting time.
        """
    }
    
    def send_whatsapp(self, to_number: str, template_name: str, data: Dict[Any, Any]) -> bool:
        """Send WhatsApp message using template"""
        if not self.client:
            logger.warning("WhatsApp service not available")
            return False
        
        try:
            template = self.templates.get(template_name, "New update: {data}")
            message_content = template.format(**data)
            
            # Format WhatsApp number
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message = self.client.messages.create(
                body=message_content,
                from_=self.whatsapp_number,
                to=to_number
            )
            
            logger.info(f"✅ WhatsApp sent to {to_number}: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured"""
        return self.client is not None
