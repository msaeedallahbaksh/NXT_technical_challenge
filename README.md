# NXT Humans Technical Challenge: AI-Powered Real-Time Assistant

##  Project Overview

A production-ready AI-powered real-time assistant built with FastAPI, React, and PostgreSQL. Features Server-Sent Events (SSE) for streaming responses, AI function calling with context validation, and comprehensive rate limiting.

##  Key Features

### Implemented Functionality
- **Real-time Streaming**: SSE-based bidirectional communication with text streaming
- **AI Function Calling**: 4 custom functions with dynamic React component rendering
  - search_products: Context-aware product search
  - show_product_details: Detailed product information with recommendations
  - dd_to_cart: Shopping cart management with inventory validation
  - get_recommendations: AI-powered product suggestions
- **Context Validation**: Prevents AI hallucination by validating product IDs against search results
- **Rate Limiting**: Comprehensive IP-based rate limiting on all endpoints
- **Production Ready**: Docker containerization, health checks, error handling

### Technical Highlights
- **Backend**: FastAPI with async/await, SQLModel ORM, AI integration (OpenAI/Anthropic)
- **Frontend**: React 18 + TypeScript, custom SSE hook, dynamic components
- **Infrastructure**: Docker Compose, PostgreSQL, Redis-ready rate limiting
- **Testing**: 53 passing frontend tests, rate limiting test suite
- **Security**: Rate limiting, CORS, input validation, context validation

##  Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Node.js 18+ and Python 3.10+ for local development

### Setup Instructions

1. **Clone the repository**:
   \\\ash
   git clone <your-repo-url>
   cd NXT_technical_challenge
   \\\

2. **Configure environment**:
   \\\ash
   cp .env.example .env
   # Edit .env with your API keys (or use AI_PROVIDER=simulate for testing)
   \\\

3. **Start the application**:
   \\\ash
   docker-compose up -d --build
   \\\

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

5. **Test the features**:
   - Open http://localhost:3000
   - Try: "Show me wireless headphones"
   - Try: "Tell me more about [product name]"
   - Try: "Add it to my cart"

##  Project Structure

\\\
NXT_technical_challenge/
 starter-code/
    backend/                  # FastAPI application
       main.py              # SSE endpoints, rate limiting
       ai_agent.py          # AI integration (OpenAI/Anthropic)
       context_manager.py   # Context validation system
       product_service.py   # Product business logic
       rate_limit_config.py # Rate limiting configuration
       test_rate_limiting.py # Rate limit test suite
    frontend/                 # React + TypeScript application
       src/
           hooks/           # useSSEConnection custom hook
           components/      # Dynamic UI components
           __tests__/       # 53 passing tests
    docker/                   # Docker configurations
 docker-compose.yml
 .env.example
\\\

##  Architecture

### Backend (FastAPI)
- **SSE Streaming**: Async event stream for real-time AI responses
- **AI Integration**: OpenAI GPT-4 or Anthropic Claude Sonnet
- **Function Calling**: AI agent can invoke backend functions dynamically
- **Context Validation**: Tracks search results to prevent hallucinations
- **Rate Limiting**: slowapi with configurable per-endpoint limits

### Frontend (React + TypeScript)
- **SSE Hook**: Custom hook with auto-reconnection and error handling
- **Dynamic Rendering**: Function calls trigger React component rendering
- **State Management**: React Context API for global state
- **Error Boundaries**: Graceful error handling at component level

### Database (PostgreSQL)
- **Products**: Product catalog with full-text search
- **Session Context**: User sessions with search history
- **Cart**: Shopping cart with inventory tracking
- **Conversation History**: Persistent message storage

##  Environment Variables

Key variables in .env.example:

\\\ash
# AI Provider (choose one)
AI_PROVIDER=anthropic              # or "openai" or "simulate"
ANTHROPIC_API_KEY=your-key-here
AI_MODEL=claude-sonnet-4-5-20250929

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/assistant

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URI=memory://   # or redis://redis:6379 for production
\\\

##  Testing

### Frontend Tests
\\\ash
cd starter-code/frontend
npm test
# 53 tests passing
\\\

### Rate Limiting Tests
\\\ash
cd starter-code/backend
python test_rate_limiting.py
# Tests all 11 endpoints with rate limiting
\\\

### API Testing
Import starter-code/backend/postman_collection.json into Postman for comprehensive API testing.

##  Security Features

### Rate Limiting
- **IP-based**: Tracks requests per IP address
- **Endpoint-specific**: Different limits for different operations
  - Health check: 100/min
  - Session creation: 10/min
  - Chat messages: 20/min (protects AI API costs)
  - Product operations: 30-60/min
- **Configurable**: Can disable via environment variable
- **Scalable**: Redis-ready for distributed systems

### Other Security
- CORS configuration
- Input validation on all endpoints
- Context validation (prevents AI from inventing product IDs)
- Error messages don't expose stack traces

##  Performance Considerations

- **Async/Await**: All I/O operations are non-blocking
- **Streaming**: Responses stream to frontend as they're generated
- **Connection Pooling**: Database connection pool for efficiency
- **Efficient Queries**: Indexed database fields for fast lookups
- **Rate Limiting**: Protects against abuse and resource exhaustion

##  Production Readiness

### What's Included
 Docker containerization with health checks
 Rate limiting on all endpoints
 Comprehensive error handling
 Context validation system
 Database migrations (init.sql)
 Environment-based configuration
 Structured logging
 API documentation (FastAPI auto-docs)

### Production Deployment Considerations
- Switch to Redis for rate limiting: RATE_LIMIT_STORAGE_URI=redis://redis:6379
- Generate strong SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
- Set DEBUG=false and proper LOG_LEVEL
- Use managed PostgreSQL service
- Add monitoring (Sentry, DataDog, etc.)
- Configure proper CORS origins
- Set up CI/CD pipeline

##  Key Technical Decisions

### Why SSE over WebSockets?
- **Simpler**: HTTP-based, works with standard proxies
- **One-directional**: Perfect for AI streaming (server  client)
- **Auto-reconnection**: Built into EventSource API
- **Lower overhead**: No handshake protocol needed

### Why Anthropic Claude?
- **Better function calling**: More reliable tool use
- **Longer context**: 200K token window
- **Agentic behavior**: Better at following instructions (especially agentic)

### Why slowapi for Rate Limiting?
- **Flask-Limiter inspired**: Familiar API
- **Redis support**: Scales horizontally
- **Flexible**: Per-endpoint configuration
- **Headers**: Includes rate limit info in responses

### Context Validation System
Prevents AI hallucination by:
1. Tracking all search results in session context
2. Validating product IDs against recent searches
3. Suggesting corrections when invalid IDs used
4. Maintaining search history for context

# Agent function calling - Update
Old: No longer goes backend streams function event -> frontend recognizing and calling the api -> api call completed and response returned to frontend
New: When function event is recognized, we just run it in the backend. We can simultaneously stream 'notification' to the frontend that the function is being ran so the user isnt left waiting.

##  Development Workflow

### Local Development
\\\ash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Shut down
docker-compose down
\\\

### Making Changes
- Backend: Changes auto-reload (DEBUG=true)
- Frontend: Changes auto-reload (React dev server)
- Database: Use init.sql for schema changes

##  Troubleshooting

### Port Conflicts
If ports 3000, 8000, or 5432 are in use:
\\\ash
docker-compose down
# Edit docker-compose.yml to change ports
docker-compose up -d
\\\

### Database Connection Issues
\\\ash
# Reset database
docker-compose down -v  # Removes volumes
docker-compose up -d
\\\

### Rate Limiting Issues
Disable for development:
\\\ash
# In .env
RATE_LIMIT_ENABLED=false
\\\

### Frontend Can't Connect
Check CORS settings in backend .env:
\\\ash
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
\\\

##  Future Improvements

To add onto this I would add:
- [ ] Backend unit tests (currently have integration tests)
- [ ] Message persistence in database for history
- [ ] User authentication and sessions
- [ ] Advanced caching layer (Redis)
- [ ] WebSocket support for bidirectional streaming
- [ ] Audio/binary data support over SSE
- [ ] Advanced AI reasoning and planning
- [ ] Performance monitoring and metrics
- [ ] Load testing suite
- [ ] Multi-step capability for AI Agents. This would allow agents to carry out more complex tasks by allowing multiple tool calls/tasks per query. Tasks like "Add the headphones to my cart and find a keyboard for me" can then be carried out by the agent in one go.

##  AI Tools Used

I used Claude 4.5 Sonnet in Cursor to code:
- I like to research best practices, discuss implementation details, concerns I have, make sure I understand the approach I will be taking in detail by discussing them with the AI.
- Then I have it generate code after confirming an implementation strategy.
- Then I read through the code to see what it implemented, what it might have missed from my implementation instructions, or see if I realize any changes that need to be made.
- Then I test the code
- For simpler bug cases I catch while reading the code, I'll either fix it or have AI do it (depends on time). For more complex issues, Ill have AI follow through the code logic with a mock scenario to find where it might be coming from.
- AI likes to write documentation on changes it made. Most of the time unnecessary and floods code base, so I generally delete them.



**Built for the NXT Humans Technical Challenge**
Demonstrates production-ready full-stack development with modern AI integration patterns.
