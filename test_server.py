#!/usr/bin/env python3
"""Test script to validate the FastAPI server and form submission."""

import sys
import json
import requests
from urllib.parse import urlencode

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_config():
    """Test config endpoint."""
    print("\nTesting /config endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/config", timeout=5)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(resp.json(), indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_form_submission():
    """Test form submission to /chat endpoint."""
    print("\nTesting form submission to /chat endpoint...")
    try:
        # Simulate form submission with headers
        data = {
            "message": "test message",
            "model": "ollama:gpt-4o",
            "gitlab_url": "https://gitlab.example.com",
        }
        
        headers = {
            "HX-Request": "true",
        }
        
        resp = requests.post(
            f"{BASE_URL}/chat",
            data=data,
            headers=headers,
            timeout=30,
        )
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('content-type')}")
        print(f"  Response preview: {resp.text[:200]}")
        
        if resp.status_code != 200:
            print(f"  Full Response: {resp.text}")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_submission():
    """Test JSON submission to /chat endpoint."""
    print("\nTesting JSON submission to /chat endpoint...")
    try:
        data = {
            "message": "test message",
            "model": "ollama:gpt-4o",
            "gitlab_url": "https://gitlab.example.com",
        }
        
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=data,
            timeout=30,
        )
        
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== FastAPI Server Tests ===\n")
    
    results = {
        "health": test_health(),
        "config": test_config(),
        "form_submission": test_form_submission(),
        "json_submission": test_json_submission(),
    }
    
    print("\n=== Summary ===")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
