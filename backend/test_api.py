#!/usr/bin/env python3
"""
Test script for ReaperGT API endpoints.
This script helps you test the API endpoints with proper Cognito authentication.
"""

import requests
import json
import sys

# Configuration - Update these values after deployment
API_BASE_URL = "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/Prod"
COGNITO_TOKEN = "your-cognito-jwt-token-here"  # Get this from your frontend after user login

def make_authenticated_request(method, endpoint, data=None):
    """Make an authenticated request to the API."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {COGNITO_TOKEN}"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return None
        
        print(f"\n{method.upper()} {endpoint}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response
        
    except Exception as e:
        print(f"Error making request: {e}")
        return None

def test_all_endpoints():
    """Test all API endpoints."""
    print("Testing ReaperGT API Endpoints")
    print("=" * 50)
    
    # Test GET /crns
    make_authenticated_request("GET", "/crns")
    
    # Test POST /crns
    test_crn = "12345"  # Replace with a valid CRN
    make_authenticated_request("POST", "/crns", {"crn": test_crn})
    
    # Test GET /crn/{crn}
    make_authenticated_request("GET", f"/crn/{test_crn}")
    
    # Test POST /register-push
    push_subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/example",
        "keys": {
            "p256dh": "example-p256dh-key",
            "auth": "example-auth-key"
        }
    }
    make_authenticated_request("POST", "/register-push", {"push_subscription": push_subscription})
    
    # Test DELETE /crns/{crn}
    make_authenticated_request("DELETE", f"/crns/{test_crn}")

def test_specific_endpoint():
    """Test a specific endpoint."""
    print("Available endpoints:")
    print("1. GET /crns")
    print("2. POST /crns")
    print("3. GET /crn/{crn}")
    print("4. DELETE /crns/{crn}")
    print("5. POST /register-push")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == "1":
        make_authenticated_request("GET", "/crns")
    elif choice == "2":
        crn = input("Enter CRN to add: ")
        make_authenticated_request("POST", "/crns", {"crn": crn})
    elif choice == "3":
        crn = input("Enter CRN to get info for: ")
        make_authenticated_request("GET", f"/crn/{crn}")
    elif choice == "4":
        crn = input("Enter CRN to delete: ")
        make_authenticated_request("DELETE", f"/crns/{crn}")
    elif choice == "5":
        endpoint = input("Enter push subscription endpoint: ")
        p256dh = input("Enter p256dh key: ")
        auth = input("Enter auth key: ")
        push_subscription = {
            "endpoint": endpoint,
            "keys": {
                "p256dh": p256dh,
                "auth": auth
            }
        }
        make_authenticated_request("POST", "/register-push", {"push_subscription": push_subscription})
    else:
        print("Invalid choice")

if __name__ == "__main__":
    print("ReaperGT API Test Script")
    print("Before running this script:")
    print("1. Update API_BASE_URL with your actual API Gateway URL")
    print("2. Update COGNITO_TOKEN with a valid JWT token from Cognito")
    print("3. Make sure your Lambda functions are deployed")
    
    if API_BASE_URL == "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/Prod":
        print("\nERROR: Please update API_BASE_URL in this script first!")
        sys.exit(1)
    
    if COGNITO_TOKEN == "your-cognito-jwt-token-here":
        print("\nERROR: Please update COGNITO_TOKEN in this script first!")
        sys.exit(1)
    
    choice = input("\nTest all endpoints (a) or specific endpoint (s)? ")
    
    if choice.lower() == "a":
        test_all_endpoints()
    elif choice.lower() == "s":
        test_specific_endpoint()
    else:
        print("Invalid choice") 