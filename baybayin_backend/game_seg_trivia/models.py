from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from game_seg_trivia.game_config import LEVELS
import uuid
import json

class UserTriviaProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_answered = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    total_incorrect = models.IntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)
    
    # Adaptive learning fields
    weaknesses = models.JSONField(default=dict, help_text="Dictionary of topics with error counts")
    top_weaknesses = models.JSONField(default=list, help_text="Top 3 weak areas")
    
    # Learning progress tracking
    mastery_level = models.IntegerField(default=1, help_text="User's Baybayin mastery level (1-10)")
    
    # Level progression
    current_level = models.IntegerField(default=1)
    current_xp = models.IntegerField(default=0)
    moves_remaining = models.IntegerField(default=0)
    consecutive_correct = models.IntegerField(default=0)
    
    # Session tracking
    session_start = models.DateTimeField(auto_now_add=True)
    session_moves = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Trivia Profile"
    
    @property
    def accuracy_rate(self):
        if self.total_answered == 0:
            return 0
        return round((self.total_correct / self.total_answered) * 100, 1)
    
    def initialize_level(self):
        """Reset level parameters when starting a new level"""
        level_config = LEVELS.get(self.current_level, LEVELS[10])
        self.moves_remaining = level_config["max_moves"]
        self.current_xp = 0
        self.consecutive_correct = 0
        self.session_moves = 0
        self.save()
        
    def complete_level(self):
        """Handle level completion"""
        self.current_level = min(self.current_level + 1, 10)
        self.initialize_level()
        
    def fail_level(self):
        """Handle level failure"""
        self.initialize_level()
        
    @property
    def level_progress(self):
        """Calculate progress percentage for current level"""
        target = LEVELS.get(self.current_level, {}).get("target_xp", 1)
        return min(100, int((self.current_xp / target) * 100))
    
    @property
    def level_config(self):
        return LEVELS.get(self.current_level, LEVELS[10])
    
class TriviaQuestion(models.Model):
    """
    Represents a single trivia question in the question bank.
    Separated from user gameplay history for reusability.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    # Core question fields
    question = models.TextField(help_text="The trivia question text")
    correct_answer = models.CharField(max_length=500, help_text="The correct answer")
    options = models.JSONField(help_text="List of answer options")
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )

    # Metadata
    source = models.TextField(blank=True, help_text="Source reference")
    tags = models.JSONField(default=list, blank=True, help_text="Question tags/categories")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata")
    
    # Tracking
    times_used = models.IntegerField(default=0, help_text="How many times this question was used")
    times_correct = models.IntegerField(default=0, help_text="How many times answered correctly")
    times_incorrect = models.IntegerField(default=0, help_text="How many times answered incorrectly")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Link to archive if generated from TriviaArchive
    archive_source = models.ForeignKey(
        'TriviaArchive',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions'
    )
    
    # Link to CodexArticle for "Learn More" functionality
    source_article = models.ForeignKey(
        'baybayin_codex.CodexArticle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trivia_questions',
        help_text="Link to the originating Codex article for 'Learn More' feature"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['difficulty']),
            models.Index(fields=['created_at']),
            models.Index(fields=['times_used']),
            models.Index(fields=['source_article']),
        ]
    
    def __str__(self):
        return f"{self.question[:50]}... ({self.difficulty})"
    
    @property
    def success_rate(self):
        """Calculate the success rate for this question"""
        if self.times_used == 0:
            return 0.0
        return round((self.times_correct / self.times_used) * 100, 2)
    
    def record_usage(self, was_correct: bool):
        """Record that this question was used and whether it was answered correctly"""
        self.times_used += 1
        if was_correct:
            self.times_correct += 1
        else:
            self.times_incorrect += 1
        self.save(update_fields=['times_used', 'times_correct', 'times_incorrect'])

    QUESTION_TYPE_CHOICES = [
        ('basic_fact', 'Basic Fact'),
        ('historical_context', 'Historical Context'),
        ('linguistic_analysis', 'Linguistic Analysis'),
        ('comparative_analysis', 'Comparative Analysis'),
    ]
    question_type = models.CharField(
        max_length=50, 
        choices=QUESTION_TYPE_CHOICES, 
        default='basic_fact',
        help_text="Category of question for adaptive learning"
    )
    
    source_facts = models.JSONField(
        default=list,
        blank=True,
        help_text="IDs of TriviaSourceFact records used to generate this question"
    )

class TriviaQuestionHistory(models.Model):
    """
    Tracks individual question attempts by users during gameplay.
    This links to TriviaQuestion for the question bank.
    """

    question = models.ForeignKey(
        TriviaQuestion,
        on_delete=models.CASCADE,
        related_name='history',
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trivia_history'
    )

    user_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField()
    time_taken = models.IntegerField(
        help_text="Time taken to answer in seconds",
        validators=[MinValueValidator(0)],
        default=0
    )

    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Game session identifier"
    )

    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-answered_at']
        verbose_name_plural = "Trivia question histories"
        indexes = [
            models.Index(fields=['user', 'answered_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['is_correct']),
        ]

    def __str__(self):
        status = "Yes" if self.is_correct else "No"
        return f"{status} {self.user.username} - {self.question.question[:30]}..."

class TriviaArchive(models.Model):
    """
    Represents a source of trivia content (book, article, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=[
        ('book', 'Book'),
        ('article', 'Article'),
        ('codex', 'Codex'),
        ('manual', 'Manual Entry'),
    ], default='book')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    debug_file_path = models.TextField(blank=True, null=True, help_text="Path to debug file for OCR verification")
    
    def __str__(self):
        return f"{self.title} ({self.source_type})"
    
    class Meta:
        ordering = ['-created_at']


class TriviaSourceFact(models.Model):
    """
    Individual chunks of content with embeddings for RAG retrieval
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField(help_text="The actual text content of this chunk")
    embedding = models.JSONField(
        help_text="Vector embedding of the content (list of floats)"
    )
    token_count = models.IntegerField(help_text="Approximate number of tokens in content")
    source_archive = models.ForeignKey(TriviaArchive, on_delete=models.CASCADE, related_name='facts')
    metadata = models.JSONField(default=dict, help_text="Additional metadata like page number, chapter, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Fact from {self.source_archive.title} ({self.token_count} tokens)"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_archive']),
            models.Index(fields=['token_count']),
        ]