"""
Twilio API Routes

FastAPI routes for Twilio voice call handling and audio streaming.
"""

import os
import json
import base64
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect
import websockets
from core.config.logging_config import get_logger
from core.config.settings import settings
from services import OwnerService, BusinessService, twilio_service
from infrastructure.redis.redis_client import redis_client
from typing import Optional
from twilio.rest.api.v2010.account.call import CallInstance
from db.database import get_db
from models import Business, Owner
from sqlalchemy.orm import Session

PREFIX = "/twilio"
logger = get_logger(__name__)
router = APIRouter(prefix=PREFIX, tags=["twilio"])

# Audio files directory
AUDIO_FILES_DIR = "/root/voice-agent/demo/audio_files"
SHOW_TIMING_MATH = False
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'response.function_call_arguments.done'
]

TOOLS = [
    {
        "type": "function",
        "name": "gather_client_information",
        "description": "Collect and store client information including name, phone, address, reason for calling",
        "parameters": {
            "type": "object",
            "properties": {
                "full_name": {
                    "type": "string",
                    "description": "Client's full name"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Client's phone number"
                },
                "address": {
                    "type": "string",
                    "description": "Client's address"
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
            "required": ["full_name", "reason_calling", "preferred_contact_method"]
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
                "preferred_date": {"type": "string", "description": "Client's preferred date"},
                "preferred_time": {"type": "string", "description": "Client's preferred time"},
                "meeting_type": {"type": "string", "enum": ["phone", "video", "in_person"]},
                "address": {"type": "string", "description": "Client's address"},
                "notes": {"type": "string", "description": "Additional notes about the client or their request"},
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
                "notes": {"type": "string"},
                "business_email": {"type": "string"},
                "business_phone": {"type": "string"}
            },
            "required": ["client_data"]
        }
    }
]

class TwilioClient:    
    @router.post("/incoming-call")
    async def incoming_call(request: Request, db: Session = Depends(get_db)):
        """Handle incoming call and return TwiML response to connect to Media Stream."""
        response = VoiceResponse()        

        connect = Connect()
        ws_url = f'wss://{request.url.hostname}{PREFIX}/media-stream'
        connect.stream(url=ws_url)
        response.append(connect)
    
        return HTMLResponse(content=str(response), media_type="application/xml")
    
    @router.get("/call-status")
    async def call_status( request: Request):
        """Handle Twilio call status webhooks"""
        try:
            form_data = await request.form()
            
            call_sid = form_data.get("CallSid", "unknown")
            call_status = form_data.get("CallStatus", "unknown")
            call_duration = form_data.get("CallDuration", "0")
            
            logger.info(f"📞 Call {call_sid} status: {call_status} (duration: {call_duration}s)")
            
            # Update call status in Redis
            status_data = {
                "call_sid": call_sid,
                "status": call_status,
                "duration": call_duration,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            await redis_client.publish_event("call_status", status_data, call_sid)
            
            return {"status": "success", "message": "Call status updated"}
            
        except Exception as e:
            logger.error(f"❌ Error handling call status: {e}")
            raise HTTPException(status_code=500, detail="Failed to update call status")

    @router.get("/audio/{filename}")
    async def get_audio(filename: str):
        """Serve audio files for Twilio calls"""
        try:
            file_path = os.path.join(AUDIO_FILES_DIR, filename)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Audio file not found")
            
            # Validate filename to prevent directory traversal
            if ".." in filename or "/" in filename:
                raise HTTPException(status_code=400, detail="Invalid filename")
            
            logger.info(f"🎵 Serving audio file: {filename}")
            return FileResponse(file_path, media_type="audio/mpeg")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error serving audio file {filename}: {e}")
            raise HTTPException(status_code=500, detail="Failed to serve audio file")


@router.post("/voice-webhook")
async def voice_webhook(request: Request):
    """Generic voice webhook for advanced Twilio voice features"""
    try:
        form_data = await request.form()
        
        # Extract webhook data
        webhook_type = form_data.get("webhook_type", "unknown")
        call_sid = form_data.get("CallSid", "unknown")
        
        logger.info(f"🔗 Voice webhook received: {webhook_type} for call {call_sid}")
        
        # Handle different webhook types
        if webhook_type == "speech":
            # Handle speech recognition results
            speech_result = form_data.get("SpeechResult", "")
            confidence = form_data.get("Confidence", "0")
            
            speech_data = {
                "call_sid": call_sid,
                "speech_result": speech_result,
                "confidence": confidence,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            await redis_client.publish_event("speech_result", speech_data, call_sid)
            
        elif webhook_type == "gather":
            # Handle gather input
            digits = form_data.get("Digits", "")
            
            gather_data = {
                "call_sid": call_sid,
                "digits": digits,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            await redis_client.publish_event("gather_result", gather_data, call_sid)
        
        return {"status": "success", "message": f"Webhook {webhook_type} processed"}
        
    except Exception as e:
        logger.error(f"❌ Error processing voice webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket, 
                              db: Session = Depends(get_db)):
    """Handle WebSocket connections between Twilio and OpenAI."""
    async def recieve_call_sid() -> str:
        """Receive the stream SID from the first message from Twilio."""
        try:
            message = await websocket.receive_text()
            message = await websocket.receive_text()
            data = json.loads(message)
            if data['event'] == 'start':
                return data['start']['callSid']
        except Exception as e:
            logger.error(f"❌ Error receiving stream SID: {e}")
            return None
        return None
    
    print("Client connected")
    await websocket.accept()
    
    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-06-03',
        additional_headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        call: Optional[CallInstance] = None
        forwarded_from: Optional[str] = settings.FORWARDED_FROM
        owner = None
        business = None
        call_sid = None
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp, call_sid, forwarded_from, owner, business
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
                        call_sid = data['start']['callSid']
                        call = twilio_service.get_call(call_sid)
                        if call.forwarded_from != call.to:
                            forwarded_from = call.forwarded_from
                        business = BusinessService.get_business(db, forwarded_from)
                        owner = OwnerService.get_owner(db, business.owner_id)
                        await initialize_session(openai_ws, owner, business)
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
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio, call_sid, owner, business
            should_end = False
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    # Handle function calls
                    if response.get('type') == 'response.function_call_arguments.done':
                        function_name = response.get('name')
                        arguments = json.loads(response.get('arguments', '{}'))
                        
                        # Process the function call and extract customer data
                        result = await handle_function_call(function_name, arguments, stream_sid, call_sid, owner, business)
                        
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
                        should_end = True
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
                        if last_assistant_item:
                            await handle_speech_started_event()
                if should_end:
                    await twilio_service.hangup_call(call_sid)
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
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


async def format_prompt(owner: Owner, business: Business) -> str:
    """Format the prompt for the session."""
    default_hours = """
    יום ראשון - יום חמישי: 8:00 - 17:00
    יום שישי: 09:00-13:00
    """
    return settings.SYSTEM_MESSAGE.format(
        language=settings.LANGUAGE,
        business_name=business.name,
        business_scope=business.scope or "עסק כללי",
        business_phone=business.callout_phone or "לא צויין",
        business_address="לא צויין" if not business.address else business.address,
        business_city="לא צויין" if not business.city else business.city,
        business_country="לא צויין" if not business.country else business.country,
        business_webpage="לא צויין" if not business.webpage_url else business.webpage_url,
        owner_email="לא צויין" if not owner.email else owner.email,
        business_services=business.services,
        business_activity_areas=business.activity_areas,
        business_tagline="לא צויין" if not business.tagline else business.tagline,
        business_description="לא צויין" if not business.description else business.description,
        business_hours=default_hours if not business.hours else business.hours,
        business_owner_name=owner.name
    )
async def initialize_session(openai_ws, owner: Optional[Owner] = None, business: Optional[Business] = None):
    """Control initial session with OpenAI."""
    prompt = await format_prompt(owner, business) if owner and business else settings.SYSTEM_MESSAGE
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": settings.VOICE,
            "instructions": prompt,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools": TOOLS
        }
    }
    await openai_ws.send(json.dumps(session_update))


async def handle_function_call(function_name, 
                               arguments, 
                               stream_sid: int, 
                               call_sid: str,
                               owner: Optional[Owner] = None, 
                               business: Optional[Business] = None):
    """Handle function calls from OpenAI and extract customer data"""
    print(f"\n🔧 Function called: {function_name}")
    print(f"📝 Arguments: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
    
    if function_name == "gather_client_information":
        try:
            # Validate customer data using schema
            from data_types import CustomerCallSchema
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
            
            # Publish validated data to Redis for downstream processing
            await redis_client.publish_event('customer_data', arguments, stream_sid)
            await redis_client.store_customer_session(stream_sid or "unknown", {
                **arguments,
                "timestamp": datetime.now().isoformat(),
                "validation_status": "valid",
                "call_sid": call_sid
            })
            
            return {
                "status": "success",
                "message": "Customer information collected and validated successfully",
                "data_collected": list(arguments.keys()),
                "validation_status": "passed"
            }
            
        except Exception as validation_error:
            logger.error(f"❌ Customer data validation failed: {validation_error}")
            
            # Publish with validation error for manual review
            await redis_client.publish_event('customer_data_invalid', {
                **arguments, 
                "validation_error": str(validation_error)
            }, stream_sid)
            
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
        await redis_client.publish_event('meeting_scheduled', arguments, stream_sid, call_sid)
        
        return {
            "status": "success",
            "message": f"Meeting scheduled for {arguments.get('client_name')} on {arguments.get('preferred_date')} at {arguments.get('preferred_time')}"
        }
    
    elif function_name == "send_business_email":
        print(f"\n📧 EMAIL NOTIFICATION SENT")
        print(f"Priority: {arguments.get('priority', 'medium')}")
        
        # Publish email request to Redis
        await redis_client.publish_event('email_request', arguments, stream_sid, call_sid)
        
        return {
            "status": "success",
            "message": "Business email sent with client details"
        }
    
    return {"status": "error", "message": "Unknown function"}
