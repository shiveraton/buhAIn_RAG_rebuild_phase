# baybayin_backend/game_seg_trivia/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import time
import logging
from .content_retrieval import get_adaptive_fact, get_random_fact

# Set up logging
logger = logging.getLogger(__name__)
from .trivia_generator import generate_trivia_from_fact, generate_trivia_with_rag, analyze_question_difficulty, calculate_points
from .adaptive_initializer import get_user_profile, update_user_profile, update_mastery_level
from .models import UserTriviaProfile, TriviaQuestionHistory
from django.contrib.auth.models import User
from .game_config import LEVELS, XP_VALUES
import random
import json
import base64
from django.utils import timezone

def create_question_token(trivia_data, start_time):
    """
    Create a stateless token containing question data for validation
    """
    token_data = {
        'question': trivia_data['question'],
        'answer': trivia_data['answer'],
        'options': trivia_data['options'],
        'start_time': start_time,
        'source_fact': trivia_data.get('source_fact'),
        'question_type': trivia_data.get('question_type', 'rag_generated'),
        'created_at': timezone.now().isoformat()
    }
    
    # Simple base64 encoding (not for security, just for transport)
    json_data = json.dumps(token_data)
    token = base64.b64encode(json_data.encode()).decode()
    return token

def decode_question_token(token):
    """
    Decode a question token back to trivia data
    """
    try:
        json_data = base64.b64decode(token.encode()).decode()
        return json.loads(json_data)
    except Exception as e:
        logger.error(f"Failed to decode question token: {e}")
        return None

@method_decorator(csrf_exempt, name='dispatch')
class TriviaTestView(APIView):
    """
    Test endpoint to verify API connectivity - no authentication required
    """
    permission_classes = []
    
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Trivia API is working!',
            'server_time': time.time()
        })

@method_decorator(csrf_exempt, name='dispatch')
class TriviaQuestionView(APIView):
    # Temporarily disable authentication for development
    permission_classes = []  # [IsAuthenticated]

    def get(self, request):
        """
        Get a new trivia question for the user with game state
        """
        logger.info(f"Get question request: user={request.user}, authenticated={request.user.is_authenticated}")
        logger.info(f"Session key: {request.session.session_key}")
        logger.info(f"Session engine: {request.session.__class__.__name__}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Cookies: {request.COOKIES}")
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            logger.info(f"Created new session: {request.session.session_key}")
        else:
            logger.info(f"Using existing session: {request.session.session_key}")
            
        # Test session write/read
        request.session['test_key'] = 'test_value'
        request.session.save()
        logger.info(f"Session test - wrote and saved test_key")
        test_read = request.session.get('test_key', 'NOT_FOUND')
        logger.info(f"Session test - read back: {test_read}")
        
        # Use RAG-powered LLM to generate dynamic questions
        if not request.user.is_authenticated:
            logger.info("Generating RAG-powered trivia for unauthenticated user")
            
            # Get recent question history to avoid repetition
            recent_questions = request.session.get('recent_questions', [])
            exclude_ids = recent_questions[-5:] if len(recent_questions) > 5 else recent_questions  # Last 5 questions
            
            # Create a minimal profile for RAG generation
            class MockProfile:
                def __init__(self):
                    self.user = None
                    self.current_level = 1
                    self.mastery_level = 1
                    self.top_weaknesses = []
                    self.accuracy_rate = 0.0

            mock_profile = MockProfile()
            
            try:
                # Try to use content retrieval for more targeted questions
                adaptive_fact = get_adaptive_fact(mock_profile, exclude_ids=exclude_ids)
                
                if adaptive_fact and random.random() < 0.4:  # 40% chance to use wiki content
                    logger.info("Using wiki content for RAG generation")
                    from .trivia_generator import generate_trivia_from_fact
                    trivia = generate_trivia_from_fact(adaptive_fact)
                    trivia['source_fact'] = adaptive_fact.id if hasattr(adaptive_fact, 'id') else None
                else:
                    # Use RAG to generate dynamic trivia about Baybayin
                    trivia = generate_trivia_with_rag(
                        "Baybayin script characters symbols meaning translation history", 
                        user_profile=mock_profile,
                        provider="deepseek",
                        recent_types=None
                    )
                
                logger.info(f"RAG generated question: {trivia.get('question', 'No question generated')[:100]}...")
                logger.info(f"RAG generated options: {trivia.get('options', [])}")
                logger.info(f"RAG generated answer: {trivia.get('answer', 'No answer')}")
                
                # Validate the RAG response structure
                if not isinstance(trivia.get('options'), list) or len(trivia.get('options', [])) < 2:
                    logger.warning("RAG response has invalid options format")
                    raise Exception("Invalid options structure")
                    
                # Ensure the trivia has required fields
                if not trivia.get('question') or not trivia.get('options') or not trivia.get('answer'):
                    logger.warning("RAG trivia incomplete, using fallback")
                    raise Exception("Incomplete RAG response")
                
                # Validate that the answer is one of the options
                answer = trivia.get('answer', '').strip()
                options = [opt.strip() for opt in trivia.get('options', [])]
                if answer not in options:
                    logger.warning(f"RAG answer '{answer}' not in options {options}")
                    # Try to find a close match
                    answer_lower = answer.lower()
                    for opt in options:
                        if opt.lower() == answer_lower:
                            trivia['answer'] = opt
                            logger.info(f"Fixed answer case mismatch: '{answer}' -> '{opt}'")
                            break
                    else:
                        raise Exception("Answer not found in options")
                        
            except Exception as e:
                logger.error(f"RAG generation failed: {e}")
                # Fallback to a simple question if RAG fails
                trivia = {
                    'question': 'What does the Baybayin script "ᜊ" represent?',
                    'options': ['Ba', 'Ka', 'Da', 'Ga'],
                    'answer': 'Ba'
                }
                logger.info("Using fallback question due to RAG failure")

            # Get existing guest game state from session or create default
            guest_game_state = request.session.get('guest_game_state', {
                'level': 1,
                'current_xp': 0,
                'target_xp': LEVELS[1]['target_xp'],  # Use game_config value
                'moves_remaining': LEVELS[1]['max_moves'],  # Use game_config value
                'consecutive_correct': 0,
                'mastery_level': 1,
                'accuracy_rate': 0.0,
                'total_questions': 0,  # Track for accuracy calculation
                'correct_answers': 0,  # Track for accuracy calculation
                'top_weaknesses': []
            })
            
            logger.info(f"📋 Current guest game state: Level {guest_game_state.get('level', 1)}, XP {guest_game_state.get('current_xp', 0)}/{guest_game_state.get('target_xp', 300)}, Moves {guest_game_state.get('moves_remaining', 12)}")

            # Save current trivia in session for answer validation
            request.session['current_trivia'] = {
                'trivia': trivia,
                'start_time': time.time(),
                'source_fact': trivia.get('source_facts'),
                'question_type': 'rag_generated'
            }

            # Track question for diversity (store question hash or first few words)
            question_id = hash(trivia['question'][:50])  # Use first 50 chars as ID
            recent_questions = request.session.get('recent_questions', [])
            recent_questions.append(question_id)
            request.session['recent_questions'] = recent_questions[-10:]  # Keep last 10

            # Also expose guest game state in session
            request.session['guest_game_state'] = guest_game_state
            
            # Force save the session
            request.session.save()
            logger.info(f"Saved RAG trivia session data, keys: {list(request.session.keys())}")
            logger.info(f"💾 Saved guest game state for next request: Level {guest_game_state['level']}, XP {guest_game_state['current_xp']}/{guest_game_state['target_xp']}")

            # Create stateless token as backup
            question_token = create_question_token(trivia, time.time())

            return Response({
                'trivia': {
                    'question': trivia['question'],
                    'options': trivia['options']
                },
                'game_state': guest_game_state,
                'question_token': question_token  # Add stateless token
            })
        
        # Original authenticated user code
        user = request.user
        profile = get_user_profile(user)
        
        # Initialize level if needed
        if profile.moves_remaining <= 0:
            profile.initialize_level()
            profile.save()
        
        # Get recent question types for diversity
        recent_types = TriviaQuestionHistory.objects.filter(
            user=user
        ).order_by('-timestamp').values_list('question_type', flat=True)[:3]
        
        # Generate trivia question with adaptive learning
        try:
            # 30% chance to focus on weak areas
            if profile.top_weaknesses and random.random() < 0.3:
                fact = get_adaptive_fact(profile)
                trivia = generate_trivia_from_fact(fact)
                trivia['source_fact'] = fact.id if fact else None
            else:
                # Use RAG for broader context
                trivia = generate_trivia_with_rag(
                    "Baybayin", 
                    profile, 
                    provider="deepseek",
                    recent_types=recent_types
                )
                trivia['source_fact'] = trivia.get('source_facts')
        except Exception as e:
            # Fallback to simple fact
            fact = get_adaptive_fact(profile) or get_random_fact()
            trivia = generate_trivia_from_fact(fact)
            trivia['source_fact'] = fact.id if fact else None
        
        # Analyze question type
        question_type = analyze_question_difficulty(trivia['question'])
        
        # Store necessary info in session for answer validation
        request.session['current_trivia'] = {
            'trivia': trivia,
            'start_time': time.time(),
            'source_fact': trivia.get('source_fact'),
            'question_type': question_type
        }
        
        # Force save the session
        request.session.save()
        logger.info(f"Saved authenticated user session data, keys: {list(request.session.keys())}")
        
        # Create stateless token as backup
        question_token = create_question_token(trivia, time.time())
        
        # Prepare game state response
        game_state = {
            'level': profile.current_level,
            'current_xp': profile.current_xp,
            'target_xp': profile.level_config['target_xp'],
            'moves_remaining': profile.moves_remaining,
            'consecutive_correct': profile.consecutive_correct,
            'mastery_level': profile.mastery_level,
            'accuracy_rate': profile.accuracy_rate,
            'top_weaknesses': profile.top_weaknesses
        }
        
        return Response({
            'trivia': {
                'question': trivia['question'],
                'options': trivia['options']
            },
            'game_state': game_state,
            'question_token': question_token  # Add stateless token
        })


@method_decorator(csrf_exempt, name='dispatch')
class SubmitAnswerView(APIView):
    permission_classes = []  # [IsAuthenticated]

    def post(self, request):
        """
        Submit an answer to the current trivia question
        """
        logger.info(f"Submit answer request: user={request.user}, authenticated={request.user.is_authenticated}")
        logger.info(f"Session key: {request.session.session_key}")
        logger.info(f"Session keys: {list(request.session.keys())}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Cookies: {request.COOKIES}")
        
        # Test session read
        test_read = request.session.get('test_key', 'NOT_FOUND')
        logger.info(f"Session test - can read test_key: {test_read}")
        
        # Force session creation if it doesn't exist
        if not request.session.session_key:
            request.session.create()
            logger.warning(f"No session found - created new session: {request.session.session_key}")
        
        data = request.data
        user_answer = data.get('user_answer', '').strip()
        question_token = data.get('question_token', '').strip()

        # Get the current question from session for RAG-generated questions
        current_trivia_session = request.session.get('current_trivia')
        
        if not current_trivia_session:
            logger.error("No current_trivia in session")
            logger.error(f"Available session keys: {list(request.session.keys())}")
            
            # Try to use stateless token as fallback
            if question_token:
                logger.warning("Session failed, trying stateless token fallback")
                token_data = decode_question_token(question_token)
                
                if token_data:
                    logger.info("Successfully decoded question token")
                    current_trivia_session = {
                        'trivia': {
                            'question': token_data['question'],
                            'answer': token_data['answer'],
                            'options': token_data['options']
                        },
                        'start_time': token_data['start_time'],
                        'source_fact': token_data.get('source_fact'),
                        'question_type': token_data.get('question_type', 'rag_generated')
                    }
                    logger.info("Using stateless token data for validation")
                else:
                    logger.error("Failed to decode question token")
            
            # If still no trivia data, return error
            if not current_trivia_session:
                return Response({
                    "error": "No active trivia question. Start a new one first.",
                    "debug": {
                        "session_key": request.session.session_key,
                        "session_keys": list(request.session.keys()),
                        "user_authenticated": request.user.is_authenticated,
                        "has_token": bool(question_token)
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract trivia data from session
        trivia = current_trivia_session['trivia']
        start_time = current_trivia_session['start_time']
        source_fact = current_trivia_session.get('source_fact')
        question_type = current_trivia_session.get('question_type', 'basic_fact')
        
        # Get the RAG-generated correct answer
        correct_answer = trivia.get('answer', '').strip()
        question_text = trivia.get('question', 'Unknown question')
        
        logger.info(f"Validating RAG question (type: {question_type})")
        logger.info(f"Question: {question_text[:100]}...")
        logger.info(f"User answer: '{user_answer}' vs RAG Correct: '{correct_answer}'")
        
        # Calculate time taken for answer
        answer_time = time.time() - start_time
        
        # Validate answer (case-insensitive, strip whitespace)
        is_correct = (user_answer.lower().strip() == correct_answer.lower().strip())
        
        # Initialize level completion flags
        level_completed = False
        level_failed = False
        
        # Handle user profiles and points calculation
        if request.user.is_authenticated:
            # Authenticated user - use full game system
            user = request.user
            profile = get_user_profile(user)
            
            # Calculate points using the sophisticated game system
            points = calculate_points(
                user_profile=profile,
                trivia=trivia,
                is_correct=is_correct,
                answer_time=answer_time,
                source_fact=source_fact
            )
            
            # Update user profile with learning data
            update_user_profile(
                user=user,
                question=trivia,
                user_answer=user_answer,
                correct_answer=correct_answer,
                source_fact=source_fact,
                question_type=question_type
            )
            
            # Update moves and XP - moves decrease regardless of correctness
            profile.moves_remaining -= 1
            
            # Add points (can be negative for incorrect answers based on game_config)
            if is_correct:
                profile.current_xp += points
                profile.consecutive_correct += 1
                logger.info(f"Correct answer: +{points} XP, consecutive: {profile.consecutive_correct}")
            else:
                # Apply negative points for incorrect answers (from XP_VALUES)
                profile.current_xp = max(0, profile.current_xp + points)  # Don't go below 0
                profile.consecutive_correct = 0
                logger.info(f"Incorrect answer: {points} XP penalty, consecutive reset")
            
            profile.save()
            
            # Update mastery level
            update_mastery_level(profile)
            
            # Check level completion/failure using game config
            # Level completion: Target XP reached
            if profile.current_xp >= profile.level_config['target_xp']:
                profile.complete_level()
                level_completed = True
                logger.info(f"User completed level {profile.current_level - 1}, advanced to {profile.current_level}")
            # Level failure: Ran out of moves without reaching target XP
            elif profile.moves_remaining <= 0:
                profile.fail_level()
                level_failed = True
                logger.info(f"User failed level {profile.current_level}, resetting level")
            
            profile.save()
            
            # Build response with real game state
            game_state = {
                "level": profile.current_level,
                "current_xp": profile.current_xp,
                "target_xp": profile.level_config['target_xp'],
                "moves_remaining": profile.moves_remaining,
                "consecutive_correct": profile.consecutive_correct,
                "mastery_level": profile.mastery_level,
                "accuracy_rate": profile.accuracy_rate,
                "top_weaknesses": profile.top_weaknesses,
                "level_completed": level_completed,
                "level_failed": level_failed
            }
            
        else:
            # Guest user - get current level and use appropriate difficulty
            current_guest_state = request.session.get('guest_game_state', {
                'level': 1,
                'current_xp': 0,
                'target_xp': LEVELS[1]['target_xp'],
                'moves_remaining': LEVELS[1]['max_moves'],
                'consecutive_correct': 0,
                'mastery_level': 1,
                'accuracy_rate': 0.0,
                'total_questions': 0,
                'correct_answers': 0,
                'top_weaknesses': []
            })
            
            # Get appropriate difficulty based on current level
            current_level = current_guest_state.get('level', 1)
            difficulty = LEVELS[current_level]['difficulty']
            
            logger.info(f"Guest user level {current_level}, using {difficulty} difficulty")
            
            # Use appropriate XP values for current level
            base_points = XP_VALUES[difficulty]["correct"] if is_correct else XP_VALUES[difficulty]["incorrect"]
            
            # Simple time bonus for guests (only for correct answers)
            time_multiplier = 1.0
            if is_correct and answer_time <= 10:  # Quick answer bonus
                time_multiplier = 1.3
            
            # Calculate points (can be negative for incorrect)
            points = int(base_points * time_multiplier) if is_correct else base_points
            
            logger.info(f"Guest points calculation: level={current_level}, difficulty={difficulty}, base={base_points}, multiplier={time_multiplier}, final={points}")
            
            # Use the current guest state (not create a new default one)
            guest_state = current_guest_state
            
            # Update guest state with proper accuracy calculation
            guest_state['moves_remaining'] -= 1  # Always decrease moves
            guest_state['total_questions'] = guest_state.get('total_questions', 0) + 1
            
            if is_correct:
                guest_state['current_xp'] += points
                guest_state['consecutive_correct'] += 1
                guest_state['correct_answers'] = guest_state.get('correct_answers', 0) + 1
                logger.info(f"Guest correct: +{points} XP, consecutive: {guest_state['consecutive_correct']}")
            else:
                # Apply penalty but don't go below 0 XP
                guest_state['current_xp'] = max(0, guest_state['current_xp'] + points)
                guest_state['consecutive_correct'] = 0
                logger.info(f"Guest incorrect: {points} XP penalty, consecutive reset")
            
            # Calculate accuracy using proper formula
            if guest_state['total_questions'] > 0:
                guest_state['accuracy_rate'] = (guest_state['correct_answers'] / guest_state['total_questions']) * 100
            
            # Save updated guest state
            request.session['guest_game_state'] = guest_state
            request.session.save()
            
            logger.info(f"💾 Saved guest state: {guest_state}")
            
            # Check guest level completion using LEVELS config
            current_level = guest_state.get('level', 1)
            current_xp = guest_state['current_xp']
            target_xp = guest_state['target_xp']
            moves_remaining = guest_state['moves_remaining']
            
            logger.info(f"Level completion check: Level {current_level}, XP {current_xp}/{target_xp}, Moves {moves_remaining}")
            
            # Level completion: Target XP reached
            level_completed = current_xp >= target_xp
            # Level failure: Ran out of moves without reaching target XP  
            level_failed = moves_remaining <= 0 and not level_completed
            
            logger.info(f"Level status: completed={level_completed}, failed={level_failed}")
            logger.info(f"📊 Final game state: level_completed={level_completed}, level_failed={level_failed}")
            
            # Handle level progression for guests
            if level_completed and current_level < 10:  # Max level is 10
                new_level = current_level + 1
                logger.info(f"🎉 Guest completed level {current_level}, advancing to {new_level}")
                logger.info(f"New level config: {LEVELS[new_level]}")
                guest_state.update({
                    'level': new_level,
                    'current_xp': 0,  # Reset XP for new level
                    'target_xp': LEVELS[new_level]['target_xp'],
                    'moves_remaining': LEVELS[new_level]['max_moves'],
                    'consecutive_correct': 0,  # Reset combo
                    'total_questions': guest_state.get('total_questions', 0),  # Keep total count
                    'correct_answers': guest_state.get('correct_answers', 0)   # Keep correct count
                })
                level_completed = True
            elif level_failed:
                logger.info(f"😔 Guest failed level {current_level}, resetting level")
                # Reset current level - keep progress stats but reset level progress
                guest_state.update({
                    'current_xp': 0,
                    'moves_remaining': LEVELS[current_level]['max_moves'],
                    'consecutive_correct': 0
                    # Keep total_questions and correct_answers for overall accuracy
                })

            game_state = {
                **guest_state,
                "level_completed": level_completed,
                "level_failed": level_failed
            }
        
        # Build final response with RAG-generated correct answer
        response_data = {
            "result": "correct" if is_correct else "incorrect",
            "correct_answer": correct_answer,  # This is now from RAG/LLM
            "points": points,
            "game_state": game_state
        }
        
        logger.info(f"🚀 Response data: result={response_data['result']}, points={response_data['points']}, level_completed={game_state.get('level_completed')}, level_failed={game_state.get('level_failed')}")
        
        # Clear the current trivia from session to allow new question generation
        if 'current_trivia' in request.session:
            del request.session['current_trivia']
            request.session.save()
            logger.info("Cleared current_trivia from session for next question")
        
        logger.info(f"Answer validation result: '{user_answer}' -> {'CORRECT' if is_correct else 'INCORRECT'}")
        logger.info(f"Points awarded: {points} (RAG answer: '{correct_answer}')")
        
        return Response(response_data)


@method_decorator(csrf_exempt, name='dispatch')
class GameStateView(APIView):
    permission_classes = []  # [IsAuthenticated]

    def get(self, request):
        """Get current game state without a new question"""
        logger.info(f"GameState request: user={request.user}, authenticated={request.user.is_authenticated}")
        logger.info(f"Session key: {request.session.session_key}")
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            logger.info(f"Created new session for game state: {request.session.session_key}")
        
        # If guest, return minimal session-stored state using LEVELS config
        if not request.user.is_authenticated:
            guest_state = request.session.get('guest_game_state', {
                'level': 1,
                'current_xp': 0,
                'target_xp': LEVELS[1]['target_xp'],  # Use game_config value
                'moves_remaining': LEVELS[1]['max_moves'],  # Use game_config value
                'consecutive_correct': 0,
                'mastery_level': 1,
                'accuracy_rate': 0.0,
                'total_questions': 0,
                'correct_answers': 0,
                'top_weaknesses': []
            })
            
            # Save default guest state if it doesn't exist
            if 'guest_game_state' not in request.session:
                request.session['guest_game_state'] = guest_state
                request.session.save()
                logger.info(f"Initialized guest game state in session")
                
            return Response(guest_state)

        user = request.user
        profile = get_user_profile(user)

        # Ensure level is initialized
        if profile.moves_remaining <= 0:
            profile.initialize_level()
            profile.save()

        return Response({
            'level': profile.current_level,
            'current_xp': profile.current_xp,
            'target_xp': profile.level_config['target_xp'],
            'moves_remaining': profile.moves_remaining,
            'consecutive_correct': profile.consecutive_correct,
            'mastery_level': profile.mastery_level,
            'accuracy_rate': profile.accuracy_rate,
            'top_weaknesses': profile.top_weaknesses
        })


@method_decorator(csrf_exempt, name='dispatch')
class ResetLevelView(APIView):
    permission_classes = []  # [IsAuthenticated]

    def post(self, request):
        """Reset current level progress"""
        logger.info(f"ResetLevel request: user={request.user}, authenticated={request.user.is_authenticated}")
        logger.info(f"Session key: {request.session.session_key}")
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            logger.info(f"Created new session for level reset: {request.session.session_key}")
            
        if not request.user.is_authenticated:
            # Reset guest state in session using LEVELS config
            request.session['guest_game_state'] = {
                'level': 1,
                'current_xp': 0,
                'target_xp': LEVELS[1]['target_xp'],  # Use game_config value
                'moves_remaining': LEVELS[1]['max_moves'],  # Use game_config value
                'consecutive_correct': 0,
                'mastery_level': 1,
                'accuracy_rate': 0.0,
                'total_questions': 0,
                'correct_answers': 0,
                'top_weaknesses': []
            }
            request.session.save()
            logger.info(f"Reset guest state in session")
            
            return Response({
                "message": "Guest level reset",
                "game_state": request.session['guest_game_state']
            })

        user = request.user
        profile = get_user_profile(user)
        profile.fail_level()
        profile.save()
        return Response({
            "message": "Level reset",
            "game_state": {
                'level': profile.current_level,
                'current_xp': profile.current_xp,
                'target_xp': profile.level_config['target_xp'],
                'moves_remaining': profile.moves_remaining
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class TriviaDebugView(APIView):
    """
    Debug endpoint to test RAG generation directly
    """
    permission_classes = []
    
    def get(self, request):
        """Test RAG generation without session management"""
        logger.info("Debug RAG generation test")
        
        # Create a minimal profile for RAG generation
        class MockProfile:
            def __init__(self):
                self.user = None
                self.current_level = 1
                self.mastery_level = 1
                self.top_weaknesses = []
                self.accuracy_rate = 0.0
        
        try:
            mock_profile = MockProfile()
            
            # Test RAG generation
            trivia = generate_trivia_with_rag(
                "Baybayin ancient Filipino script writing system", 
                user_profile=mock_profile,
                provider="deepseek",
                recent_types=None
            )
            
            logger.info(f"RAG debug result: {trivia}")
            
            return Response({
                'status': 'success',
                'rag_trivia': trivia,
                'validation': {
                    'has_question': bool(trivia.get('question')),
                    'has_options': bool(trivia.get('options')),
                    'has_answer': bool(trivia.get('answer')),
                    'options_count': len(trivia.get('options', [])),
                    'answer_in_options': trivia.get('answer') in trivia.get('options', [])
                }
            })
            
        except Exception as e:
            logger.error(f"RAG debug error: {e}")
            return Response({
                'status': 'error',
                'error': str(e),
                'message': 'RAG generation failed'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SessionTestView(APIView):
    """
    Test endpoint to verify session persistence across requests
    """
    permission_classes = []
    
    def get(self, request):
        """Set a test value in session"""
        if not request.session.session_key:
            request.session.create()
            logger.info(f"Created session: {request.session.session_key}")
        
        test_value = f"test_data_{time.time()}"
        request.session['test_data'] = test_value
        request.session.save()
        
        logger.info(f"GET - Session {request.session.session_key}: Set test_data = {test_value}")
        
        return Response({
            'action': 'set',
            'session_key': request.session.session_key,
            'test_data': test_value,
            'headers': dict(request.headers),
            'cookies': dict(request.COOKIES)
        })
    
    def post(self, request):
        """Read the test value from session"""
        logger.info(f"POST - Session key: {request.session.session_key}")
        logger.info(f"POST - Session keys: {list(request.session.keys())}")
        logger.info(f"POST - Cookies: {dict(request.COOKIES)}")
        
        test_data = request.session.get('test_data', 'NOT_FOUND')
        
        return Response({
            'action': 'get',
            'session_key': request.session.session_key,
            'test_data': test_data,
            'session_keys': list(request.session.keys()),
            'headers': dict(request.headers),
            'cookies': dict(request.COOKIES)
        })