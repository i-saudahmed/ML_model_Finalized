#!/usr/bin/env python3
"""
Simple test script for the ML Model API
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        return False

def test_basic_endpoint():
    """Test the basic endpoint"""
    print("🔍 Testing basic endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Basic endpoint passed: {data['message']}")
            return True
        else:
            print(f"❌ Basic endpoint failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Basic endpoint failed with error: {e}")
        return False

def test_rank_endpoint():
    """Test the rank endpoint with sample data"""
    print("🔍 Testing rank endpoint...")
    
    # Sample test data
    test_data = {
        "jobId": "test-job-123",
        "description": "We are looking for a Python developer with experience in machine learning and Flask. Bachelor's degree required. 2-3 years experience preferred."
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/rank",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rank endpoint passed: Received {len(data)} results")
            return True
        elif response.status_code == 404:
            data = response.json()
            if "No resumes found" in data.get("message", ""):
                print("✅ Rank endpoint working (no resumes found for test job)")
                return True
            else:
                print(f"❌ Unexpected 404 response: {data}")
                return False
        else:
            print(f"❌ Rank endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Rank endpoint failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting ML Model API Tests...")
    print("=" * 50)
    
    tests = [
        test_basic_endpoint,
        test_health_check,
        test_rank_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the API configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
