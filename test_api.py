#!/usr/bin/env python3
"""
Simple test script for the Koisk LLM API.
Run this after starting the Docker container to test all endpoints.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test an API endpoint and print results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=data,
                headers={"Content-Type": "application/json"}
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Is the server running?")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    """Run all API tests."""
    print("🚀 Starting Koisk LLM API Tests")
    print(f"Base URL: {BASE_URL}")
    
    # Wait a moment for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test 1: Basic endpoints
    test_endpoint("GET", "/", description="Root endpoint")
    test_endpoint("GET", "/health", description="Health check")
    
    # Test 2: Text interactions
    test_endpoint("POST", "/interact", 
                 data={"text": "Hello, how are you?"}, 
                 description="Greeting interaction")
    
    test_endpoint("POST", "/interact", 
                 data={"text": "Can you help me?"}, 
                 description="Help request")
    
    test_endpoint("POST", "/interact", 
                 data={"text": "Thank you for your help"}, 
                 description="Thank you interaction")
    
    test_endpoint("POST", "/interact", 
                 data={"text": "What services do you offer?"}, 
                 description="General question")
    
    # Test 3: Audio interaction (mock)
    test_endpoint("POST", "/interact", 
                 data={"audio_file": "test_audio.wav"}, 
                 description="Audio interaction (mock)")
    
    # Test 4: Error cases
    test_endpoint("POST", "/interact", 
                 data={}, 
                 description="Empty request (should fail)")
    
    test_endpoint("GET", "/invalid", 
                 description="Invalid endpoint (should return 404)")
    
    # Test 5: API documentation
    print(f"\n{'='*60}")
    print("📚 API Documentation URLs:")
    print(f"{'='*60}")
    print(f"Swagger UI: {BASE_URL}/docs")
    print(f"ReDoc: {BASE_URL}/redoc")
    print(f"OpenAPI JSON: {BASE_URL}/openapi.json")
    
    print(f"\n{'='*60}")
    print("🎉 All tests completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
