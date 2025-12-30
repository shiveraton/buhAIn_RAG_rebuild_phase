# baybayin_backend/game_seg_trivia/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
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
from .ai_content_analyzer import AIContentAnalyzer
from .adaptive_question_selector import AdaptiveQuestionSelector
from .models import UserSkillProfile, TriviaQuestionAnswered

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

def get_fallback_question_from_pdf(recent_questions=None, user_profile=None):
    """
    Generate a fallback question directly from PDF-sourced facts.
    This ensures all questions come from the actual PDF content, not hardcoded data.
    
    Args:
        recent_questions: List of question hashes to avoid
        user_profile: Optional user profile for adaptive selection
        
    Returns:
        dict: Question data with question, options, and answer
    """
    from baybayin_codex_pdf.models import PDFCodexEntry
    
    recent_questions = recent_questions or []
    max_attempts = 10  # Try up to 10 different facts
    
    for attempt in range(max_attempts):
        try:
            # Get a random fact from PDF content, avoiding recent ones
            if user_profile:
                fact = get_adaptive_fact(user_profile, use_pdf=True)
            else:
                # Get random PDF fact
                pdf_entries = PDFCodexEntry.objects.all()
                if not pdf_entries.exists():
                    logger.error("No PDF entries found in database!")
                    raise Exception("No PDF content available")
                
                fact = random.choice(list(pdf_entries.order_by('?')[:20]))
            
            if not fact:
                continue
            
            # Check if this fact was recently used
            fact_text = getattr(fact, 'text', '')
            fact_hash = hash(fact_text[:50])
            
            if fact_hash in recent_questions:
                logger.info(f"Skipping recently used fact (attempt {attempt + 1})")
                continue
            
            # Generate question from fact using the existing generator
            trivia = generate_trivia_from_fact(fact)
            
            if trivia and trivia.get('question') and trivia.get('options'):
                logger.info(f"Generated fallback from PDF fact: {trivia['question'][:50]}...")
                trivia['source_fact'] = getattr(fact, 'id', None)
                return trivia
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            continue
    
    # If all attempts failed, use the most basic fact-based approach
    logger.error("All PDF fallback attempts failed, using simple fact display")
    try:
        pdf_entries = PDFCodexEntry.objects.all()
        if pdf_entries.exists():
            fact = random.choice(list(pdf_entries.order_by('?')[:5]))
            return generate_trivia_from_fact(fact)
    except Exception as e:
        logger.error(f"Final fallback also failed: {e}")
    
    # Absolute last resort: return None to signal total failure
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
                # Generate fallback from PDF content instead of hardcoded questions
                trivia = get_fallback_question_from_pdf(recent_questions)
                if not trivia:
                    logger.error("PDF fallback failed, cannot generate question")
                    return Response({
                        'error': 'Unable to generate trivia question',
                        'message': 'Please try again later'
                    }, status=500)
                logger.info(f"Using PDF fallback question: {trivia['question'][:50]}...")

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
        
        # Get recent questions to avoid repetition
        recent_question_history = TriviaQuestionHistory.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        recent_questions = [hash(q.question.question[:50]) for q in recent_question_history if q.question]
        
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
            logger.error(f"Trivia generation failed for authenticated user: {e}")
            # Try fact-based fallback first
            try:
                fact = get_adaptive_fact(profile) or get_random_fact()
                if fact:
                    trivia = generate_trivia_from_fact(fact)
                    trivia['source_fact'] = fact.id if fact else None
                else:
                    raise Exception("No facts available")
            except Exception as inner_e:
                # Final fallback: generate from PDF content
                logger.error(f"Fact-based fallback also failed: {inner_e}, using PDF fallback")
                trivia = get_fallback_question_from_pdf(recent_questions, user_profile=profile)
                if not trivia:
                    logger.error("All fallback methods failed")
                    return Response({
                        'error': 'Unable to generate trivia question',
                        'message': 'Please try again later'
                    }, status=500)
                trivia['source_fact'] = trivia.get('source_fact', None)
        
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

@method_decorator(csrf_exempt, name='dispatch')
class AdaptiveTriviaQuestionView(APIView):
    """
    100% AI-DRIVEN trivia system
    - AI analyzes PDF content for difficulty
    - AI selects optimal question for each user
    - AI updates user skill based on performance
    NO hardcoded rules or levels
    """
    permission_classes = []  # Allow both authenticated and guest users

    def get(self, request):
        """
        AI automatically selects the best next question for this specific user
        """
        logger.info(f"🤖 AI Trivia request from user: {request.user if request.user.is_authenticated else 'Guest'}")
        
        try:
            # Handle both authenticated and guest users
            if request.user.is_authenticated:
                # Get or create user skill profile
                skill_profile, created = UserSkillProfile.objects.get_or_create(
                    user=request.user
                )
                
                if created:
                    logger.info(f"Created new skill profile for user {request.user.username}")
            else:
                # For guests, create a temporary profile based on session
                skill_profile = self._get_guest_skill_profile(request)
            
            # AI selects the BEST next question for this user
            selected_content = AdaptiveQuestionSelector.select_next_question(skill_profile)
            
            if not selected_content:
                return Response({
                    'error': 'No suitable content available',
                    'message': 'AI is analyzing content. Please try again in a moment.',
                    'suggestion': 'Run: python manage.py analyze_content'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Generate question from selected content
            try:
                question_data = self._generate_question_from_content(selected_content)
            except Exception as e:
                logger.error(f"Question generation failed: {e}")
                return Response({
                    'error': 'Question generation failed',
                    'message': 'Unable to create question from content'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Store question start time
            question_start_time = time.time()
            
            # Store session data for answer validation
            session_data = {
                'content_id': selected_content.id,
                'correct_answer': question_data['correct_answer'],
                'question_difficulty': selected_content.calibrated_difficulty,
                'start_time': question_start_time,
                'user_skill_before': skill_profile.overall_skill,
                'ai_category': selected_content.ai_category
            }
            
            if request.user.is_authenticated:
                request.session['adaptive_trivia'] = session_data
            else:
                request.session['guest_adaptive_trivia'] = session_data
            
            request.session.save()
            
            # Prepare response with AI insights
            response_data = {
                'question': question_data['question'],
                'choices': question_data['choices'],
                'content_id': selected_content.id,  # For tracking
                
                # AI-generated insights (educational value)
                'ai_insights': {
                    'your_skill_level': f"{skill_profile.overall_skill:.0f}",
                    'skill_description': skill_profile.get_skill_level_description(),
                    'question_difficulty': f"{selected_content.calibrated_difficulty:.2f}",
                    'difficulty_description': self._get_difficulty_description(selected_content.calibrated_difficulty),
                    'predicted_success_rate': f"{skill_profile.predict_success_probability(selected_content.calibrated_difficulty) * 100:.0f}%",
                    'topic_category': selected_content.ai_category.replace('_', ' ').title() if selected_content.ai_category else 'General',
                    'estimated_study_time': f"{selected_content.ai_estimated_minutes or 5} min",
                    'cognitive_level': selected_content.ai_cognitive_level or 'comprehension',
                    'total_questions_answered': skill_profile.total_questions,
                    'accuracy_rate': f"{skill_profile.accuracy * 100:.1f}%" if skill_profile.total_questions > 0 else "N/A"
                },
                
                # Learning progress
                'progress': {
                    'questions_answered': skill_profile.total_questions,
                    'correct_answers': skill_profile.total_correct,
                    'skill_level': skill_profile.overall_skill,
                    'optimal_difficulty': skill_profile.get_recommended_difficulty(),
                    'learning_rate': skill_profile.learning_rate
                }
            }
            
            # Add learning insights for experienced users
            if skill_profile.total_questions >= 10:
                insights = AdaptiveQuestionSelector.get_learning_insights(skill_profile)
                response_data['learning_insights'] = insights
            
            logger.info(f"✅ AI selected question: difficulty={selected_content.calibrated_difficulty:.2f}, "
                       f"category={selected_content.ai_category}, "
                       f"user_skill={skill_profile.overall_skill:.0f}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"AI trivia generation error: {e}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'error': 'AI system error',
                'message': 'Unable to generate question',
                'details': str(e) if settings.DEBUG else 'Internal error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_guest_skill_profile(self, request):
        """Create temporary skill profile for guest users based on session"""
        
        # Get session-based skill data
        session_skill = request.session.get('guest_skill_profile', {
            'overall_skill': 1000.0,
            'category_skills': {},
            'total_questions': 0,
            'total_correct': 0,
            'recent_performance': [],
            'optimal_difficulty_range': {"min": 0.3, "max": 0.6}
        })
        
        # Create temporary profile object (not saved to DB)
        class TempSkillProfile:
            def __init__(self, data):
                self.user = None
                self.overall_skill = data['overall_skill']
                self.category_skills = data['category_skills']
                self.total_questions = data['total_questions']
                self.total_correct = data['total_correct']
                self.recent_performance = data['recent_performance']
                self.optimal_difficulty_range = data['optimal_difficulty_range']
                self.learning_rate = 1.0
                self.skill_uncertainty = 350.0
            
            @property
            def accuracy(self):
                if self.total_questions == 0:
                    return 0.0
                return self.total_correct / self.total_questions
            
            def get_recommended_difficulty(self):
                return (self.optimal_difficulty_range['min'] + self.optimal_difficulty_range['max']) / 2
            
            def get_skill_level_description(self):
                if self.overall_skill < 800:
                    return "Novice Learner"
                elif self.overall_skill < 950:
                    return "Developing Understanding"
                elif self.overall_skill < 1100:
                    return "Competent Practitioner"
                elif self.overall_skill < 1300:
                    return "Advanced Scholar"
                else:
                    return "Expert Practitioner"
            
            def predict_success_probability(self, difficulty):
                return 1 / (1 + 10 ** ((difficulty * 1000 - self.overall_skill) / 400))
            
            def get_category_skill(self, category):
                return self.category_skills.get(category, self.overall_skill * 0.9)
        
        return TempSkillProfile(session_skill)
    
    def _generate_question_from_content(self, content):
        """Generate question from PDF content using existing RAG system"""
        
        # Use the existing trivia generator
        try:
            trivia = generate_trivia_from_fact(content)
            
            if not trivia or not trivia.get('question') or not trivia.get('options'):
                raise Exception("Invalid trivia generated")
            
            # Shuffle options for variety
            options = trivia['options'].copy()
            correct_answer = trivia['answer']
            random.shuffle(options)
            
            return {
                'question': trivia['question'],
                'choices': options,
                'correct_answer': correct_answer
            }
            
        except Exception as e:
            logger.error(f"RAG generation failed, using simple fallback: {e}")
            
            # Simple fallback question
            content_snippet = (content.cleaned_text or content.text)[:150]
            
            return {
                'question': f'What is the following text about?\n\n"{content_snippet}..."',
                'choices': ['Baybayin Script', 'Modern Filipino', 'Spanish Colonial', 'English Language'],
                'correct_answer': 'Baybayin Script'
            }
    
    def _get_difficulty_description(self, difficulty):
        """Convert difficulty score to human-readable description"""
        if difficulty < 0.2:
            return "Very Easy"
        elif difficulty < 0.4:
            return "Easy"
        elif difficulty < 0.6:
            return "Medium"
        elif difficulty < 0.8:
            return "Hard"
        else:
            return "Very Hard"


@method_decorator(csrf_exempt, name='dispatch')
class AdaptiveTriviaAnswerView(APIView):
    """
    AI automatically updates user skill based on performance
    NO manual scoring - everything calculated by AI
    """
    permission_classes = []

    def post(self, request):
        """
        Submit answer and let AI update user skill automatically
        """
        
        try:
            selected_answer = request.data.get('selected_answer')
            content_id = request.data.get('content_id')
            
            if not selected_answer:
                return Response({
                    'error': 'Missing answer',
                    'message': 'Please provide selected_answer'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get session data
            if request.user.is_authenticated:
                session_data = request.session.get('adaptive_trivia')
                skill_profile = UserSkillProfile.objects.get(user=request.user)
            else:
                session_data = request.session.get('guest_adaptive_trivia')
                skill_profile = self._get_guest_skill_profile(request)
            
            if not session_data:
                return Response({
                    'error': 'Session expired',
                    'message': 'Please get a new question'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate answer
            correct_answer = session_data['correct_answer']
            is_correct = selected_answer.strip() == correct_answer.strip()
            
            # Calculate response time
            response_time = time.time() - session_data['start_time']
            
            # Get content
            from baybayin_codex_pdf.models import PDFCodexEntry
            content = PDFCodexEntry.objects.get(id=session_data['content_id'])
            
            # AI updates skill automatically
            if request.user.is_authenticated:
                skill_change = skill_profile.update_skill(
                    question_difficulty=session_data['question_difficulty'],
                    answered_correctly=is_correct,
                    response_time=response_time
                )
                
                # Update category skill
                if session_data.get('ai_category'):
                    skill_profile.update_category_skill(
                        session_data['ai_category'],
                        skill_change
                    )
                
                # Record detailed answer
                TriviaQuestionAnswered.objects.create(
                    user=request.user,
                    source_fact=content,
                    selected_answer=selected_answer,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    response_time_seconds=response_time,
                    question_difficulty=session_data['question_difficulty'],
                    user_skill_at_time=session_data['user_skill_before'],
                    skill_change=skill_change
                )
                
            else:
                # Update guest session profile
                skill_change = self._update_guest_skill(
                    request, 
                    session_data['question_difficulty'],
                    is_correct,
                    response_time
                )
            
            # Update content statistics
            content.times_asked += 1
            if is_correct:
                content.times_answered_correctly += 1
            
            # Update average response time
            if content.average_response_time:
                content.average_response_time = (content.average_response_time + response_time) / 2
            else:
                content.average_response_time = response_time
            
            content.save()
            
            # Generate AI feedback
            feedback_message = AdaptiveQuestionSelector.generate_feedback_message(
                is_correct=is_correct,
                skill_change=skill_change,
                user_profile=skill_profile,
                question_difficulty=session_data['question_difficulty']
            )
            
            # Prepare response
            response_data = {
                'is_correct': is_correct,
                'correct_answer': correct_answer,
                'explanation': (content.cleaned_text or content.text)[:300] + '...',
                
                # AI-generated feedback
                'ai_feedback': {
                    'message': feedback_message,
                    'skill_change': f"{skill_change:+.1f}",
                    'new_skill_level': skill_profile.overall_skill,
                    'skill_description': skill_profile.get_skill_level_description(),
                    'response_time': f"{response_time:.1f}s",
                    'difficulty_rating': f"{session_data['question_difficulty'] * 100:.0f}%",
                    'success_rate_on_similar': f"{skill_profile.predict_success_probability(session_data['question_difficulty']) * 100:.0f}%",
                    'total_questions': skill_profile.total_questions if hasattr(skill_profile, 'total_questions') else 0,
                    'accuracy': f"{skill_profile.accuracy * 100:.1f}%" if hasattr(skill_profile, 'accuracy') else "N/A"
                },
                
                # Learning insights
                'learning_progress': {
                    'questions_answered': skill_profile.total_questions if hasattr(skill_profile, 'total_questions') else 0,
                    'skill_level': skill_profile.overall_skill,
                    'recommended_difficulty': skill_profile.get_recommended_difficulty(),
                }
            }
            
            # Clear session data
            if request.user.is_authenticated:
                request.session.pop('adaptive_trivia', None)
            else:
                request.session.pop('guest_adaptive_trivia', None)
            
            request.session.save()
            
            logger.info(f"✅ Answer processed: correct={is_correct}, "
                       f"skill_change={skill_change:+.1f}, "
                       f"new_skill={skill_profile.overall_skill:.0f}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Answer processing error: {e}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'error': 'Answer processing failed',
                'message': str(e) if settings.DEBUG else 'Internal error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_guest_skill_profile(self, request):
        """Get guest skill profile from session (same as in question view)"""
        session_skill = request.session.get('guest_skill_profile', {
            'overall_skill': 1000.0,
            'category_skills': {},
            'total_questions': 0,
            'total_correct': 0,
            'recent_performance': [],
            'optimal_difficulty_range': {"min": 0.3, "max": 0.6}
        })
        
        class TempSkillProfile:
            def __init__(self, data):
                self.user = None
                self.overall_skill = data['overall_skill']
                self.category_skills = data['category_skills']
                self.total_questions = data['total_questions']
                self.total_correct = data['total_correct']
                self.recent_performance = data['recent_performance']
                self.optimal_difficulty_range = data['optimal_difficulty_range']
                self.learning_rate = 1.0
                self.skill_uncertainty = 350.0
            
            @property
            def accuracy(self):
                if self.total_questions == 0:
                    return 0.0
                return self.total_correct / self.total_questions
            
            def get_recommended_difficulty(self):
                return (self.optimal_difficulty_range['min'] + self.optimal_difficulty_range['max']) / 2
            
            def get_skill_level_description(self):
                if self.overall_skill < 800:
                    return "Novice Learner"
                elif self.overall_skill < 950:
                    return "Developing Understanding"
                elif self.overall_skill < 1100:
                    return "Competent Practitioner"
                elif self.overall_skill < 1300:
                    return "Advanced Scholar"
                else:
                    return "Expert Practitioner"
            
            def predict_success_probability(self, difficulty):
                return 1 / (1 + 10 ** ((difficulty * 1000 - self.overall_skill) / 400))
            
            def get_category_skill(self, category):
                return self.category_skills.get(category, self.overall_skill * 0.9)
        
        return TempSkillProfile(session_skill)
    
    def _update_guest_skill(self, request, question_difficulty, is_correct, response_time):
        """Update guest skill profile in session"""
        
        session_skill = request.session.get('guest_skill_profile', {
            'overall_skill': 1000.0,
            'category_skills': {},
            'total_questions': 0,
            'total_correct': 0,
            'recent_performance': [],
            'optimal_difficulty_range': {"min": 0.3, "max": 0.6}
        })
        
        # Simple skill update for guests (similar to Elo)
        expected_score = 1 / (1 + 10 ** ((question_difficulty * 1000 - session_skill['overall_skill']) / 400))
        actual_score = 1.0 if is_correct else 0.0
        
        k_factor = 32 * (1 / (1 + session_skill['total_questions'] / 100))
        skill_change = k_factor * (actual_score - expected_score)
        
        # Update skill
        session_skill['overall_skill'] += skill_change
        session_skill['overall_skill'] = max(400, min(2000, session_skill['overall_skill']))
        
        # Update counters
        session_skill['total_questions'] += 1
        if is_correct:
            session_skill['total_correct'] += 1
        
        # Update recent performance
        session_skill['recent_performance'].append({
            'difficulty': question_difficulty,
            'correct': is_correct,
            'response_time': response_time,
            'timestamp': timezone.now().isoformat()
        })
        session_skill['recent_performance'] = session_skill['recent_performance'][-50:]
        
        # Update difficulty range based on recent performance
        if len(session_skill['recent_performance']) >= 10:
            recent_10 = session_skill['recent_performance'][-10:]
            recent_accuracy = sum(1 for r in recent_10 if r['correct']) / 10
            
            if recent_accuracy > 0.8:
                session_skill['optimal_difficulty_range']['min'] += 0.05
                session_skill['optimal_difficulty_range']['max'] += 0.05
            elif recent_accuracy < 0.5:
                session_skill['optimal_difficulty_range']['min'] = max(0.1, session_skill['optimal_difficulty_range']['min'] - 0.05)
                session_skill['optimal_difficulty_range']['max'] = max(0.3, session_skill['optimal_difficulty_range']['max'] - 0.05)
        
        # Save back to session
        request.session['guest_skill_profile'] = session_skill
        request.session.save()
        
        return skill_change