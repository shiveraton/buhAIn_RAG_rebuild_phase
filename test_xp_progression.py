#!/usr/bin/env python3
"""
Test script to verify XP persistence and level progression
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_xp_persistence_and_level_progression():
    """Test that XP persists and level advances correctly"""
    print("🎯 Testing XP Persistence and Level Progression")
    print("=" * 60)
    
    session = requests.Session()
    
    print("\n1. Getting initial game state...")
    response = session.get(f"{BASE_URL}/api/trivia/game-state/")
    if response.status_code == 200:
        initial_state = response.json()
        print(f"Initial state: Level {initial_state['level']}, XP {initial_state['current_xp']}/{initial_state['target_xp']}, Moves {initial_state['moves_remaining']}")
    
    question_count = 0
    max_questions = 20  # Safety limit
    
    while question_count < max_questions:
        question_count += 1
        print(f"\n--- Question {question_count} ---")
        
        # Get question
        response = session.get(f"{BASE_URL}/api/trivia/question/")
        if response.status_code != 200:
            print(f"❌ Failed to get question: {response.status_code}")
            break
            
        data = response.json()
        question = data['trivia']['question']
        options = data['trivia']['options']
        current_state = data['game_state']
        
        print(f"Q: {question}")
        print(f"Game State: L{current_state['level']} XP:{current_state['current_xp']}/{current_state['target_xp']} M:{current_state['moves_remaining']}")
        
        # Answer correctly to gain XP (use first option)
        correct_answer = options[0] if options else "Unknown"
        
        answer_response = session.post(f"{BASE_URL}/api/trivia/submit/", json={'user_answer': correct_answer})
        if answer_response.status_code != 200:
            print(f"❌ Failed to submit answer: {answer_response.status_code}")
            break
            
        result = answer_response.json()
        new_state = result['game_state']
        
        result_emoji = "✅" if result['result'] == 'correct' else "❌"
        points_text = f"+{result['points']}" if result['points'] > 0 else str(result['points'])
        
        print(f"{result_emoji} {result['result']} ({points_text} XP)")
        print(f"Updated: L{new_state['level']} XP:{new_state['current_xp']}/{new_state['target_xp']} M:{new_state['moves_remaining']}")
        
        # Check for level progression
        if new_state.get('level_completed'):
            print(f"🎉 LEVEL {current_state['level']} COMPLETED! Advanced to Level {new_state['level']}")
            print(f"   New target: {new_state['target_xp']} XP, {new_state['moves_remaining']} moves")
        
        if new_state.get('level_failed'):
            print(f"💀 LEVEL {new_state['level']} FAILED - Ran out of moves")
            
        # Stop if level completed or failed
        if new_state.get('level_completed') or new_state.get('level_failed'):
            break
            
        # Stop if no moves left
        if new_state['moves_remaining'] <= 0:
            print("⚠️  No moves remaining")
            break
            
        time.sleep(0.5)
    
    print(f"\n🏁 Test completed after {question_count} questions")

def test_session_persistence():
    """Test that XP persists across multiple requests"""
    print("\n\n🔄 Testing Session Persistence")
    print("=" * 60)
    
    session = requests.Session()
    
    # Get initial state
    response1 = session.get(f"{BASE_URL}/api/trivia/game-state/")
    if response1.status_code == 200:
        state1 = response1.json()
        print(f"Initial XP: {state1['current_xp']}")
    
    # Get a question and answer it
    question_response = session.get(f"{BASE_URL}/api/trivia/question/")
    if question_response.status_code == 200:
        data = question_response.json()
        options = data['trivia']['options']
        
        # Submit answer
        answer_response = session.post(f"{BASE_URL}/api/trivia/submit/", json={'user_answer': options[0]})
        if answer_response.status_code == 200:
            result = answer_response.json()
            new_xp = result['game_state']['current_xp']
            print(f"After answering: {new_xp} XP (gained {result['points']})")
    
    # Get state again to confirm persistence
    response2 = session.get(f"{BASE_URL}/api/trivia/game-state/")
    if response2.status_code == 200:
        state2 = response2.json()
        print(f"Persistent XP: {state2['current_xp']}")
        
        if state1['current_xp'] != state2['current_xp']:
            print("✅ XP correctly persisted across requests!")
        else:
            print("⚠️  XP may not have changed")

if __name__ == "__main__":
    print("🎮 Testing Baybayin Trivia XP & Level System")
    print("=" * 70)
    
    try:
        test_xp_persistence_and_level_progression()
        test_session_persistence()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 Test completed!")
