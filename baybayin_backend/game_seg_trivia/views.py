# baybayin_backend/game_seg_trivia/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import time
from .content_retrieval import get_adaptive_fact, get_random_fact
from .trivia_generator import generate_trivia_from_fact, generate_trivia_with_rag, analyze_question_difficulty, calculate_points
from .adaptive_initializer import get_user_profile, update_user_profile, update_mastery_level
from .models import UserTriviaProfile, TriviaQuestionHistory
from django.contrib.auth.models import User
from .game_config import LEVELS
import random

class TriviaQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get a new trivia question for the user with game state
        """
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
            'game_state': game_state
        })


class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Submit an answer to the current trivia question
        """
        user = request.user
        profile = get_user_profile(user)
        data = request.data
        user_answer = data.get('user_answer', '').strip()
        
        # Retrieve current trivia from session
        current_trivia_session = request.session.get('current_trivia')
        if not current_trivia_session:
            return Response({"error": "No active trivia question. Start a new one first."}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        trivia = current_trivia_session['trivia']
        start_time = current_trivia_session['start_time']
        source_fact = current_trivia_session.get('source_fact')
        question_type = current_trivia_session.get('question_type', 'basic_fact')
        
        # Calculate time taken
        answer_time = time.time() - start_time
        
        # Validate answer
        correct_answer = trivia.get('answer', '')
        is_correct = (user_answer.lower() == correct_answer.lower())
        
        # Calculate points
        points = calculate_points(
            user_profile=profile,
            trivia=trivia,
            is_correct=is_correct,
            answer_time=answer_time,
            source_fact=source_fact
        )
        
        # Update user profile
        update_user_profile(
            user=user,
            question=trivia,
            user_answer=user_answer,
            correct_answer=correct_answer,
            source_fact=source_fact,
            question_type=question_type
        )
        
        # Update moves and XP
        profile.current_xp += points
        if is_correct:
            profile.consecutive_correct += 1
        else:
            profile.consecutive_correct = 0
            
        profile.moves_remaining -= 1
        profile.save()
        
        # Update mastery level
        update_mastery_level(profile)
        
        # Check level completion/failure
        level_completed = False
        level_failed = False
        
        if profile.current_xp >= profile.level_config['target_xp']:
            profile.complete_level()
            level_completed = True
        elif profile.moves_remaining <= 0:
            profile.fail_level()
            level_failed = True
            
        profile.save()
        
        # Prepare response
        response_data = {
            "result": "correct" if is_correct else "incorrect",
            "correct_answer": correct_answer,
            "points": points,
            "game_state": {
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
        }
        
        # Clear current trivia from session
        if 'current_trivia' in request.session:
            del request.session['current_trivia']
        
        return Response(response_data)


class GameStateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current game state without a new question"""
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


class ResetLevelView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Reset current level progress"""
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