"""
Voice Agent Main Entry Point

Main entry point for the voice agent system.
"""

import asyncio
import uvicorn
from core.config.settings import settings
from core.config.logging_config import setup_logging
from services.redis_consumer_service import create_redis_consumer_service
from app import app


async def run_consumer_service():
    """Run the Redis consumer service"""
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


async def main():
    """Main function to run the voice agent system"""
    # Setup logging
    setup_logging(level="INFO")
    
    print("🚀 Starting Voice Agent System...")
    print(f"📡 Server will run on {settings.HOST}:{settings.PORT}")
    
    # Start the consumer service in the background
    consumer_task = asyncio.create_task(run_consumer_service())
    
    try:
        # Start the FastAPI server
        config = uvicorn.Config(
            app=app,
            host=settings.HOST,
            port=settings.PORT,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await asyncio.create_task(server.serve())
    except KeyboardInterrupt:
        print("⏹️  Shutting down voice agent system...")
    finally:
        # Cancel the consumer task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

        
if __name__ == "__main__":
    asyncio.run(main())