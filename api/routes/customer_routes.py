"""
Customer API Routes

FastAPI routes for customer-related operations.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from core.config.logging_config import get_logger
from infrastructure.redis.redis_client import redis_client
from services.data_processing.customer_processor import CustomerDataProcessor

logger = get_logger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = await redis_client.health_check()
    return {
        "status": "healthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/sessions/{stream_id}")
async def get_customer_session(stream_id: str):
    """Get customer session data by stream ID"""
    try:
        session_data = await redis_client.get_customer_session(stream_id)
        if session_data:
            return {"status": "success", "data": session_data}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error retrieving session {stream_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/events")
async def create_customer_event(event_data: Dict[Any, Any]):
    """Create a new customer event"""
    try:
        event_type = event_data.get('event_type')
        if not event_type:
            raise HTTPException(status_code=400, detail="event_type is required")
        
        stream_id = event_data.get('stream_id')
        data = event_data.get('data', {})
        
        # Publish event to Redis
        success = await redis_client.publish_event(event_type, data, stream_id)
        
        if success:
            return {"status": "success", "message": f"Event {event_type} published successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate")
async def validate_customer_data(customer_data: Dict[Any, Any]):
    """Validate customer data using the schema"""
    try:
        processor = CustomerDataProcessor()
        validated_data, error = processor.process_customer_data(customer_data)
        
        if validated_data:
            return {
                "status": "success",
                "message": "Customer data validated successfully",
                "data": {
                    "client_name": validated_data.client_name,
                    "phone_number": validated_data.phone_number,
                    "email": getattr(validated_data, 'email', None),
                    "address": validated_data.address,
                    "reason_calling": validated_data.reason_calling,
                    "preferred_contact_method": validated_data.preferred_contact_method
                }
            }
        else:
            return {
                "status": "error",
                "message": "Validation failed",
                "error": error
            }
            
    except Exception as e:
        logger.error(f"Error validating customer data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
