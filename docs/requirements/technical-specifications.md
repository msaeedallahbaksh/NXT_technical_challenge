# Technical Specifications

## 🎯 Core Requirements

### Backend Specifications (FastAPI)

#### 1. Server-Sent Events (SSE) Implementation
**Endpoint**: `GET /api/stream/{session_id}`

**Event Types**:
```python
class SSEEventType(str, Enum):
    TEXT_CHUNK = "text_chunk"       # Streaming text response
    FUNCTION_CALL = "function_call" # AI function execution
    COMPLETION = "completion"       # Turn completion signal
    ERROR = "error"                # Error handling
    CONTEXT_UPDATE = "context"     # Context state changes
```

**Event Format**:
```python
@dataclass
class SSEEvent:
    event: SSEEventType
    data: Dict[str, Any]
    id: str
    timestamp: datetime
```

**Implementation Requirements**:
- Use `fastapi.responses.StreamingResponse` for SSE
- Implement connection cleanup on client disconnect
- Handle concurrent connections per session
- Add connection retry logic with exponential backoff
- Stream chunks with 50-100ms intervals for realistic feel

#### 2. Function Calling System
**Required Functions**:

```python
async def search_products(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> List[Product]:
    """Context-aware product search with result tracking"""
    
async def show_product_details(
    product_id: str,
    include_recommendations: bool = True
) -> ProductDetails:
    """Get detailed product info with validation"""
    
async def add_to_cart(
    product_id: str,
    quantity: int = 1,
    session_id: str
) -> CartUpdate:
    """Add product to cart with inventory validation"""
    
async def get_recommendations(
    based_on: str,  # product_id or category
    max_results: int = 5
) -> List[Product]:
    """Get related product recommendations"""
```

**Context Validation Requirements**:
- Track all search results in session context
- Validate product IDs against recent search results
- Implement suggestion system for invalid IDs
- Log validation failures for debugging
- Return structured error responses with suggestions

#### 3. Database Schema (SQLModel)
**Required Models**:

```python
class Product(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str
    price: float
    category: str = Field(index=True)
    image_url: str
    in_stock: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SearchContext(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    search_query: str
    results: List[str] = Field(sa_column=Column(JSON))  # Product IDs
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    product_id: str = Field(foreign_key="product.id")
    quantity: int = Field(default=1, ge=1)
    added_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 4. AI Integration Layer
**Interface Definition**:
```python
class AIAgent(Protocol):
    async def stream_response(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream AI response with function calling"""
        
    async def execute_function(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute function call with validation"""
```

**Implementation Options**:
- **Option A**: OpenAI/Anthropic API with function calling
- **Option B**: Simulated responses with realistic delays
- **Option C**: Local LLM integration (Ollama/llamacpp)

### Frontend Specifications (React + TypeScript)

#### 1. SSE Connection Hook
**Required Interface**:
```typescript
interface SSEConnectionHook {
  messages: Message[];
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (message: string) => void;
  clearMessages: () => void;
  reconnect: () => void;
  error: string | null;
}

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'function_call' | 'error';
  content: string;
  timestamp: Date;
  function_call?: {
    name: string;
    parameters: Record<string, any>;
    result?: any;
  };
}
```

**Implementation Requirements**:
- Auto-reconnection with exponential backoff
- Message queueing during disconnection
- Proper cleanup on component unmount
- TypeScript strict mode compliance
- Error boundary integration

#### 2. Dynamic Component Rendering System
**Required Components**:
```typescript
// Function call mapping
const FunctionComponents: Record<string, React.ComponentType<any>> = {
  search_products: SearchResults,
  show_product_details: ProductCard,
  add_to_cart: CartNotification,
  get_recommendations: RecommendationGrid
};

// Component interfaces
interface SearchResultsProps {
  products: Product[];
  query: string;
  onProductSelect: (id: string) => void;
}

interface ProductCardProps {
  product: ProductDetails;
  onAddToCart: (id: string, quantity: number) => void;
  recommendations?: Product[];
}
```

**Rendering Requirements**:
- Dynamic component resolution based on function names
- Props transformation from function call results
- Error boundaries for component failures
- Smooth animations for component appearance
- Mobile-responsive layouts

#### 3. Chat Interface Requirements
**Core Features**:
- Real-time text streaming with typing indicators
- Message history persistence
- Auto-scroll to latest messages
- Input validation and character limits
- Loading states and error handling
- Copy message functionality

**UI/UX Requirements**:
- Clean, modern design
- Mobile-first responsive layout
- Accessibility compliance (WCAG 2.1 AA)
- Keyboard navigation support
- Dark/light theme support (bonus)

#### 4. State Management
**Required State**:
```typescript
interface AppState {
  session: {
    id: string;
    connected: boolean;
    context: Record<string, any>;
  };
  chat: {
    messages: Message[];
    isTyping: boolean;
    error: string | null;
  };
  products: {
    searchResults: Product[];
    cart: CartItem[];
    recommendations: Product[];
  };
}
```

**Management Options**:
- React Context + useReducer (recommended)
- Redux Toolkit (acceptable)
- Zustand (acceptable)
- Local state only (minimum viable)

### Infrastructure Specifications

#### 1. Docker Configuration
**Multi-stage Build Requirements**:

**Backend Dockerfile**:
```dockerfile
FROM python:3.10-slim AS base
# Environment setup

FROM base AS dependencies  
# Install build dependencies and packages

FROM base AS runtime
# Copy only runtime dependencies
# Create non-root user
# Health checks
```

**Frontend Dockerfile**:
```dockerfile
FROM node:18-alpine AS build
# Build React app

FROM nginx:alpine AS production
# Serve static files
# Custom nginx config
# Health checks
```

#### 2. Docker Compose Setup
**Required Services**:
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/assistant
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
      
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=assistant
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d assistant"]
```

#### 3. Environment Configuration
**Required Variables**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/assistant

# AI Integration
OPENAI_API_KEY=your-key-here  # If using OpenAI
ANTHROPIC_API_KEY=your-key-here  # If using Anthropic
AI_MODEL=gpt-3.5-turbo  # or claude-3-haiku

# Application
SECRET_KEY=your-secret-key
ENVIRONMENT=development
DEBUG=true

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 🧪 Testing Requirements

### Backend Testing
**Required Test Coverage**:
- SSE connection management
- Function call validation  
- Context tracking accuracy
- Database operations
- Error handling scenarios

**Testing Framework**: pytest + pytest-asyncio
**Minimum Coverage**: 80% on core logic

### Frontend Testing
**Required Test Coverage**:
- SSE hook functionality
- Component rendering from function calls
- Error boundary behavior
- User interaction flows

**Testing Framework**: Jest + React Testing Library
**Minimum Coverage**: 70% on components and hooks

### Integration Testing
**Required Scenarios**:
- End-to-end chat flow
- Function call execution
- Context validation
- Error recovery
- Connection resilience

## 🔧 Development Tools

### Code Quality
**Backend**:
- Black (formatting)
- isort (import sorting)  
- flake8 (linting)
- mypy (type checking)

**Frontend**:
- Prettier (formatting)
- ESLint (linting)
- TypeScript strict mode
- Husky (git hooks)

### Documentation
- API docs via FastAPI auto-generation
- Component docs via Storybook (bonus)
- Architecture Decision Records (ADRs)
- README with clear setup instructions

### Monitoring (Bonus)
- Structured logging
- Health check endpoints
- Performance metrics
- Error tracking

## 🎯 Success Criteria

### Minimum Viable Product
- ✅ Working SSE connection with text streaming
- ✅ At least 2 function calls (search + details)
- ✅ Basic React chat interface
- ✅ Docker setup that works
- ✅ Basic error handling

### Production Ready
- ✅ All 4 required function calls implemented
- ✅ Context validation system working
- ✅ Robust error handling and recovery
- ✅ Clean, responsive UI
- ✅ Comprehensive testing
- ✅ Proper documentation

### Exceptional
- 🚀 Advanced features (audio simulation, caching)
- 🚀 Performance optimizations
- 🚀 Production monitoring
- 🚀 Accessibility compliance
- 🚀 Security best practices
- 🚀 Scalability considerations