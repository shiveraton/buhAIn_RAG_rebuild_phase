# baybayin_backend/game_seg_trivia/urls.py
from django.urls import path
from .views import TriviaTestView, TriviaQuestionView, SubmitAnswerView, GameStateView, ResetLevelView, TriviaDebugView, SessionTestView

urlpatterns = [
    path('test/', TriviaTestView.as_view(), name='trivia-test'),
    path('debug/', TriviaDebugView.as_view(), name='trivia-debug'),
    path('session-test/', SessionTestView.as_view(), name='session-test'),
    path('question/', TriviaQuestionView.as_view(), name='trivia-question'),
    path('submit-answer/', SubmitAnswerView.as_view(), name='trivia-submit-answer'),
    path('game-state/', GameStateView.as_view(), name='trivia-game-state'),
    path('reset-level/', ResetLevelView.as_view(), name='trivia-reset-level'),
]
