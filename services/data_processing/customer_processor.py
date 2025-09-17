"""
Customer Data Processor Module

Handles processing and validation of customer data using schemas.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from marshmallow import ValidationError
from data_types import CustomerCall, CustomerCallSchema
from core.config.logging_config import get_logger

logger = get_logger(__name__)


class CustomerDataProcessor:
    """Processes and validates customer data using CustomerCall schema"""
    
    def __init__(self):
        self.schema = CustomerCallSchema()
    
    def process_customer_data(self, raw_data: Dict[Any, Any]) -> Tuple[Optional[CustomerCall], Optional[str]]:
        """Process and validate customer data using CustomerCall schema"""
        try:
            # Prepare data for validation
            validation_data = dict(raw_data)
            
            # Ensure timestamp is present
            if 'timestamp' not in validation_data:
                validation_data['timestamp'] = datetime.now().isoformat()
            
            # Map field names to schema expectations
            field_mapping = {
                'preferred_contact': 'preferred_contact_method',
                'notes': 'additional_notes'
            }
            
            for old_key, new_key in field_mapping.items():
                if old_key in validation_data:
                    validation_data[new_key] = validation_data.pop(old_key)
            
            # Validate and create CustomerCall object
            customer_call = self.schema.load(validation_data)
            
            logger.info(f"✅ Customer data validated successfully for {customer_call.full_name}")
            return customer_call, None
            
        except ValidationError as e:
            error_msg = f"Validation failed: {e.messages}"
            logger.error(f"❌ {error_msg}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return None, error_msg
    
    def extract_customer_info(self, conversation_text: str) -> Dict[str, Any]:
        """Extract customer information from conversation text"""
        # This is a simplified extraction - in production, you might use NLP/AI
        extracted_data = {
            'timestamp': datetime.now().isoformat(),
            'conversation_text': conversation_text
        }
        
        # Basic extraction logic (enhance with AI/NLP in production)
        if 'meeting' in conversation_text.lower() or 'schedule' in conversation_text.lower():
            extracted_data['meeting_request'] = True
        
        if 'urgent' in conversation_text.lower() or 'emergency' in conversation_text.lower():
            extracted_data['urgency'] = 'high'
        
        return extracted_data
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Basic phone number validation"""
        if not phone_number:
            return False
        
        # Remove common separators
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Basic validation (enhance with proper phone validation library)
        return len(cleaned) >= 10
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email:
            return False
        
        # Basic email format validation
        return '@' in email and '.' in email.split('@')[1]
