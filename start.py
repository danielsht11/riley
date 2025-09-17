#!/usr/bin/env python3
"""
Simple startup script for development

This script provides an easy way to start the voice agent system
in different modes.
"""

import sys
import asyncio
import uvicorn
from core.config.settings import settings
from core.config.logging_config import setup_logging


def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting Voice Agent API Server...")
    print(f"📡 Server will run on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )


def start_consumer_service():
    """Start only the Redis consumer service"""
    print("🔄 Starting Redis Consumer Service...")
    
    async def run_consumer():
        from services.redis_consumer_service import create_redis_consumer_service
        consumer = create_redis_consumer_service()
        
        try:
            if await consumer.initialize():
                await consumer.start_consuming()
            else:
                print("❌ Failed to initialize consumer service")
        except KeyboardInterrupt:
            print("⏹️  Shutting down consumer service...")
        finally:
            await consumer.shutdown()
    
    asyncio.run(run_consumer())


def start_full_system():
    """Start the full system (API + Consumer)"""
    print("🌟 Starting Full Voice Agent System...")
    
    async def run_full_system():
        from services.redis_consumer_service import create_redis_consumer_service
        consumer = create_redis_consumer_service()
        
        try:
            if await consumer.initialize():
                # Start consumer in background
                consumer_task = asyncio.create_task(consumer.start_consuming())
                
                # Start API server
                config = uvicorn.Config(
                    app="app:app",
                    host=settings.HOST,
                    port=settings.PORT,
                    log_level="info"
                )
                server = uvicorn.Server(config)
                await server.serve()
                
        except KeyboardInterrupt:
            print("⏹️  Shutting down full system...")
        finally:
            await consumer.shutdown()
    
    asyncio.run(run_full_system())


def main():
    """Main entry point"""
    setup_logging(level="INFO")
    
    if len(sys.argv) < 2:
        print("Usage: python start.py [api|consumer|full]")
        print("  api      - Start only the FastAPI server")
        print("  consumer - Start only the Redis consumer service")
        print("  full     - Start the complete system")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "api":
        start_api_server()
    elif mode == "consumer":
        start_consumer_service()
    elif mode == "full":
        start_full_system()
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: api, consumer, full")
        sys.exit(1)


if __name__ == "__main__":
    main()
