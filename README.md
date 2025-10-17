# NXT Humans Technical Challenge: AI-Powered Real-Time Assistant

## 🎯 Challenge Overview

Welcome to the NXT Humans full-stack technical challenge! This challenge is based on real-world problems encountered while building AI-powered applications at NXT Humans. You'll be building a simplified version of an **AI-powered real-time assistant** that demonstrates advanced patterns we use in production.

**Core Challenge**: Build a real-time streaming AI assistant with function calling capabilities, context validation, and multi-modal communication patterns.

### Why This Challenge?

This challenge is derived from our experience building the MAC Beauty Advisor AI application - a sophisticated beauty consultation platform that integrates Google's Agent Development Kit (ADK) with real-time streaming, voice processing, and complex product recommendation systems. The patterns you'll implement are battle-tested in production and represent the type of challenges you'll face working with AI-powered applications at scale.

## 🛠 What You'll Build

You'll create a **Product Discovery Assistant** - a real-time AI agent that helps users find and learn about products through natural conversation, with the following capabilities:

### Core Features
1. **Real-time bidirectional communication** via Server-Sent Events (SSE)
2. **AI function calling** with dynamic component rendering
3. **Context-aware product search** with validation to prevent AI hallucination
4. **Streaming text responses** with partial updates
5. **Multi-modal data handling** (text, JSON function calls, binary data simulation)
6. **Sophisticated state management** across frontend and backend

### Key Technical Challenges
- **SSE Event Processing Pipeline**: Handle multiple event types (text streaming, function calls, completion signals)
- **Context Validation System**: Track and validate AI agent responses to prevent hallucinations
- **Dynamic Component System**: Render React components based on AI function calls
- **State Synchronization**: Manage complex state across real-time connections
- **Performance Optimization**: Handle streaming data efficiently

## 📋 Technical Requirements

### Backend Requirements (FastAPI + Python)
- **FastAPI** application with async/await patterns
- **Server-Sent Events (SSE)** endpoint for real-time communication
- **AI Agent Integration** (simulated or real LLM integration)
- **Function Calling System** with at least 4 custom functions:
  - `search_products(query, category)` - Product search with context tracking
  - `show_product_details(product_id)` - Detailed product information
  - `add_to_cart(product_id, quantity)` - Shopping cart management
  - `get_recommendations(based_on)` - Related product suggestions
- **Context Management** - Track search results and validate function call parameters
- **Database Integration** - SQLModel/SQLAlchemy with async operations
- **Error Handling** - Robust error recovery and suggestion system

### Frontend Requirements (React + TypeScript)
- **React 18+** with TypeScript and modern hooks
- **SSE Connection Hook** - Custom hook for managing Server-Sent Events
- **Real-time Chat Interface** - Stream text with partial updates
- **Dynamic Component Rendering** - Render components based on function calls
- **State Management** - Context or modern state management patterns
- **Error Boundaries** - Graceful error handling and recovery
- **Responsive Design** - Clean, professional UI that works on mobile/desktop

### Infrastructure Requirements
- **Docker** containerization with multi-stage builds
- **Docker Compose** for local development
- **Environment Configuration** - Proper secrets management
- **Health Checks** - Container health monitoring
- **Development Tools** - Hot reloading, debugging capabilities

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TS)               │
│  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │  Chat Interface │  │    Dynamic Components        │ │
│  │  - SSE Hook     │  │  - ProductCard               │ │
│  │  - Text Stream  │  │  - SearchResults             │ │
│  │  - User Input   │  │  - CartView                  │ │
│  └─────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                             │ SSE Connection
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              SSE Stream Handler                     │ │
│  │  ┌──────────────┐  ┌─────────────┐ ┌─────────────┐ │ │
│  │  │    Event     │  │  Function   │ │  Context    │ │ │
│  │  │  Processing  │  │   Calling   │ │ Validation  │ │ │
│  │  └──────────────┘  └─────────────┘ └─────────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                AI Agent Layer                       │ │
│  │  ┌──────────────┐  ┌─────────────────────────────┐ │ │
│  │  │   Product    │  │      Function Tools         │ │ │
│  │  │   Search     │  │  - search_products          │ │ │
│  │  │   Engine     │  │  - show_product_details     │ │ │
│  │  └──────────────┘  │  - add_to_cart             │ │ │
│  └─────────────────────│  - get_recommendations     │─┘ │
│                        └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  DATABASE (PostgreSQL)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Products  │  │  Search     │  │  User Sessions  │ │
│  │   Catalog   │  │  Context    │  │  & Cart Data    │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Challenge Levels

### **Level 1: Foundation (Required)**
- ✅ Basic SSE connection with text streaming
- ✅ Simple product search function
- ✅ React component rendering from function calls
- ✅ Basic error handling

### **Level 2: Production Ready (Expected)**
- ✅ Context validation system
- ✅ Multiple function tools with parameter validation
- ✅ Sophisticated state management
- ✅ Proper Docker containerization
- ✅ Comprehensive error handling and recovery

### **Level 3: Advanced (Impressive)**
- 🚀 Audio/binary data simulation over SSE
- 🚀 Advanced caching and performance optimization
- 🚀 Comprehensive test suite with real-time testing
- 🚀 Production monitoring and logging
- 🚀 AI agent reasoning and planning capabilities

## 📁 Repository Structure

```
tech-challenge/
├── README.md                          # This file
├── docs/                              # Documentation
│   ├── requirements/                  # Detailed specifications
│   ├── evaluation/                    # Grading criteria  
│   └── instructions/                  # Setup and submission guides
├── starter-code/                      # Provided starter templates
│   ├── backend/                       # FastAPI app structure
│   ├── frontend/                      # React app structure  
│   └── docker/                        # Container configurations
├── examples/                          # Reference implementations
└── evaluation/                        # Scoring rubrics
```

## 🚀 Getting Started

### Prerequisites
- **Docker & Docker Compose** (latest versions)
- **Node.js 18+** and **Python 3.10+** (for local development)
- **Git** for version control
- **Text Editor/IDE** of your choice

### Quick Start
1. **Clone and Setup**:
   ```bash
   git clone <your-fork>
   cd tech-challenge
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start Development Environment**:
   ```bash
   docker-compose up -d
   ```

3. **Access Applications**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Test your SSE connection: http://localhost:8000/stream

4. **Begin Implementation**:
   - Start with `backend/main.py` for SSE setup
   - Implement `frontend/src/hooks/useSSEConnection.ts`
   - Build your AI function tools

## ⏱ Time Expectations

- **Minimum Viable Solution**: 6-8 hours
- **Production Quality Solution**: 12-16 hours  
- **Advanced Solution with Extras**: 20+ hours

**We recommend time-boxing**: Focus on core functionality first, then add advanced features if time permits.

## 📝 Submission Requirements

### Code Submission
1. **Git Repository** with clear commit history showing your development process
2. **README.md** documenting your approach, trade-offs, and instructions
3. **Working Docker setup** that starts with `docker-compose up`
4. **Test coverage** for critical functionality
5. **API documentation** (automatically generated via FastAPI)

### Documentation Requirements
1. **Architecture Decision Record** - Explain your key technical choices
2. **Performance Considerations** - How you handled real-time data
3. **Error Handling Strategy** - Your approach to resilience
4. **Scaling Considerations** - How your solution would handle growth
5. **Future Improvements** - What you would add with more time

### Demonstration
Be prepared to:
- **Live demo** your working application
- **Walk through your code** and explain key decisions
- **Discuss alternative approaches** and trade-offs
- **Handle questions** about scaling and production considerations

## 🎯 What We're Looking For

### Technical Excellence
- **Clean, readable code** with proper structure and patterns
- **Real-time programming competency** - efficient SSE handling
- **State management expertise** - complex state across components
- **Error resilience** - graceful handling of failures
- **Performance awareness** - efficient data processing

### Full-Stack Capabilities  
- **Backend API design** - well-structured FastAPI applications
- **Frontend development** - modern React patterns with TypeScript
- **Database design** - efficient schema and query patterns
- **DevOps practices** - containerization and deployment readiness

### Problem-Solving Approach
- **Analysis and planning** - clear technical decisions
- **Code organization** - modular, maintainable architecture
- **Testing strategy** - appropriate test coverage
- **Documentation** - clear communication of design decisions

## 🤖 AI Integration Notes

### Using Coding Agents (Encouraged!)
We **encourage** you to use AI coding assistants (Claude, Copilot, etc.) as this reflects modern development practices. However:

1. **Show Your Work**: Include comments explaining key decisions and trade-offs
2. **Demonstrate Understanding**: Be prepared to explain any AI-generated code
3. **Add Personal Touch**: Customize and improve upon AI suggestions
4. **Document Process**: Note in your README how you leveraged AI tools

### AI Integration Options
- **Option 1**: Use OpenAI/Anthropic APIs for real AI integration
- **Option 2**: Simulate AI responses with predefined logic (acceptable)
- **Option 3**: Use local LLM (Ollama, etc.) for full control

## 💡 Pro Tips

### Development Strategy
1. **Start with SSE basics** - Get text streaming working first
2. **Build function calling** - One function at a time
3. **Add context validation** - Prevent common AI errors
4. **Polish the UI** - Make it feel responsive and professional
5. **Add advanced features** - If time permits

### Common Pitfalls
- **SSE Connection Management** - Handle reconnections gracefully
- **State Synchronization** - Keep frontend/backend state aligned  
- **Error Boundaries** - Don't let errors crash the entire app
- **Performance** - Stream processing can be CPU intensive
- **Context Validation** - AI agents can hallucinate IDs/parameters

### Bonus Points
- **Production Monitoring** - Add logging, metrics, health checks
- **Advanced Testing** - Real-time connection testing, load testing
- **Security** - Input validation, rate limiting, CORS
- **Accessibility** - Keyboard navigation, screen reader support
- **Performance** - Lazy loading, efficient updates, caching

## 📞 Support

### Getting Help
- Check the `docs/` folder for detailed specifications
- Review `examples/` for reference implementations  
- Common issues and solutions are documented in `docs/troubleshooting.md`

### Questions?
During the challenge, you may ask clarifying questions, but we won't provide implementation guidance. Part of the challenge is working through technical problems independently - just like in real development work.

---

**Good luck, and we're excited to see what you build!** 🚀

This challenge represents the kind of sophisticated, real-world problems you'd tackle at NXT Humans. Show us your technical skills, problem-solving approach, and ability to build production-quality software with modern AI integration patterns.