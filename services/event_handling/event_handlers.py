"""
Event Handlers Module

Handles different types of events in the voice agent system.
"""

from datetime import datetime
from typing import Dict, Any
from core.config.logging_config import get_logger
from services.communication.email_service import EmailService
from services.communication.whatsapp_service import WhatsAppService
from services.data_processing.customer_processor import CustomerDataProcessor

logger = get_logger(__name__)


class BaseEventHandler:
    """Base class for event handlers"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")
    
    async def handle_event(self, event_data: Dict[Any, Any]) -> None:
        """Handle a specific event type"""
        raise NotImplementedError


class CustomerDataEventHandler(BaseEventHandler):
    """Handles customer data events"""
    
    def __init__(self, data_processor: CustomerDataProcessor, 
                 email_service: EmailService,
                 whatsapp_service: WhatsAppService):
        super().__init__("CustomerDataEventHandler")
        self.data_processor = data_processor
        self.email_service = email_service
        self.whatsapp_service = whatsapp_service
    
    async def handle_event(self, event_data: Dict[Any, Any]) -> None:
        """Handle new customer data events"""
        self.logger.info("📋 Processing customer data event")
        
        # Process and validate customer data
        customer_call, error = self.data_processor.process_customer_data(event_data['data'])
        
        if customer_call:
            # Send email notification
            subject = f"New Customer Contact: {customer_call.full_name}"
            email_data = {
                'timestamp': event_data['timestamp'],
                'stream_id': event_data.get('stream_id'),
                'full_name': customer_call.full_name,
                'phone_number': customer_call.phone_number,
                'address': customer_call.address,
                'email': getattr(customer_call, 'email', ''),
                'reason_calling': customer_call.reason_calling,
                'preferred_contact_method': customer_call.preferred_contact_method,
                'additional_notes': customer_call.additional_notes or '',
                'urgency': event_data['data'].get('urgency', 'medium')
            }
            
            self.email_service.send_email(subject, 'customer_data', email_data)
            
            # Send WhatsApp if preferred contact method is WhatsApp
            if customer_call.preferred_contact_method.lower() == 'whatsapp':
                whatsapp_data = {
                    'timestamp': datetime.fromisoformat(event_data['timestamp']).strftime('%Y-%m-%d %H:%M'),
                    'full_name': customer_call.full_name,
                    'phone_number': customer_call.phone_number,
                    'address': customer_call.address,
                    'reason_calling': customer_call.reason_calling,
                    'preferred_contact_method': customer_call.preferred_contact_method
                }
                
                # Send to business WhatsApp
                from core.config.settings import settings
                business_whatsapp = settings.BUSINESS_WHATSAPP_NUMBER
                if business_whatsapp:
                    self.whatsapp_service.send_whatsapp(business_whatsapp, 'customer_data', whatsapp_data)
        else:
            self.logger.warning(f"⚠️ Customer data validation failed: {error}")


class InvalidCustomerDataEventHandler(BaseEventHandler):
    """Handles invalid customer data events"""
    
    def __init__(self, email_service: EmailService):
        super().__init__("InvalidCustomerDataEventHandler")
        self.email_service = email_service
    
    async def handle_event(self, event_data: Dict[Any, Any]) -> None:
        """Handle invalid customer data that needs manual review"""
        self.logger.warning("⚠️ Processing invalid customer data event")
        
        subject = "VALIDATION FAILED - Customer Data Needs Review"
        email_data = {
            **event_data['data'],
            'timestamp': event_data['timestamp'],
            'stream_id': event_data.get('stream_id'),
            'validation_error': event_data['data'].get('validation_error', 'Unknown validation error')
        }
        
        self.email_service.send_email(subject, 'customer_data_invalid', email_data)


class MeetingScheduledEventHandler(BaseEventHandler):
    """Handles meeting scheduled events"""
    
    def __init__(self, email_service: EmailService):
        super().__init__("MeetingScheduledEventHandler")
        self.email_service = email_service
    
    async def handle_event(self, event_data: Dict[Any, Any]) -> None:
        """Handle meeting scheduled events"""
        self.logger.info("📅 Processing meeting scheduled event")
        
        data = event_data['data']
        subject = f"Meeting Scheduled: {data.get('client_name', 'Unknown Client')}"
        
        email_data = {
            **data,
            'timestamp': event_data['timestamp']
        }
        
        self.email_service.send_email(subject, 'meeting_scheduled', email_data)


class HighPriorityEventHandler(BaseEventHandler):
    """Handles high priority customer contacts"""
    
    def __init__(self, email_service: EmailService, 
                 whatsapp_service: WhatsAppService):
        super().__init__("HighPriorityEventHandler")
        self.email_service = email_service
        self.whatsapp_service = whatsapp_service
    
    async def handle_event(self, event_data: Dict[Any, Any]) -> None:
        """Handle high priority customer contacts"""
        self.logger.warning("🚨 Processing HIGH PRIORITY event")
        
        data = event_data['data']
        subject = f"🚨 HIGH PRIORITY: {data.get('full_name', 'Unknown Customer')}"
        
        email_data = {
            **data,
            'timestamp': event_data['timestamp'],
            'stream_id': event_data.get('stream_id')
        }
        
        # Send urgent email
        self.email_service.send_email(subject, 'high_priority', email_data)
        
        # Send WhatsApp notification for high priority
        from core.config.settings import settings
        business_whatsapp = settings.BUSINESS_WHATSAPP_NUMBER
        if business_whatsapp:
            whatsapp_data = {
                'full_name': data.get('full_name', 'Unknown'),
                'phone_number': data.get('phone_number', 'No phone'),
                'reason_calling': data.get('reason_calling', 'Not specified'),
                'urgency': data.get('urgency', 'HIGH')
            }
            self.whatsapp_service.send_whatsapp(business_whatsapp, 'high_priority', whatsapp_data)
