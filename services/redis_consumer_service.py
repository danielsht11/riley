"""
Redis Consumer Service Module

Main service for consuming Redis events and routing them to appropriate handlers.
"""

import json
from typing import Dict, Any
from core.config.settings import settings
from core.config.logging_config import get_logger
from infrastructure.redis.redis_client import redis_client
from services.communication.email_service import EmailService
from services.communication.whatsapp_service import WhatsAppService
from services.data_processing.customer_processor import CustomerDataProcessor
from services.event_handling.event_handlers import (
    CustomerDataEventHandler,
    InvalidCustomerDataEventHandler,
    MeetingScheduledEventHandler,
    HighPriorityEventHandler
)

logger = get_logger(__name__)


class RedisConsumerService:
    """Redis pub/sub consumer service for handling various events"""
    
    def __init__(self):
        self.running = False
        self.email_service = EmailService()
        self.whatsapp_service = WhatsAppService()
        self.customer_processor = CustomerDataProcessor()
        
        # Initialize event handlers
        self.event_handlers: Dict[str, Any] = {}
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for different event types"""
        self.event_handlers = {
            'customer_data': CustomerDataEventHandler(
                self.customer_processor, 
                self.email_service, 
                self.whatsapp_service
            ),
            'customer_data_invalid': InvalidCustomerDataEventHandler(self.email_service),
            'meeting_scheduled': MeetingScheduledEventHandler(self.email_service),
            'high_priority': HighPriorityEventHandler(self.email_service, self.whatsapp_service)
        }
    
    async def initialize(self) -> bool:
        """Initialize the consumer service"""
        try:
            # Connect to Redis
            if not await redis_client.connect():
                return False
            
            logger.info("✅ RedisConsumerService initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RedisConsumerService: {e}")
            return False
    
    async def process_event(self, channel: str, message: str) -> None:
        """Process individual Redis events"""
        try:
            event_data = json.loads(message)
            event_type = event_data.get('event_type')
            
            logger.info(f"📨 Received event on {channel}: {event_type}")
            
            # Route to appropriate handler
            if event_type in self.event_handlers:
                await self.event_handlers[event_type].handle_event(event_data)
            elif channel == settings.REDIS_CHANNELS['high_priority']:
                await self.event_handlers['high_priority'].handle_event(event_data)
            else:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")
    
    async def start_consuming(self) -> None:
        """Start consuming Redis pub/sub messages"""
        if not redis_client.connected:
            logger.error("❌ Redis client not connected")
            return
        
        self.running = True
        
        try:
            # Subscribe to all channels
            pubsub = await redis_client.subscribe_to_channels(list(settings.REDIS_CHANNELS.values()))
            
            logger.info("🎯 Redis consumer service started - waiting for events...")
            
            while self.running:
                message = await pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    await self.process_event(channel, data)
                    
        except KeyboardInterrupt:
            logger.info("⏹️  Shutting down consumer service...")
        except Exception as e:
            logger.error(f"❌ Error in consumer service: {e}")
        finally:
            if 'pubsub' in locals():
                await pubsub.unsubscribe()
            logger.info("✅ Redis consumer service stopped")
    
    async def stop_consuming(self) -> None:
        """Stop consuming messages"""
        self.running = False
    
    async def shutdown(self) -> None:
        """Shutdown the service"""
        await self.stop_consuming()
        await redis_client.disconnect()
        logger.info("✅ RedisConsumerService shutdown complete")


# Factory function for creating services
def create_redis_consumer_service() -> RedisConsumerService:
    """Factory function to create a Redis consumer service"""
    return RedisConsumerService()
