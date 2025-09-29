#!/usr/bin/env python3
"""
Simple test script to check session persistence
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/trivia"

def test_session_persistence():
    """Test if sessions persist between requests"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("🔧 Testing session persistence...")
    print("="*50)
    
    # Step 1: Set data in session
    print("\n📝 Step 1: Setting data in session...")
    set_response = session.get(f"{BASE_URL}/session-test/")
    print(f"Status: {set_response.status_code}")
    
    if set_response.status_code == 200:
        set_data = set_response.json()
        print(f"Session Key: {set_data.get('session_key')}")
        print(f"Test Data Set: {set_data.get('test_data')}")
        print(f"Cookies Received: {set_data.get('cookies')}")
    else:
        print(f"❌ Set failed: {set_response.text}")
        return
    
    # Step 2: Read data from session
    print("\n📖 Step 2: Reading data from session...")
    get_response = session.post(f"{BASE_URL}/session-test/")
    print(f"Status: {get_response.status_code}")
    
    if get_response.status_code == 200:
        get_data = get_response.json()
        print(f"Session Key: {get_data.get('session_key')}")
        print(f"Test Data Retrieved: {get_data.get('test_data')}")
        print(f"Session Keys: {get_data.get('session_keys')}")
        print(f"Cookies Sent: {get_data.get('cookies')}")
        
        # Check if session persisted
        if get_data.get('test_data') != 'NOT_FOUND':
            print("✅ Session persistence is WORKING!")
        else:
            print("❌ Session persistence is BROKEN!")
    else:
        print(f"❌ Get failed: {get_response.text}")

if __name__ == "__main__":
    test_session_persistence()
