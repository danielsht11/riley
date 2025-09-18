"""
Redis Client Module

Manages Redis connections and provides utility functions for Redis operations.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import redis.asyncio as redis
from core.config.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for async operations"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.client.ping()
            self.connected = True
            logger.info("✅ Connected to Redis successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.connected = False
            logger.info("✅ Disconnected from Redis")
    
    async def publish_event(self, event_type: str, data: Dict[Any, Any], stream_id: str = None, call_sid: str = None) -> bool:
        """Publish customer events to Redis for downstream processing"""
        if not self.connected or not self.client:
            logger.warning("Redis not connected, skipping event publication")
            return False
        
        try:
            # Create event payload
            event_payload = {
                'event_id': str(uuid.uuid4()),
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'stream_id': stream_id,
                'call_sid': call_sid,
                'data': data
            }
            
            # Publish to specific channel based on event type
            channel = settings.REDIS_CHANNELS.get(event_type, 'customer:general')
            
            # Publish the event
            await self.client.publish(channel, json.dumps(event_payload, ensure_ascii=False))
            
            # Also store in Redis for persistence with TTL (24 hours)
            key = f"customer:session:{stream_id or 'unknown'}:{event_payload['event_id']}"
            await self.client.setex(key, 86400, json.dumps(event_payload, ensure_ascii=False))
            
            # Check for high priority and publish to priority channel
            if data.get('urgency') in ['high', 'urgent']:
                await self.client.publish(settings.REDIS_CHANNELS['high_priority'], 
                                       json.dumps(event_payload, ensure_ascii=False))
            
            logger.info(f"📡 Published event '{event_type}' to Redis channel '{channel}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
            return False
    
    async def store_customer_session(self, stream_id: str, data: Dict[Any, Any]) -> bool:
        """Store complete customer session data in Redis"""
        if not self.connected or not self.client:
            return False
        
        try:
            session_key = f"customer:session:{stream_id}"
            session_data = {
                'stream_id': stream_id,
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'status': 'active'
            }
            
            # Store with 24-hour TTL
            await self.client.setex(session_key, 86400, json.dumps(session_data, ensure_ascii=False))
            logger.info(f"💾 Stored customer session: {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store customer session: {e}")
            return False
    
    async def get_customer_session(self, stream_id: str) -> Optional[Dict[Any, Any]]:
        """Retrieve customer session data from Redis"""
        if not self.connected or not self.client:
            return None
        
        try:
            session_key = f"customer:session:{stream_id}"
            session_data = await self.client.get(session_key)
            if session_data:
                return json.loads(session_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve customer session: {e}")
            return None
    
    async def subscribe_to_channels(self, channels: list) -> redis.client.PubSub:
        """Subscribe to Redis channels for pub/sub"""
        if not self.connected or not self.client:
            raise RuntimeError("Redis not connected")
        
        pubsub = self.client.pubsub()
        for channel in channels:
            await pubsub.subscribe(channel)
            logger.info(f"📡 Subscribed to channel: {channel}")
        
        return pubsub
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()
