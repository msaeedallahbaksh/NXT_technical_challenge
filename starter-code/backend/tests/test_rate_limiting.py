#!/usr/bin/env python3
"""
Rate Limiting Test Script

This script tests the rate limiting functionality of your API.
It sends multiple requests to various endpoints and shows when
rate limits are hit.

Usage:
    python test_rate_limiting.py
"""

import requests
import time
from datetime import datetime
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message: str):
    """Print info message"""
    print(f"  {message}")


def test_endpoint(
    url: str,
    method: str = "GET",
    json_data: Dict[str, Any] = None,
    expected_limit: int = 0,
    delay: float = 0.5
):
    """
    Test an endpoint's rate limiting.
    
    Args:
        url: Endpoint URL
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        expected_limit: Expected rate limit (for display)
        delay: Delay between requests in seconds
    """
    print_section(f"Testing: {url}")
    print_info(f"Expected limit: {expected_limit} requests/minute")
    print_info(f"Method: {method}")
    print_info("")
    
    request_count = 0
    rate_limited = False
    
    # Send requests until we hit the rate limit or reach max attempts
    max_attempts = expected_limit + 10 if expected_limit else 30
    
    for i in range(1, max_attempts + 1):
        try:
            # Make request
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=json_data, timeout=5)
            
            # Check status
            if response.status_code == 200:
                request_count += 1
                print_success(f"Request {i:2d}: Success (200 OK)")
            elif response.status_code == 429:
                # Rate limit hit!
                rate_limited = True
                data = response.json()
                print_error(f"Request {i:2d}: RATE LIMITED (429)")
                print_info(f"  Message: {data.get('message', 'Rate limit exceeded')[:80]}...")
                print_info(f"  Retry after: {data.get('retry_after', 'N/A')}")
                break
            else:
                print_warning(f"Request {i:2d}: Unexpected status {response.status_code}")
            
            # Small delay between requests
            time.sleep(delay)
            
        except requests.exceptions.ConnectionError:
            print_error(f"Connection failed! Is the server running?")
            return False
        except requests.exceptions.Timeout:
            print_warning(f"Request {i:2d}: Timeout")
        except Exception as e:
            print_error(f"Request {i:2d}: Error - {str(e)}")
    
    # Summary
    print_info("")
    if rate_limited:
        print_success(f"✓ Rate limiting is working!")
        print_info(f"  Successful requests: {request_count}")
        print_info(f"  Rate limited after: {request_count} requests")
        if expected_limit and abs(request_count - expected_limit) <= 2:
            print_success(f"  Matches expected limit of ~{expected_limit}")
        return True
    else:
        print_warning(f"⚠ Did not hit rate limit after {request_count} requests")
        if expected_limit:
            print_warning(f"  Expected to be limited around {expected_limit} requests")
        return False


def main():
    """Main test function"""
    API_URL = "http://localhost:8000"
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  RATE LIMITING TEST SUITE{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    print_info(f"Testing API at: {API_URL}")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create a test session first
    print_section("Setting up test session")
    try:
        response = requests.post(f"{API_URL}/api/sessions", json={})
        if response.status_code == 200:
            session_id = response.json().get("session_id")
            print_success(f"Created test session: {session_id}")
        else:
            print_error("Failed to create session")
            session_id = "test-session-123"
            print_warning(f"Using fallback session: {session_id}")
    except Exception as e:
        print_error(f"Error creating session: {e}")
        session_id = "test-session-123"
        print_warning(f"Using fallback session: {session_id}")
    
    # Test different endpoints
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check (100/minute - generous)
    tests_total += 1
    print_info("\n" + "="*60)
    if test_endpoint(
        f"{API_URL}/health",
        method="GET",
        expected_limit=100,
        delay=0.1  # Faster for this one since limit is high
    ):
        tests_passed += 1
    
    input("\nPress Enter to continue to next test...")
    
    # Test 2: Send Message (20/minute - strict!)
    tests_total += 1
    print_info("\n" + "="*60)
    if test_endpoint(
        f"{API_URL}/api/chat/{session_id}/message",
        method="POST",
        json_data={"message": "Test message", "context": {}},
        expected_limit=20,
        delay=2  # Slower since limit is lower
    ):
        tests_passed += 1
    
    input("\nPress Enter to continue to next test...")
    
    # Test 3: Search Products (30/minute)
    tests_total += 1
    print_info("\n" + "="*60)
    if test_endpoint(
        f"{API_URL}/api/functions/search_products",
        method="POST",
        json_data={
            "query": "test",
            "session_id": session_id
        },
        expected_limit=30,
        delay=1.5
    ):
        tests_passed += 1
    
    # Final summary
    print_section("TEST SUMMARY")
    print_info(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print_success("✓ All rate limiting tests passed!")
    elif tests_passed > 0:
        print_warning(f"⚠ {tests_passed} out of {tests_total} tests passed")
    else:
        print_error("✗ All tests failed. Check if rate limiting is enabled.")
    
    print_info("")
    print_info("To disable rate limiting during development:")
    print_info("  export RATE_LIMIT_ENABLED=false")
    print_info("")
    print_info("For more info, see: RATE_LIMITING_GUIDE.md")
    print_info("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")

