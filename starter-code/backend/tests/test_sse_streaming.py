"""
Tests for Server-Sent Events (SSE) streaming functionality.

This module tests the SSE implementation for real-time communication
between the backend and frontend.
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient


class TestSSEConnection:
    """Tests for SSE connection establishment and management."""
    
    def test_sse_endpoint_exists(self, test_client: TestClient):
        """Test SSE endpoint is accessible."""
        # Create a session first
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Try to connect to SSE endpoint
        with test_client.stream("GET", f"/api/stream/{session_id}") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_sse_connection_headers(self, test_client: TestClient):
        """Test SSE connection has correct headers."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with test_client.stream("GET", f"/api/stream/{session_id}") as response:
            assert response.headers.get("cache-control") == "no-cache"
            assert response.headers.get("connection") == "keep-alive"
    
    def test_sse_invalid_session(self, test_client: TestClient):
        """Test SSE connection with invalid session ID."""
        response = test_client.get("/api/stream/invalid_session_id")
        
        # Should return error (404 or appropriate error code)
        assert response.status_code in [404, 400, 422]


class TestSSESendMessage:
    """Tests for sending messages through SSE."""
    
    def test_send_message_endpoint_exists(self, test_client: TestClient):
        """Test send message endpoint exists."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        response = test_client.post(
            f"/api/stream/{session_id}",
            json={"message": "Hello"}
        )
        
        # Endpoint should exist and accept messages
        assert response.status_code in [200, 202]
    
    def test_send_message_with_content(self, test_client: TestClient):
        """Test sending a message with content."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        message_data = {
            "message": "Search for headphones",
            "context": {}
        }
        
        response = test_client.post(
            f"/api/stream/{session_id}",
            json=message_data
        )
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "status" in data or "message" in data
    
    def test_send_empty_message(self, test_client: TestClient):
        """Test sending an empty message."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        response = test_client.post(
            f"/api/stream/{session_id}",
            json={"message": ""}
        )
        
        # Should handle empty message (either accept or reject)
        assert response.status_code in [200, 202, 400, 422]
    
    def test_send_message_invalid_session(self, test_client: TestClient):
        """Test sending message to invalid session."""
        response = test_client.post(
            "/api/stream/invalid_session",
            json={"message": "test"}
        )
        
        # Should return error
        assert response.status_code in [404, 400, 422]


class TestSSEEventTypes:
    """Tests for different SSE event types."""
    
    def test_sse_sends_connection_event(self, test_client: TestClient):
        """Test SSE sends connection event on connect."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with test_client.stream("GET", f"/api/stream/{session_id}") as response:
            # Read first event
            for line in response.iter_lines():
                if line:
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        assert event_type in ["connection", "ping", "text_chunk"]
                        break
                    elif line.startswith("data:"):
                        # Got data, check if it's valid JSON
                        data_str = line.split(":", 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            assert isinstance(data, dict)
                            break
                        except json.JSONDecodeError:
                            pass


class TestSSEErrorHandling:
    """Tests for SSE error handling."""
    
    def test_sse_handles_malformed_request(self, test_client: TestClient):
        """Test SSE handles malformed POST request."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        response = test_client.post(
            f"/api/stream/{session_id}",
            data="not json"
        )
        
        # Should return error
        assert response.status_code in [400, 422]
    
    def test_sse_handles_missing_message_field(self, test_client: TestClient):
        """Test SSE handles missing message field."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        response = test_client.post(
            f"/api/stream/{session_id}",
            json={"not_message": "test"}
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]


class TestSSEConnectionLifecycle:
    """Tests for SSE connection lifecycle management."""
    
    def test_sse_connection_can_be_reestablished(self, test_client: TestClient):
        """Test SSE connection can be closed and reopened."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # First connection
        with test_client.stream("GET", f"/api/stream/{session_id}") as response1:
            assert response1.status_code == 200
        
        # Second connection (should work after first is closed)
        with test_client.stream("GET", f"/api/stream/{session_id}") as response2:
            assert response2.status_code == 200
    
    def test_multiple_sessions_independent(self, test_client: TestClient):
        """Test multiple sessions are independent."""
        # Create two sessions
        session1 = test_client.post("/api/sessions").json()["session_id"]
        session2 = test_client.post("/api/sessions").json()["session_id"]
        
        assert session1 != session2
        
        # Both should work
        with test_client.stream("GET", f"/api/stream/{session1}") as response1:
            assert response1.status_code == 200
        
        with test_client.stream("GET", f"/api/stream/{session2}") as response2:
            assert response2.status_code == 200


class TestSSEPerformance:
    """Tests for SSE performance characteristics."""
    
    def test_sse_connection_responds_quickly(self, test_client: TestClient):
        """Test SSE connection establishment is fast."""
        import time
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        start = time.time()
        response = test_client.get(f"/api/stream/{session_id}")
        elapsed = time.time() - start
        
        # Should respond quickly (within 1 second)
        assert elapsed < 1.0
        assert response.status_code == 200
    
    def test_sse_handles_rapid_messages(self, test_client: TestClient):
        """Test SSE can handle rapid message sending."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Send multiple messages rapidly
        responses = []
        for i in range(5):
            response = test_client.post(
                f"/api/stream/{session_id}",
                json={"message": f"Message {i}"}
            )
            responses.append(response)
        
        # All should be accepted
        assert all(r.status_code in [200, 202] for r in responses)


class TestSSEFormat:
    """Tests for SSE message format compliance."""
    
    def test_sse_format_valid(self, test_client: TestClient):
        """Test SSE messages follow correct format."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with test_client.stream("GET", f"/api/stream/{session_id}") as response:
            event_found = False
            data_found = False
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.strip()
                
                if line.startswith("event:"):
                    event_found = True
                    # Event type should not be empty
                    event_type = line.split(":", 1)[1].strip()
                    assert len(event_type) > 0
                
                elif line.startswith("data:"):
                    data_found = True
                    # Data should be valid JSON or text
                    data_str = line.split(":", 1)[1].strip()
                    assert len(data_str) > 0
                
                elif line.startswith("id:"):
                    # ID should not be empty
                    event_id = line.split(":", 1)[1].strip()
                    assert len(event_id) > 0
                
                # Stop after processing a few lines
                if event_found and data_found:
                    break


class TestSSEWithFunctions:
    """Tests for SSE integration with function calls."""
    
    @pytest.mark.asyncio
    async def test_sse_triggers_function_call(
        self,
        async_test_client,
        test_session_id,
        sample_products
    ):
        """Test sending message through SSE can trigger function calls."""
        # This is an integration test that would require full SSE setup
        # For now, test that the POST endpoint works
        
        message_data = {
            "message": "Search for headphones",
            "context": {}
        }
        
        response = await async_test_client.post(
            f"/api/stream/{test_session_id}",
            json=message_data
        )
        
        # Should be accepted
        assert response.status_code in [200, 202]


class TestSSEConcurrency:
    """Tests for SSE concurrent connection handling."""
    
    def test_single_session_single_connection(self, test_client: TestClient):
        """Test single session with single connection works."""
        session_response = test_client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with test_client.stream("GET", f"/api/stream/{session_id}") as response:
            assert response.status_code == 200
            
            # Send a message while connected
            msg_response = test_client.post(
                f"/api/stream/{session_id}",
                json={"message": "test"}
            )
            assert msg_response.status_code in [200, 202]

