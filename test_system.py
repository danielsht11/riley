#!/usr/bin/env python3
"""
System Test Script

Simple test to verify all components are working correctly.
"""

import asyncio
import sys
from core.config.logging_config import setup_logging
from core.config.settings import settings


async def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    try:
        print(f"  ✅ Port: {settings.PORT}")
        print(f"  ✅ Host: {settings.HOST}")
        print(f"  ✅ Redis URL: {settings.REDIS_URL}")
        print(f"  ✅ Language: {settings.LANGUAGE}")
        print(f"  ✅ Voice: {settings.VOICE}")
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


async def test_redis_connection():
    """Test Redis connection"""
    print("🔴 Testing Redis connection...")
    try:
        from infrastructure.redis.redis_client import redis_client
        connected = await redis_client.connect()
        if connected:
            print("  ✅ Redis connected successfully")
            await redis_client.disconnect()
            return True
        else:
            print("  ❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"  ❌ Redis test error: {e}")
        return False


async def test_services():
    """Test service initialization"""
    print("⚙️  Testing services...")
    try:
        from services.communication.email_service import EmailService
        from services.communication.whatsapp_service import WhatsAppService
        from services.data_processing.customer_processor import CustomerDataProcessor
        
        email_service = EmailService()
        whatsapp_service = WhatsAppService()
        customer_processor = CustomerDataProcessor()
        
        print("  ✅ Email service initialized")
        print("  ✅ WhatsApp service initialized")
        print("  ✅ Customer processor initialized")
        
        # Test email service configuration
        if email_service.is_configured():
            print("  ✅ Email service configured")
        else:
            print("  ⚠️  Email service not configured (missing credentials)")
        
        # Test WhatsApp service configuration
        if whatsapp_service.is_configured():
            print("  ✅ WhatsApp service configured")
        else:
            print("  ⚠️  WhatsApp service not configured (missing Twilio credentials)")
        
        return True
    except Exception as e:
        print(f"  ❌ Service test error: {e}")
        return False


async def test_event_handlers():
    """Test event handler initialization"""
    print("🎯 Testing event handlers...")
    try:
        from services.event_handling.event_handlers import (  # noqa: F401
            CustomerDataEventHandler,
            InvalidCustomerDataEventHandler,
            MeetingScheduledEventHandler,
            HighPriorityEventHandler
        )
        
        print("  ✅ All event handlers imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ Event handler test error: {e}")
        return False


async def test_api_routes():
    """Test API route imports"""
    print("🌐 Testing API routes...")
    try:
        from api.routes.customer_routes import router as customer_router  # noqa: F401
        from api.routes.twilio_routes import router as twilio_router  # noqa: F401
        print("  ✅ Customer routes imported successfully")
        print("  ✅ Twilio routes imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ API route test error: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Starting Voice Agent System Tests...")
    print("=" * 50)
    
    setup_logging(level="INFO")
    
    tests = [
        ("Configuration", test_config),
        ("Redis Connection", test_redis_connection),
        ("Services", test_services),
        ("Event Handlers", test_event_handlers),
        ("API Routes", test_api_routes),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
