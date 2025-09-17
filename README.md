# Voice Agent System

A clean, modular voice agent system built with FastAPI, Redis, and modern Python practices.

## 🏗️ Architecture Overview

The system is organized into a clean, modular architecture following SOLID principles:

```
demo/
├── core/                           # Core application modules
│   ├── config/                     # Configuration management
│   │   ├── settings.py            # Application settings
│   │   └── logging_config.py      # Logging configuration
│   └── utils/                      # Utility functions
├── infrastructure/                  # Infrastructure layer
│   ├── redis/                      # Redis client and operations
│   │   └── redis_client.py        # Redis connection management
│   └── database/                   # Database connections (future)
├── services/                        # Business logic services
│   ├── communication/              # Communication services
│   │   ├── email_service.py       # Email service
│   │   └── whatsapp_service.py    # WhatsApp service
│   ├── data_processing/            # Data processing services
│   │   └── customer_processor.py  # Customer data processing
│   ├── event_handling/             # Event handling services
│   │   └── event_handlers.py      # Event handlers
│   └── redis_consumer_service.py  # Main Redis consumer
├── api/                            # API layer
│   ├── routes/                     # API routes
│   │   └── customer_routes.py     # Customer API endpoints
│   └── websockets/                 # WebSocket handlers (future)
├── app.py                          # FastAPI application
├── main.py                         # Application entry point
└── requirements.txt                # Dependencies
```

## 🚀 Key Features

- **Clean Architecture**: Separation of concerns with clear module boundaries
- **Async Support**: Full async/await support throughout the system
- **Event-Driven**: Redis pub/sub for event handling
- **Modular Services**: Easy to extend and maintain
- **Type Safety**: Comprehensive type hints
- **Configuration Management**: Centralized configuration
- **Logging**: Structured logging with configurable levels

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd voice-agent/demo
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Server Configuration
PORT=8000
HOST=0.0.0.0
DEBUG=false

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
VOICE=alloy
LANGUAGE=he-IL

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
BUSINESS_EMAIL=business@example.com

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
BUSINESS_WHATSAPP_NUMBER=+1234567890
```

## 📡 API Endpoints

### Health Check
- `GET /health` - System health status
- `GET /customers/health` - Customer service health

### Customer Management
- `GET /customers/sessions/{stream_id}` - Get customer session
- `POST /customers/events` - Create customer event
- `POST /customers/validate` - Validate customer data

### Twilio Voice Integration
- `POST /incoming-call` - Handle incoming Twilio voice calls (legacy endpoint)
- `POST /twilio/incoming-call` - Handle incoming Twilio voice calls
- `POST /twilio/call-status` - Handle call status webhooks
- `GET /twilio/audio/{filename}` - Serve audio files for calls
- `POST /twilio/voice-webhook` - Generic voice webhook handler
- `GET /audio/{filename}` - Legacy audio endpoint

## 🔄 Event Flow

1. **Customer Interaction**: Voice agent processes customer call
2. **Event Publishing**: Customer data published to Redis
3. **Event Processing**: Redis consumer processes events
4. **Notification**: Email/WhatsApp notifications sent
5. **Data Storage**: Customer data stored in Redis

## 🧪 Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

### Running in Development Mode
```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Service Architecture

### Core Services

- **RedisConsumerService**: Main service orchestrating event consumption
- **CustomerDataProcessor**: Processes and validates customer data
- **EmailService**: Handles email communications
- **WhatsAppService**: Manages WhatsApp messages via Twilio

### Event Handlers

- **CustomerDataEventHandler**: Processes valid customer data
- **InvalidCustomerDataEventHandler**: Handles validation failures
- **MeetingScheduledEventHandler**: Manages meeting scheduling
- **HighPriorityEventHandler**: Processes urgent customer contacts

## 📊 Monitoring

The system includes comprehensive logging and health checks:

- **Health Endpoints**: Monitor service status
- **Structured Logging**: Configurable log levels and formats
- **Redis Health Checks**: Monitor Redis connection status
- **Error Handling**: Global exception handling with detailed error responses

## 🚀 Deployment

### Docker (Recommended)
```bash
docker build -t voice-agent .
docker run -p 8000:8000 voice-agent
```

### Production
```bash
# Use production WSGI server
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code examples

---

**Built with ❤️ using FastAPI, Redis, and modern Python practices**
