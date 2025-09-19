from contextlib import asynccontextmanager
import os
import json
import base64
import asyncio
import websockets
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv
from datetime import datetime
import logging
from data_types import CustomerCallSchema
from typing import Dict, Any
import uuid

from services.redis_consumer_service import RedisConsumerService

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 8000))
LANGUAGE = os.getenv('LANGUAGE', 'he-IL')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Redis configuration
REDIS_CHANNELS = {
    'customer_data': 'customer:data:new',
    'customer_data_invalid': 'customer:data:invalid', 
    'meeting_scheduled': 'customer:meeting:scheduled', 
    'email_request': 'customer:email:request',
    'high_priority': 'customer:priority:high'
}

# Customer data storage (in production, use a database)
customer_data_store = {}

# Setup logging for customer data
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = None

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Connected to Redis successfully")
        return redis_client
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return None

async def publish_customer_event(event_type: str, data: Dict[Any, Any], stream_id: str = None):
    """Publish customer events to Redis for downstream processing"""
    if not redis_client:
        logger.warning("Redis not available, skipping event publication")
        return False
    
    try:
        # Create event payload
        event_payload = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'stream_id': stream_id,
            'data': data
        }
        
        # Publish to specific channel based on event type
        channel = REDIS_CHANNELS.get(event_type, 'customer:general')
        
        # Publish the event
        await redis_client.publish(channel, json.dumps(event_payload, ensure_ascii=False))
        
        # Also store in Redis for persistence with TTL (24 hours)
        key = f"customer:session:{stream_id or 'unknown'}:{event_payload['event_id']}"
        await redis_client.setex(key, 86400, json.dumps(event_payload, ensure_ascii=False))
        
        # Check for high priority and publish to priority channel
        if data.get('urgency') in ['high', 'urgent']:
            await redis_client.publish(REDIS_CHANNELS['high_priority'], json.dumps(event_payload, ensure_ascii=False))
        
        logger.info(f"📡 Published event '{event_type}' to Redis channel '{channel}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to publish to Redis: {e}")
        return False

async def store_customer_session(stream_id: str, data: Dict[Any, Any]):
    """Store complete customer session data in Redis"""
    if not redis_client:
        return False
    
    try:
        # Store session data with 7 days TTL
        session_key = f"customer:session:{stream_id}"
        await redis_client.setex(session_key, 604800, json.dumps(data, ensure_ascii=False))
        
        # Add to customer index for easy lookup
        customer_name = data.get('client_name', '').strip()
        phone = data.get('phone_number', '').strip()
        
        if customer_name:
            await redis_client.sadd(f"customer:index:name:{customer_name.lower()}", stream_id)
        if phone:
            await redis_client.sadd(f"customer:index:phone:{phone}", stream_id)
        
        return True
    except Exception as e:
        logger.error(f"Failed to store customer session: {e}")
        return False

SYSTEM_MESSAGE = (
    f"""
אתה סוכן קול מקצועי שמדבר {LANGUAGE} עבור עסק. מטרתך היא:

לקבל את המתקשרים בצורה חמה ומקצועית
להבין מדוע הם מתקשרים ואיך העסק שלך יכול לעזור
לאסוף מידע חיוני על הלקוח:
- שם מלא
- מספר טלפון
- כתובת (אם רלוונטי)
- תיאור מפורט של הבעיה או הצורך
- שיטת יצירת הקשר המועדפת

בהתבסס על השיחה, לבצע אחד מהבאים:
- לקבוע פגישה עם העסק (אם הם רוצים לתאם) ולציין שקיום הפגישה מותנה באישור בעל העסק
- לשלוח מידע מפורט למייל העסקי למעקב

בשני המקרים יש לודא את הפרטים של הלקוח לפני ביצוע
תמיד להיות מנומס, מקצועי ומועיל
לשאול שאלות הבהרה בעת הצורך
לאשר את כל המידע לפני ההמשך

השתמש בכלים הזמינים כדי:
- gather_client_information: לאסוף ולשמור פרטי לקוח
- set_up_meeting: לקבוע פגישות לפי בקשה
- send_business_email: לשלוח פרטי לקוח לעסק למעקב
- summarize_conversation: לספק סיכום וסיכומי המשך

זכור: מטרתך היא לספק שירות לקוחות מצוין תוך איסוף כל המידע הנדרש לעסק כדי לבצע מעקב יעיל.
    """
)

VOICE = 'Coral'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'response.function_call_arguments.done'
]
SHOW_TIMING_MATH = False
WELCOME_AUDIO_FILE_PATH = "/root/voice-agent/demo/audio_files/welcome.mp3"

if not os.path.exists(WELCOME_AUDIO_FILE_PATH):
    print(f"Welcome audio file not found at {WELCOME_AUDIO_FILE_PATH}")
    print("Please run the create_default_audio.py script to generate the audio files")
    exit(1)


if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Server is starting...")
    yield
    # Shutdown code
    print("Server is shutting down...")
    
app = FastAPI(lifespan=lifespan)

def print_customer_data(data, stream_id=None):
    """Print customer data in a formatted way to terminal"""
    print("\n" + "="*60)
    print("🎯 CUSTOMER DATA EXTRACTED")
    print("="*60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if stream_id:
        print(f"📞 Stream ID: {stream_id}")
    print("-" * 60)
    
    if isinstance(data, dict):
        for key, value in data.items():
            if value:  # Only print non-empty values
                emoji = get_field_emoji(key)
                print(f"{emoji} {key.replace('_', ' ').title()}: {value}")
    
    print("="*60)
    print()
    
    # Also log to file for persistence
    logger.info(f"Customer data extracted: {json.dumps(data, indent=2, ensure_ascii=False)}")

def get_field_emoji(field_name):
    """Get appropriate emoji for field names"""
    emoji_map = {
        'client_name': '👤',
        'phone_number': '📱',
        'address': '🏠',
        'email': '📧',
        'reason_calling': '💭',
        'preferred_contact_method': '📞',
        'additional_notes': '📝'

    }
    return emoji_map.get(field_name.lower(), '📋')

# Define the tools/functions that the AI can use
TOOLS = [
    {
        "type": "function",
        "name": "gather_client_information",
        "description": "Collect and store client information including name, phone, address, reason for calling",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {
                    "type": "string",
                    "description": "Client's full name"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Client's phone number"
                },
                "address": {
                    "type": "string",
                    "description": "Client's address (if relevant)"
                },
                "email": {
                    "type": "string",
                    "description": "Client's email address"
                },
                "reason_calling": {
                    "type": "string",
                    "description": "Detailed description of why the client is calling"
                },
                "preferred_contact_method": {
                    "type": "string",
                    "enum": ["Whatsapp", "Email", "Phone"],
                    "description": "Client's preferred method of contact"
                },
                "additional_notes": {
                    "type": "string",
                    "description": "Additional notes about the client or their request"
                }
            },
            "required": ["client_name", "reason_calling", "preferred_contact_method"]
        }
    },
    {
        "type": "function",
        "name": "set_up_meeting",
        "description": "Schedule a meeting with the client",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "preferred_date": {"type": "string"},
                "preferred_time": {"type": "string"},
                "meeting_type": {"type": "string", "enum": ["phone", "video", "in_person"]},
                "notes": {"type": "string"}
            },
            "required": ["client_name", "preferred_date", "preferred_time"]
        }
    },
    {
        "type": "function",
        "name": "send_business_email",
        "description": "Send client details to business email for follow-up",
        "parameters": {
            "type": "object",
            "properties": {
                "client_data": {"type": "object"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "notes": {"type": "string"}
            },
            "required": ["client_data"]
        }
    }
]

async def handle_function_call(function_name, arguments, stream_id=None):
    """Handle function calls from OpenAI and extract customer data"""
    print(f"\n🔧 Function called: {function_name}")
    print(f"📝 Arguments: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
    
    if function_name == "gather_client_information":
        try:
            # Validate customer data using schema
            schema = CustomerCallSchema()
            
            # Prepare data for validation (ensure timestamp is included)
            validation_data = {
                **arguments,
                "timestamp": datetime.now().isoformat()
            }
            
            # Map fields to match schema
            field_mapping = {
                'preferred_contact': 'preferred_contact_method',
                'notes': 'additional_notes'
            }
            
            for old_key, new_key in field_mapping.items():
                if old_key in validation_data:
                    validation_data[new_key] = validation_data.pop(old_key)
            
            # Validate the data
            customer_call = schema.load(validation_data)
            
            # Store the validated customer data locally
            customer_data = {
                **arguments,
                "timestamp": datetime.now().isoformat(),
                "stream_id": stream_id,
                "validation_status": "valid"
            }
            customer_data_store[stream_id or "unknown"] = customer_data
            
            # Print the extracted data to terminal
            print_customer_data(arguments, stream_id)
            print(f"✅ Customer data validation: PASSED")
            
            # Publish validated data to Redis for downstream processing
            await publish_customer_event('customer_data', arguments, stream_id)
            await store_customer_session(stream_id or "unknown", customer_data)
            
            return {
                "status": "success",
                "message": "Customer information collected and validated successfully",
                "data_collected": list(arguments.keys()),
                "validation_status": "passed"
            }
            
        except Exception as validation_error:
            logger.error(f"❌ Customer data validation failed: {validation_error}")
            
            # Store invalid data with error info
            customer_data = {
                **arguments,
                "timestamp": datetime.now().isoformat(),
                "stream_id": stream_id,
                "validation_status": "invalid",
                "validation_error": str(validation_error)
            }
            customer_data_store[stream_id or "unknown"] = customer_data
            
            # Still print data but mark as invalid
            print_customer_data(arguments, stream_id)
            print(f"❌ Customer data validation: FAILED - {validation_error}")
            
            # Publish with validation error for manual review
            await publish_customer_event('customer_data_invalid', {
                **arguments, 
                "validation_error": str(validation_error)
            }, stream_id)
            
            return {
                "status": "warning",
                "message": "Customer information collected but validation failed. Please verify data manually.",
                "data_collected": list(arguments.keys()),
                "validation_status": "failed",
                "validation_error": str(validation_error)
            }
    
    elif function_name == "set_up_meeting":
        print(f"\n📅 MEETING SCHEDULED")
        print(f"Client: {arguments.get('client_name')}")
        print(f"Date: {arguments.get('preferred_date')}")
        print(f"Time: {arguments.get('preferred_time')}")
        print(f"Type: {arguments.get('meeting_type', 'Not specified')}")
        
        # Publish meeting event to Redis
        await publish_customer_event('meeting_scheduled', arguments, stream_id)
        
        return {
            "status": "success",
            "message": f"Meeting scheduled for {arguments.get('client_name')} on {arguments.get('preferred_date')} at {arguments.get('preferred_time')}"
        }
    
    elif function_name == "send_business_email":
        print(f"\n📧 EMAIL NOTIFICATION SENT")
        print(f"Priority: {arguments.get('priority', 'medium')}")
        if 'client_data' in arguments:
            print_customer_data(arguments['client_data'], stream_id)
        
        # Publish email request to Redis
        await publish_customer_event('email_request', arguments, stream_id)
        
        return {
            "status": "success",
            "message": "Business email sent with client details"
        }
    
    return {"status": "error", "message": "Unknown function"}

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(f"/root/riley/audio_files/{filename}")

@app.get("/customer-data")
async def get_customer_data():
    """API endpoint to retrieve collected customer data"""
    return {"customer_data": customer_data_store}

@app.get("/redis-stats")
async def get_redis_stats():
    """API endpoint to get Redis connection stats"""
    if not redis_client:
        return {"status": "disconnected"}
    
    try:
        info = await redis_client.info()
        return {
            "status": "connected",
            "redis_version": info.get('redis_version'),
            "connected_clients": info.get('connected_clients'),
            "total_commands_processed": info.get('total_commands_processed')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    file_name = os.path.basename(WELCOME_AUDIO_FILE_PATH)
    server_url = os.getenv("SERVER_URL", "https://2aa6b1c77942.ngrok-free.app")
    response.play(f"{server_url}/audio/{file_name}")
    response.pause(length=1)
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-06-03",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.state == websockets.State.OPEN:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.state == websockets.State.OPEN:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    # Handle function calls
                    if response.get('type') == 'response.function_call_arguments.done':
                        function_name = response.get('name')
                        arguments = json.loads(response.get('arguments', '{}'))
                        
                        # Process the function call and extract customer data
                        result = await handle_function_call(function_name, arguments, stream_sid)
                        
                        # Send function result back to OpenAI
                        function_result = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": response.get('call_id'),
                                "output": json.dumps(result)
                            }
                        }
                        await openai_ws.send(json.dumps(function_result))

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        if response.get('item_id'):
                            last_assistant_item = response['item_id']

                        await send_mark(websocket, stream_sid)

                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "tools": TOOLS,
            "temperature": 0.6,
            "max_output_tokens": 2000,
            "automatic_turn_detection": "semantic",
            "eagerness": "auto",
            "noise_reduction": "none"
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

async def main():
    """Main function to run the Redis consumer service"""
    import uvicorn
    await init_redis()
    consumer = RedisConsumerService()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    try:
        await consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("⏹️  Shutting down...")
    finally:
        await consumer.stop()
        
if __name__ == "__main__":
    asyncio.run(main())
    # uvicorn.run(app, host="0.0.0.0", port=PORT)