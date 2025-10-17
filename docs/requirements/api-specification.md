# API Specification

## 🔗 Endpoints Overview

### Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com/api`

### Authentication
For this challenge, authentication is optional but encouraged. If implemented:
- Bearer token authentication
- Session-based authentication
- Simple API key (minimum)

---

## 📡 Server-Sent Events

### Stream Connection
```http
GET /api/stream/{session_id}
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Path Parameters:**
- `session_id` (string, required): Unique session identifier

**Response Format:**
```
event: text_chunk
id: msg_123
data: {"content": "Hello! How can I help you find products today?", "partial": true}

event: function_call  
id: msg_124
data: {"function": "search_products", "parameters": {"query": "wireless headphones", "category": "electronics"}}

event: completion
id: msg_125
data: {"turn_id": "turn_123", "total_tokens": 45}
```

**Event Types:**
- `text_chunk`: Streaming text response chunks
- `function_call`: AI agent function execution
- `completion`: Indicates turn completion
- `error`: Error information
- `context`: Context state updates

### Send Message
```http
POST /api/chat/{session_id}/message
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "I'm looking for wireless headphones under $200",
  "context": {
    "previous_search": "headphones",
    "budget_range": "under_200"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "msg_126",
  "session_id": "session_abc123"
}
```

---

## 🛠 Function Call APIs

### Search Products
**Function Name:** `search_products`

```http
POST /api/functions/search_products
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "wireless headphones",
  "category": "electronics",
  "limit": 10,
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "prod_123",
        "name": "Sony WH-1000XM4 Wireless Headphones",
        "description": "Industry leading noise cancellation",
        "price": 349.99,
        "category": "electronics",
        "image_url": "https://example.com/sony-headphones.jpg",
        "in_stock": true,
        "rating": 4.8,
        "reviews_count": 1247
      }
    ],
    "total_results": 43,
    "search_context": {
      "query": "wireless headphones",
      "category": "electronics",
      "results_cached": true
    }
  },
  "context_updated": true
}
```

### Show Product Details
**Function Name:** `show_product_details`

```http
POST /api/functions/show_product_details
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_id": "prod_123",
  "include_recommendations": true,
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "id": "prod_123",
      "name": "Sony WH-1000XM4 Wireless Headphones",
      "description": "Industry leading noise cancellation with 30-hour battery life",
      "long_description": "The Sony WH-1000XM4 headphones feature...",
      "price": 349.99,
      "category": "electronics",
      "image_url": "https://example.com/sony-headphones.jpg",
      "additional_images": ["https://example.com/sony-1.jpg"],
      "in_stock": true,
      "stock_quantity": 15,
      "rating": 4.8,
      "reviews_count": 1247,
      "specifications": {
        "battery_life": "30 hours",
        "weight": "254g",
        "connectivity": "Bluetooth 5.0"
      },
      "features": [
        "Active Noise Cancellation",
        "30-hour battery",
        "Quick Charge (10min = 5hours)"
      ]
    },
    "recommendations": [
      {
        "id": "prod_124",
        "name": "Bose QuietComfort 45",
        "price": 329.99,
        "image_url": "https://example.com/bose.jpg",
        "reason": "Similar noise cancellation features"
      }
    ]
  },
  "validation": {
    "product_exists": true,
    "in_recent_search": true,
    "context_valid": true
  }
}
```

### Add to Cart
**Function Name:** `add_to_cart`

```http
POST /api/functions/add_to_cart
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_id": "prod_123",
  "quantity": 2,
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cart_item": {
      "id": "cart_456",
      "product_id": "prod_123",
      "product_name": "Sony WH-1000XM4 Wireless Headphones",
      "quantity": 2,
      "unit_price": 349.99,
      "total_price": 699.98,
      "added_at": "2024-01-20T10:30:00Z"
    },
    "cart_summary": {
      "total_items": 3,
      "total_products": 2,
      "subtotal": 899.97,
      "estimated_tax": 89.99,
      "estimated_total": 989.96
    }
  },
  "validation": {
    "product_exists": true,
    "sufficient_stock": true,
    "valid_quantity": true
  }
}
```

### Get Recommendations
**Function Name:** `get_recommendations`

```http
POST /api/functions/get_recommendations
Content-Type: application/json
```

**Request Body:**
```json
{
  "based_on": "prod_123",
  "recommendation_type": "similar",
  "max_results": 5,
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": "prod_124",
        "name": "Bose QuietComfort 45",
        "price": 329.99,
        "image_url": "https://example.com/bose.jpg",
        "similarity_score": 0.89,
        "reason": "Similar noise cancellation and wireless features"
      }
    ],
    "recommendation_context": {
      "based_on_product": "Sony WH-1000XM4",
      "algorithm": "collaborative_filtering",
      "factors": ["category", "price_range", "features"]
    }
  }
}
```

---

## 🔍 Utility APIs

### Session Management
```http
POST /api/sessions
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "user_789",
  "context": {}
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "created_at": "2024-01-20T10:30:00Z",
  "expires_at": "2024-01-20T14:30:00Z"
}
```

### Get Session Context
```http
GET /api/sessions/{session_id}/context
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "context": {
    "search_history": ["wireless headphones", "bluetooth speakers"],
    "viewed_products": ["prod_123", "prod_124"],
    "cart_items": ["cart_456"],
    "preferences": {
      "budget_max": 400,
      "preferred_brands": ["Sony", "Bose"]
    }
  },
  "last_updated": "2024-01-20T10:35:00Z"
}
```

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "services": {
    "database": "healthy",
    "ai_service": "healthy",
    "cache": "healthy"
  },
  "version": "1.0.0"
}
```

---

## 📊 Data Models

### Product Model
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "long_description": "string",
  "price": "number",
  "category": "string",
  "image_url": "string",
  "additional_images": ["string"],
  "in_stock": "boolean",
  "stock_quantity": "number",
  "rating": "number",
  "reviews_count": "number",
  "specifications": "object",
  "features": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Cart Item Model
```json
{
  "id": "string",
  "session_id": "string",
  "product_id": "string",
  "product_name": "string",
  "quantity": "number",
  "unit_price": "number",
  "total_price": "number",
  "added_at": "datetime"
}
```

### Search Context Model
```json
{
  "id": "string",
  "session_id": "string",
  "search_query": "string",
  "results": ["string"],
  "category": "string",
  "timestamp": "datetime"
}
```

---

## 🚨 Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with ID 'prod_999' was not found",
    "details": {
      "product_id": "prod_999",
      "suggestions": [
        {
          "id": "prod_123",
          "name": "Sony WH-1000XM4",
          "similarity": 0.75
        }
      ]
    }
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### Common Error Codes
- `PRODUCT_NOT_FOUND`: Product doesn't exist
- `INVALID_PRODUCT_ID`: Product ID not in search context
- `INSUFFICIENT_STOCK`: Not enough inventory
- `SESSION_EXPIRED`: Session no longer valid
- `VALIDATION_ERROR`: Invalid request parameters
- `AI_SERVICE_ERROR`: AI service unavailable
- `RATE_LIMIT_EXCEEDED`: Too many requests

---

## 🔐 Security Considerations

### Input Validation
- All inputs sanitized and validated
- SQL injection prevention
- XSS protection
- Rate limiting on all endpoints

### CORS Configuration
```json
{
  "origins": ["http://localhost:3000", "https://yourdomain.com"],
  "methods": ["GET", "POST"],
  "allow_headers": ["Content-Type", "Authorization"]
}
```

### Rate Limiting
- 100 requests per minute per session
- 1000 SSE connections per hour per IP
- Exponential backoff for failures