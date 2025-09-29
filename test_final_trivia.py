#!/usr/bin/env python3
"""
Final test script for the Baybayin trivia system
Tests both question generation and answer submission for guest users
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_guest_trivia_flow():
    """Test complete guest trivia flow"""
    print("🎯 Testing Guest Trivia Flow")
    print("=" * 50)
    
    # Create a session
    session = requests.Session()
    
    # Test 1: Get a question
    print("\n1. Getting a trivia question...")
    try:
        response = session.get(f"{BASE_URL}/api/trivia/question/")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Question: {data['trivia']['question']}")
            print(f"📊 Game State: Level {data['game_state']['level']}, XP {data['game_state']['current_xp']}/{data['game_state']['target_xp']}, Moves {data['game_state']['moves_remaining']}")
            
            # Test 2: Submit a wrong answer
            print(f"\n2. Submitting incorrect answer...")
            answer_data = {
                'user_answer': 'Wrong Answer'
            }
            answer_response = session.post(f"{BASE_URL}/api/trivia/submit/", json=answer_data)
            print(f"Status: {answer_response.status_code}")
            
            if answer_response.status_code == 200:
                result = answer_response.json()
                print(f"✅ Result: {result['result']}")
                print(f"🎯 Correct Answer: {result['correct_answer']}")
                print(f"⭐ Points: {result['points']}")
                print(f"📊 Updated Game State: Level {result['game_state']['level']}, XP {result['game_state']['current_xp']}/{result['game_state']['target_xp']}, Moves {result['game_state']['moves_remaining']}")
                print(f"🏆 Level Completed: {result['game_state'].get('level_completed', False)}")
                print(f"💀 Level Failed: {result['game_state'].get('level_failed', False)}")
                
                # Test 3: Get another question to test session persistence
                print(f"\n3. Getting another question to test session persistence...")
                response2 = session.get(f"{BASE_URL}/api/trivia/question/")
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"✅ New Question: {data2['trivia']['question']}")
                    print(f"📊 Persistent Game State: Level {data2['game_state']['level']}, XP {data2['game_state']['current_xp']}/{data2['game_state']['target_xp']}, Moves {data2['game_state']['moves_remaining']}")
                else:
                    print(f"❌ Failed to get second question: {response2.status_code}")
            else:
                print(f"❌ Failed to submit answer: {answer_response.status_code}")
                print(f"Response: {answer_response.text}")
        else:
            print(f"❌ Failed to get question: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure Django server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_level_progression():
    """Test level progression by answering correctly multiple times"""
    print("\n\n🎯 Testing Level Progression")
    print("=" * 50)
    
    session = requests.Session()
    
    for i in range(5):  # Test 5 questions
        print(f"\n--- Question {i+1} ---")
        
        # Get question
        response = session.get(f"{BASE_URL}/api/trivia/question/")
        if response.status_code != 200:
            print(f"❌ Failed to get question {i+1}")
            continue
            
        data = response.json()
        correct_answer = data['trivia']['choices'][0]  # Assume first choice is correct for testing
        print(f"Q: {data['trivia']['question']}")
        print(f"Game State: L{data['game_state']['level']} XP:{data['game_state']['current_xp']}/{data['game_state']['target_xp']} M:{data['game_state']['moves_remaining']}")
        
        # Submit correct answer
        answer_response = session.post(f"{BASE_URL}/api/trivia/submit/", json={'user_answer': correct_answer})
        if answer_response.status_code == 200:
            result = answer_response.json()
            print(f"✅ {result['result']} (+{result['points']} points)")
            print(f"Updated: L{result['game_state']['level']} XP:{result['game_state']['current_xp']}/{result['game_state']['target_xp']} M:{result['game_state']['moves_remaining']}")
            
            if result['game_state'].get('level_completed'):
                print(f"🎉 LEVEL COMPLETED!")
            if result['game_state'].get('level_failed'):
                print(f"💀 LEVEL FAILED!")
        else:
            print(f"❌ Failed to submit answer")
        
        time.sleep(0.5)  # Small delay between requests

if __name__ == "__main__":
    print("🎮 Final Baybayin Trivia System Test")
    print("=" * 60)
    
    # Test basic flow
    success = test_guest_trivia_flow()
    
    if success:
        # Test level progression
        test_level_progression()
    
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
