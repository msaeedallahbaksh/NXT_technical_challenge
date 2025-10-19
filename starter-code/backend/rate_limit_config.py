"""
Rate Limiting Config

RATE LIMITING STRATEGIES USED HERE:
1. Per-IP rate limiting: Each IP address has its own limit
2. Different limits per endpoint: Critical endpoints have stricter limits
3. Sliding window: More accurate than fixed windows
4. Graceful degradation: Clear error messages when limits are hit

"""

import os
from typing import Dict


class RateLimitConfig:
    """
    Rate limiting configuration for different endpoint types.
    
    This class defines rate limits for various operations in the application.
    You can adjust these values based on your needs and server capacity.
    """
    
    # GENERAL API LIMITS
    # These apply to regular API endpoints
    
    # Health check: Very generous since it's just checking if server is alive
    HEALTH_CHECK_LIMIT = "100/minute"
    
    # Session creation: Moderate limit to prevent session flooding
    CREATE_SESSION_LIMIT = "10/minute"  # Can create 10 sessions per minute per IP
    
    # Session context retrieval: Generous since it's just reading data
    GET_SESSION_CONTEXT_LIMIT = "60/minute"
    
    
    # CHAT & MESSAGING LIMITS
    # Most important because they trigger AI calls which cost money
    
    # Sending messages to AI: STRICT limit because each message costs money
    # and uses AI API credits
    SEND_MESSAGE_LIMIT = "20/minute"  # 20 messages per minute per IP
    # Why? AI APIs charge per message and can be expensive. This prevents
    # someone from sending 1000 messages and causing a huge bill.
    
    # SSE stream connection: Moderate limit
    SSE_STREAM_LIMIT = "10/minute"  # Can open 10 SSE connections per minute
    # Why? Each SSE connection holds server resources. Too many connections
    # from one IP could exhaust server capacity.
    
    
    # FUNCTION CALL LIMITS (AI-triggered actions)
    # These are triggered by AI but we still limit them for safety
    
    # Product search: Moderate limit for database queries
    SEARCH_PRODUCTS_LIMIT = "30/minute"  # 30 searches per minute
    # Why? Searches query the database. Too many could slow down the DB
    # for other users.
    
    # Product details: Generous limit (less intensive than search)
    PRODUCT_DETAILS_LIMIT = "50/minute"
    # Why? This is a simple database lookup by ID. Relatively cheap operation.
    
    # Add to cart: Moderate limit
    ADD_TO_CART_LIMIT = "30/minute"
    # Why? This writes to the database. We want to prevent someone from
    # adding items to cart thousands of times per minute.
    
    # Remove from cart: Same as add to cart
    REMOVE_FROM_CART_LIMIT = "30/minute"
    
    # Get cart: Generous (just reading data)
    GET_CART_LIMIT = "60/minute"
    
    # Get recommendations: Moderate (can be CPU intensive)
    GET_RECOMMENDATIONS_LIMIT = "30/minute"
    # Why? Recommendation algorithms can be computationally expensive.
    
    
    # BURST LIMITS (Short-term protection)
    # These prevent sudden spikes of traffic
    
    # Per-second limits to prevent rapid-fire requests
    MESSAGE_BURST_LIMIT = "5/second"  # Max 5 messages per second
    FUNCTION_BURST_LIMIT = "10/second"  # Max 10 function calls per second
    

    # CONFIGURATION HELPERS
    
    @classmethod
    def get_limit(cls, endpoint_type: str) -> str:
        """
        Get rate limit for a specific endpoint type.
        
        Args:
            endpoint_type: Type of endpoint (e.g., 'send_message', 'search_products')
            
        Returns:
            Rate limit string (e.g., '10/minute')
        """
        limit_map: Dict[str, str] = {
            'health': cls.HEALTH_CHECK_LIMIT,
            'create_session': cls.CREATE_SESSION_LIMIT,
            'get_session_context': cls.GET_SESSION_CONTEXT_LIMIT,
            'send_message': cls.SEND_MESSAGE_LIMIT,
            'sse_stream': cls.SSE_STREAM_LIMIT,
            'search_products': cls.SEARCH_PRODUCTS_LIMIT,
            'product_details': cls.PRODUCT_DETAILS_LIMIT,
            'add_to_cart': cls.ADD_TO_CART_LIMIT,
            'remove_from_cart': cls.REMOVE_FROM_CART_LIMIT,
            'get_cart': cls.GET_CART_LIMIT,
            'get_recommendations': cls.GET_RECOMMENDATIONS_LIMIT,
        }
        
        return limit_map.get(endpoint_type, "100/minute")  # Default limit
    
    @classmethod
    def is_enabled(cls) -> bool:
        """
        Check if rate limiting is enabled via environment variable.
        
        You can disable rate limiting during development by setting:
        RATE_LIMIT_ENABLED=false
        
        In production, always keep this enabled!
        """
        return os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    @classmethod
    def get_storage_uri(cls) -> str:
        """
        Get storage URI for rate limit data.
        
        Two options:
        1. Memory storage (default): Fast but doesn't work across multiple servers
           Use for: Development, single-server deployments
           
        2. Redis storage: Slower but works across multiple servers
           Use for: Production with multiple servers (load balanced)
           
        Set REDIS_URL environment variable to use Redis:
        REDIS_URL=redis://localhost:6379
        """
        redis_url = os.getenv("REDIS_URL")
        
        if redis_url:
            return redis_url  # Use Redis for distributed rate limiting
        else:
            return "memory://"  # Use in-memory storage (single server only)


# HUMAN-READABLE EXPLANATIONS

RATE_LIMIT_EXPLANATIONS = {
    "send_message": (
        "You can send up to 20 messages per minute. "
        "This protects our AI API costs and ensures fair usage for all users."
    ),
    "search_products": (
        "You can search up to 30 times per minute. "
        "This prevents database overload and ensures fast responses for everyone."
    ),
    "add_to_cart": (
        "You can add items to cart up to 30 times per minute. "
        "This prevents accidental duplicate additions and database strain."
    ),
    "sse_stream": (
        "You can open up to 10 connections per minute. "
        "This protects server resources and prevents connection exhaustion."
    ),
}


def get_rate_limit_error_message(endpoint_type: str, limit: str) -> str:
    """
    Generate a user-friendly error message when rate limit is hit.
    
    Args:
        endpoint_type: Type of endpoint that was rate limited
        limit: The rate limit that was exceeded (e.g., '10/minute')
        
    Returns:
        Human-readable error message
    """
    explanation = RATE_LIMIT_EXPLANATIONS.get(
        endpoint_type,
        "This action has rate limiting to ensure fair usage for all users."
    )
    
    return (
        f"⏱️ Rate limit exceeded. {explanation}\n"
        f"Limit: {limit}\n"
        f"Please wait a moment before trying again."
    )

