# Voice Agent with Twilio Integration

This voice agent now supports both local microphone input and Twilio phone call handling through webhooks.

## Features

- **Local Mode**: Original microphone-based voice agent for local testing
- **Twilio Mode**: Webhook-based phone call handling for production use
- **FastAPI Server**: RESTful API endpoints for Twilio integration
- **Speech Recognition**: Automatic speech-to-text via Twilio's speech input
- **Audio Playback**: Uses `response.play()` for high-quality audio responses
- **Dynamic Audio Generation**: Creates audio files on-demand using OpenAI TTS
- **Client Information Collection**: Automatically extracts structured client data from conversations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Default Audio Files

```bash
python create_default_audio.py
```

This creates the required audio files for system messages (welcome, fallback, error, etc.).

### 2. Environment Variables

Create a `.env` file with:

```bash
OPENAI_API_KEY=your_openai_api_key_here
# Optional: Set your Twilio credentials if needed
# TWILIO_ACCOUNT_SID=your_twilio_account_sid
# TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

### 3. Twilio Configuration

In your Twilio console, set the webhook URL for incoming calls to:
```
https://your-domain.com/incoming-call
```

**Important**: Make sure your server is accessible via HTTPS, as Twilio requires secure connections for webhooks.

## Running the Application

### Local Voice Agent Mode (Original Functionality)

```bash
python main.py
```

This runs the original microphone-based voice agent for local testing.

### Twilio Server Mode

```bash
# Option 1: Use the provided script
chmod +x run_twilio_server.sh
./run_twilio_server.sh

# Option 2: Set environment variable manually
export RUN_SERVER=true
python main.py
```

This starts the FastAPI server on port 8000 for Twilio webhooks.

## API Endpoints

### POST /incoming-call
- **Purpose**: Handles incoming Twilio calls
- **Action**: Creates a speech gathering session
- **Response**: TwiML XML for call handling

### POST /process-speech
- **Purpose**: Processes speech input from Twilio
- **Input**: Form data with `SpeechResult` field
- **Action**: Runs the voice agent workflow
- **Response**: TwiML XML with AI response

### GET /health
- **Purpose**: Health check endpoint
- **Response**: JSON status information

### GET /audio/{filename}
- **Purpose**: Serve audio files for Twilio playback
- **Input**: Audio filename (MP3)
- **Response**: Audio file with proper MIME type

### GET /client-info
- **Purpose**: View client information structure and endpoint information
- **Response**: JSON with client info structure and usage notes

### POST /extract-client-info
- **Purpose**: Manually trigger client information extraction from conversation text
- **Input**: Form data with `conversation_text` field
- **Response**: JSON with extracted client information

## How It Works

1. **Incoming Call**: When someone calls your Twilio number, it hits `/incoming-call`
2. **Audio Welcome**: Plays welcome message using `response.play()`
3. **Speech Collection**: Twilio gathers speech input from the caller
4. **Processing**: The speech is sent to `/process-speech` for AI processing
5. **Audio Generation**: AI response is converted to audio using OpenAI TTS
6. **Audio Playback**: Response is played using `response.play()` with generated audio file
7. **Conversation**: The process continues for multi-turn conversations

## Customization

### Modify the AI Response Logic

Edit the `process_speech` function in `main.py` to integrate with your actual workflow:

```python
@app.post("/process-speech")
async def process_speech(request: Request):
    # Get speech input
    form_data = await request.form()
    speech_result = form_data.get('SpeechResult', '')
    
    # Run your actual workflow here
    # result = await your_workflow.run(speech_result)
    
    # Generate response based on workflow result
    response = VoiceResponse()
    response.say("Your AI response here")
    return Response(content=str(response), media_type="application/xml")
```

### Add More Endpoints

You can add additional endpoints for:
- Call recording
- SMS handling
- Call analytics
- Custom workflows

## Testing

### Local Testing

1. Start the Twilio server: `./run_twilio_server.sh`
2. Use ngrok to expose your local server: `ngrok http 8000`
3. Update your Twilio webhook URL with the ngrok URL
4. Make a test call to your Twilio number

### Health Check

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in the uvicorn.run() call
2. **Twilio webhook errors**: Check the server logs for detailed error messages
3. **Speech not recognized**: Ensure your Twilio account supports speech input

### Logs

The server provides detailed logging for:
- Incoming webhook requests
- Speech processing
- Error handling
- Workflow execution

## Security Considerations

- Use HTTPS in production
- Validate incoming webhook requests
- Implement rate limiting
- Secure your OpenAI API key
- Monitor usage and costs
