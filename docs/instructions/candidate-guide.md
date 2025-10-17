# Candidate Guide: AI Product Discovery Assistant Challenge

## 🎯 Welcome to the NXT Humans Technical Challenge!

Congratulations on reaching the technical assessment phase! This challenge is based on real-world problems we solve at NXT Humans, building sophisticated AI-powered applications with real-time communication and advanced user experiences.

---

## 📋 Challenge Overview

**Your Mission**: Build a real-time AI-powered product discovery assistant that helps users find products through natural conversation.

**Time Limit**: We recommend **12-16 hours** of focused work, but you have **1 week** to complete and submit your solution.

**What Makes This Different**: This isn't just another CRUD app. You'll be implementing advanced patterns we use in production:
- Real-time bidirectional communication via Server-Sent Events
- AI function calling with context validation
- Dynamic React component rendering based on AI responses
- Sophisticated state management across real-time connections

---

## 🚀 Getting Started

### 1. Repository Setup
```bash
# Fork or clone this repository
git clone [your-repository]
cd tech-challenge

# Copy environment template
cp .env.example .env

# Start the development environment
docker-compose up -d
```

### 2. Verify Your Setup
- **Frontend**: http://localhost:3000 (React app)
- **Backend**: http://localhost:8000/docs (FastAPI docs)
- **Database**: PostgreSQL running on port 5432

### 3. Expected Behavior
When working correctly:
- Chat interface loads with connection status indicator
- You can type messages and receive AI responses
- Function calls render as UI components (product cards, search results)
- SSE connection shows as "connected"

---

## 📝 Implementation Requirements

### Core Requirements (Must Have)
1. **SSE Connection** - Real-time streaming text responses
2. **Function Calling** - At least 2 of 4 required functions working
3. **Dynamic Components** - Function calls render React components
4. **Basic Error Handling** - Application doesn't crash on errors
5. **Docker Setup** - Runs with `docker-compose up`

### Production Requirements (Expected)
1. **All 4 Functions** - search, details, cart, recommendations
2. **Context Validation** - Prevent AI hallucination with product IDs
3. **Connection Management** - Auto-reconnection, proper cleanup
4. **Comprehensive Testing** - Unit and integration tests
5. **Clean Architecture** - Maintainable, scalable code structure

### Advanced Requirements (Impressive)
1. **Performance Optimization** - Efficient streaming, caching
2. **Security Implementation** - Input validation, CORS, rate limiting
3. **Accessibility** - WCAG compliance, keyboard navigation
4. **Innovation** - Creative features beyond requirements
5. **Production Readiness** - Monitoring, logging, deployment

---

## 🛠 Technical Architecture

### Backend (FastAPI + Python)
Your backend should implement:
```python
# SSE endpoint for real-time communication
@app.get("/api/stream/{session_id}")
async def stream_chat(session_id: str):
    # Real-time event streaming
    pass

# Function endpoints
@app.post("/api/functions/search_products")
@app.post("/api/functions/show_product_details")  
@app.post("/api/functions/add_to_cart")
@app.post("/api/functions/get_recommendations")
```

**Key Patterns**:
- Async/await throughout
- SQLModel for database operations
- Context tracking to prevent AI hallucination
- Proper error handling and validation

### Frontend (React + TypeScript)
Your frontend should implement:
```typescript
// SSE connection management
const useSSEConnection = (options: SSEConnectionOptions) => {
  // EventSource management
  // Auto-reconnection logic
  // Message parsing and state management
  return { messages, sendMessage, connectionStatus, ... };
};

// Dynamic component rendering
const FunctionCallRenderer = ({ functionCall }) => {
  // Map function names to React components
  // Handle different function call types
  return <DynamicComponent />;
};
```

**Key Patterns**:
- Custom hooks for SSE management
- Context API for global state
- TypeScript strict mode
- Error boundaries for graceful failures

---

## 🧪 Development Strategy

### Phase 1: Foundation (Hours 1-4)
1. **Set up SSE connection** - Get basic text streaming working
2. **Implement one function** - Start with `search_products`
3. **Create chat interface** - Basic message display
4. **Test Docker setup** - Ensure everything runs

### Phase 2: Core Features (Hours 5-8)
1. **Add remaining functions** - Details, cart, recommendations
2. **Implement context validation** - Prevent AI errors
3. **Dynamic component rendering** - Function calls → UI components
4. **Error handling** - Graceful failures and recovery

### Phase 3: Polish & Testing (Hours 9-12)
1. **Write tests** - Unit and integration coverage
2. **Performance optimization** - Streaming efficiency
3. **UI/UX improvements** - Polish the interface
4. **Documentation** - README and code comments

### Phase 4: Advanced Features (Hours 13-16)
1. **Security hardening** - Validation, rate limiting
2. **Additional features** - Caching, monitoring
3. **Accessibility** - Keyboard navigation, screen readers
4. **Production readiness** - Health checks, logging

---

## 🎯 Success Tips

### Technical Excellence
- **Start Simple**: Get basic SSE working before adding complexity
- **Test Early**: Don't wait until the end to test functionality
- **Use TypeScript**: Proper typing will save you debugging time
- **Follow Patterns**: Look at our starter code for guidance
- **Handle Errors**: Plan for failures from the beginning

### Time Management
- **Time-box Features**: Don't spend 4 hours perfecting one function
- **Focus on Core**: Get all basic requirements working first
- **Document As You Go**: Don't leave documentation for the end
- **Test Incrementally**: Verify each piece as you build it

### AI Integration Options
You have several choices for AI integration:
1. **Use OpenAI/Anthropic APIs** - Real AI with function calling
2. **Simulate AI responses** - Use our MockAIAgent class
3. **Hybrid approach** - Mock for development, real for demo

### Common Pitfalls to Avoid
- **SSE connection management** - Handle reconnections properly
- **State synchronization** - Keep frontend/backend in sync
- **Context validation** - Don't let AI hallucinate product IDs
- **Error boundaries** - Prevent crashes from breaking the app
- **Docker issues** - Test your containers regularly

---

## 📚 Resources & References

### Starter Code Overview
```
starter-code/
├── backend/                    # FastAPI application
│   ├── main.py                # SSE endpoints and routing
│   ├── models.py              # Database models and DTOs
│   ├── ai_agent.py            # AI integration (mock & real)
│   ├── product_service.py     # Product operations
│   └── context_manager.py     # Context validation
├── frontend/                   # React application  
│   └── src/
│       ├── hooks/
│       │   └── useSSEConnection.ts  # SSE management
│       ├── components/
│       │   └── ChatInterface.tsx    # Main chat UI
│       └── context/
│           └── AppStateContext.tsx  # Global state
└── docker/                     # Container configurations
    ├── Dockerfile.backend
    └── Dockerfile.frontend
```

### Key Documentation
- **Technical Specifications**: `/docs/requirements/technical-specifications.md`
- **API Specification**: `/docs/requirements/api-specification.md`
- **Architecture Guide**: Main README.md

### External Resources
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React SSE Tutorial**: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- **SQLModel Guide**: https://sqlmodel.tiangolo.com/
- **TypeScript Handbook**: https://www.typescriptlang.org/docs/

---

## 🚫 What We're NOT Looking For

### Anti-Patterns
- **Over-engineering** - Don't build enterprise-scale for a demo
- **Perfect UI** - Focus on functionality over pixel-perfect design
- **Every possible feature** - Core requirements done well > many features done poorly
- **Complex state management** - Redux/Zustand only if truly needed
- **Premature optimization** - Get it working first

### Time Wasters
- **Extensive styling** - Clean and functional is enough
- **Complex animations** - Simple transitions are fine
- **Perfect error messages** - Clear and helpful is enough
- **Comprehensive logging** - Basic logging is sufficient

---

## 📤 Submission Guidelines

### What to Submit
1. **Git Repository** - Your complete codebase with commit history
2. **README.md** - Comprehensive setup and usage instructions
3. **Working Demo** - Application must start with `docker-compose up`
4. **Documentation** - Architecture decisions and trade-offs

### Submission Format
```markdown
## Submission Checklist
- [ ] Repository is public or shared with NXT Humans team
- [ ] README.md includes setup instructions
- [ ] Application starts without errors
- [ ] Core functionality demonstrates
- [ ] Tests run successfully (if present)
- [ ] Documentation explains architecture decisions
```

### Repository Structure
```
your-submission/
├── README.md                   # Your implementation guide
├── docker-compose.yml          # Working container setup
├── .env.example               # Required environment variables
├── backend/                   # Your FastAPI implementation
├── frontend/                  # Your React implementation
├── tests/                     # Your test suite (if present)
└── docs/                      # Additional documentation
    ├── ARCHITECTURE.md        # Your design decisions
    ├── API.md                 # Your API documentation
    └── TRADE_OFFS.md          # Compromises and future improvements
```

### Code Quality Requirements
- **Clean Code**: Readable, well-organized, consistent formatting
- **Comments**: Complex logic explained, not obvious statements
- **Naming**: Clear, descriptive variable and function names
- **Structure**: Logical file organization and module separation
- **Error Handling**: Graceful failures, user-friendly messages

---

## 🎤 Demo Preparation

### What We'll Test
1. **Application Startup** - `docker-compose up` works without issues
2. **Basic Chat Flow** - Can send messages and receive responses
3. **Function Calling** - Search, details, cart operations work
4. **Error Handling** - Graceful failures and recovery
5. **Code Walkthrough** - Explain key technical decisions

### Be Prepared to Discuss
- **Architecture Decisions** - Why you chose certain patterns
- **Trade-offs Made** - What you sacrificed for time/simplicity
- **Scaling Considerations** - How you'd handle production load
- **Alternative Approaches** - Other ways you considered solving problems
- **Future Improvements** - What you'd add with more time

### Common Demo Questions
- "Walk me through your SSE implementation"
- "How do you prevent AI hallucination?"
- "What happens when the connection drops?"
- "How would you handle 1000 concurrent users?"
- "What security measures did you implement?"

---

## ❓ Getting Help

### During Development
- **README Issues**: Check setup instructions carefully
- **Docker Problems**: Ensure ports aren't conflicted
- **SSE Debugging**: Use browser dev tools Network tab
- **API Testing**: Use FastAPI's `/docs` endpoint

### What You Can Ask
- **Clarifying Questions**: About requirements or expectations
- **Technical Issues**: If starter code isn't working
- **Scope Questions**: Whether certain features are expected

### What We Won't Help With
- **Implementation Guidance**: How to code specific features
- **Debugging Code**: Finding bugs in your implementation
- **Architecture Decisions**: Which patterns to use
- **Time Management**: How to prioritize your work

---

## 🏆 Final Words

This challenge represents the kind of sophisticated, real-world problems you'll solve at NXT Humans. We're looking for developers who can:

- **Think systematically** about complex technical problems
- **Build production-quality** software with proper error handling
- **Learn quickly** and adapt to new technologies
- **Communicate clearly** about technical decisions
- **Balance perfection** with practical delivery

Remember: **We'd rather see core functionality working well than advanced features half-implemented.**

**Good luck, and we're excited to see what you build!** 🚀

---

**Questions?** Reach out to the NXT Humans team through the provided contact method. We're here to help with clarifications and technical issues.