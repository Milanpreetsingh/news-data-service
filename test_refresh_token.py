#!/usr/bin/env python3
"""
Test script for refresh token implementation
Run this after starting the server to test the new endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_refresh_token_flow():
    print("=" * 60)
    print("Testing Refresh Token Implementation")
    print("=" * 60)
    
    session = requests.Session()
    
    print("\n1. Creating test user...")
    signup_data = {
        "email": "refreshtest@example.com",
        "username": "refreshtester",
        "password": "test123456"
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if response.status_code == 201:
            print("✓ User created successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✓ User already exists (proceeding with login)")
        else:
            print(f"✗ Signup failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"✗ Signup error: {e}")
        return
    
    print("\n2. Logging in...")
    login_data = {
        "email": "refreshtest@example.com",
        "password": "test123456"
    }
    
    try:
        response = session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            print("✓ Login successful")
            print(f"  - Access token received: {access_token[:20]}...")
            print(f"  - Token type: {data.get('token_type')}")
            
            if "Authorization" in response.headers:
                print(f"  - Authorization header set: {response.headers['Authorization'][:30]}...")
            else:
                print("  ⚠ Authorization header NOT found in response")
            
            if "refresh_token" in [cookie.name for cookie in session.cookies]:
                print("  - Refresh token cookie set")
            else:
                print("  ⚠ Refresh token cookie NOT found")
                print(f"  Cookies: {list(session.cookies)}")
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"✗ Login error: {e}")
        return
    
    print("\n3. Testing refresh token endpoint...")
    try:
        response = session.post(f"{BASE_URL}/auth/refresh")
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            
            print("✓ Token refresh successful")
            print(f"  - New access token: {new_access_token[:20]}...")
            print(f"  - Token type: {data.get('token_type')}")
            
            if "Authorization" in response.headers:
                print(f"  - Authorization header set: {response.headers['Authorization'][:30]}...")
            else:
                print("  ⚠ Authorization header NOT found in response")
            
            if new_access_token != access_token:
                print("  ✓ New token is different from old token")
            else:
                print("  ⚠ Warning: New token is same as old token")
        else:
            print(f"✗ Refresh failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Refresh error: {e}")
    
    print("\n4. Testing logout...")
    try:
        response = session.post(f"{BASE_URL}/auth/logout")
        if response.status_code == 200:
            data = response.json()
            print("✓ Logout successful")
            print(f"  - Message: {data.get('message')}")
            
            if "refresh_token" not in [cookie.name for cookie in session.cookies]:
                print("  ✓ Refresh token cookie cleared")
            else:
                print("  ⚠ Refresh token cookie still present")
        else:
            print(f"✗ Logout failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Logout error: {e}")
    
    print("\n5. Testing refresh after logout (should fail)...")
    try:
        response = session.post(f"{BASE_URL}/auth/refresh")
        if response.status_code == 401:
            print("✓ Refresh correctly denied after logout")
        else:
            print(f"⚠ Unexpected status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_refresh_token_flow()
