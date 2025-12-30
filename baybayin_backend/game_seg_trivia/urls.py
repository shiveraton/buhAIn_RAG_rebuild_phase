# baybayin_backend/game_seg_trivia/urls.py
from django.urls import path
from .views import (
    TriviaTestView, TriviaQuestionView, SubmitAnswerView, GameStateView, ResetLevelView, 
    TriviaDebugView, SessionTestView, AdaptiveTriviaQuestionView, AdaptiveTriviaAnswerView
)
from .admin_views import GenerateQuizView, QuizTaskStatusView, SourceFactsListView

urlpatterns = [
    # Game endpoints
    path('test/', TriviaTestView.as_view(), name='trivia-test'),
    path('debug/', TriviaDebugView.as_view(), name='trivia-debug'),
    path('session-test/', SessionTestView.as_view(), name='session-test'),
    path('question/', TriviaQuestionView.as_view(), name='trivia-question'),
    path('submit-answer/', SubmitAnswerView.as_view(), name='trivia-submit-answer'),
    path('game-state/', GameStateView.as_view(), name='trivia-game-state'),
    path('reset-level/', ResetLevelView.as_view(), name='trivia-reset-level'),
    
    # 🤖 AI-DRIVEN ADAPTIVE TRIVIA (100% Automated)
    path('ai/question/', AdaptiveTriviaQuestionView.as_view(), name='ai-trivia-question'),
    path('ai/submit/', AdaptiveTriviaAnswerView.as_view(), name='ai-trivia-submit'),
    
    # Admin endpoints (UC 21 - Quiz Generation)
    path('admin/generate-quiz/', GenerateQuizView.as_view(), name='admin-generate-quiz'),
    path('admin/task-status/<str:task_id>/', QuizTaskStatusView.as_view(), name='admin-task-status'),
    path('admin/source-facts/', SourceFactsListView.as_view(), name='admin-source-facts'),
]
