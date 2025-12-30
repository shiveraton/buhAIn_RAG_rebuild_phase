from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from game_seg_trivia.game_config import LEVELS
import uuid
import json

def default_difficulty_range():
    """Default difficulty range for user skill profile"""
    return {"min": 0.3, "max": 0.6}

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
    
    # CRITICAL: The Golden Thread - Traceability to source fact (thesis requirement)
    source_fact = models.ForeignKey(
        'TriviaSourceFact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_questions',
        db_index=True,
        help_text="PRIMARY source fact used to generate this question (thesis traceability requirement)"
    )
    
    # Legacy field - for questions using multiple facts (backward compatibility)
    source_facts = models.JSONField(
        default=list,
        blank=True,
        help_text="DEPRECATED: Legacy field for multiple fact IDs. Use source_fact FK instead."
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
    THESIS REQUIREMENT: Embeddings stored as JSON string in SQLite (not FAISS)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField(help_text="The actual text content of this chunk")
    
    # CRITICAL: Embedding stored as JSON string per thesis requirements
    embedding_json = models.TextField(
        help_text="Vector embedding as JSON-serialized array of floats (thesis requirement)",
        db_index=False  # Not indexed as it's for retrieval, not filtering
    )
    
    # Legacy field - keep for backward compatibility during migration
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="DEPRECATED: Use embedding_json instead"
    )
    
    token_count = models.IntegerField(help_text="Approximate number of tokens in content")
    source_archive = models.ForeignKey(TriviaArchive, on_delete=models.CASCADE, related_name='facts')
    metadata = models.JSONField(default=dict, help_text="Additional metadata like page number, chapter, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_embedding(self, embedding_vector):
        """
        Store embedding as JSON string (thesis requirement)
        Args:
            embedding_vector: numpy array or list of floats
        """
        import numpy as np
        if isinstance(embedding_vector, np.ndarray):
            embedding_vector = embedding_vector.tolist()
        self.embedding_json = json.dumps(embedding_vector)
    
    def get_embedding(self):
        """
        Retrieve embedding as numpy array
        Returns:
            numpy array of floats
        """
        import numpy as np
        if self.embedding_json:
            return np.array(json.loads(self.embedding_json))
        elif self.embedding:  # Fallback for legacy data
            return np.array(self.embedding)
        return None
    
    def __str__(self):
        return f"Fact from {self.source_archive.title} ({self.token_count} tokens)"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_archive']),
            models.Index(fields=['token_count']),
        ]


# ===========================
# AI-DRIVEN ADAPTIVE LEARNING MODELS
# ===========================

class UserSkillProfile(models.Model):
    """
    AI-driven adaptive skill tracking (100% automated, no manual levels)
    Uses Elo-like rating system for continuous skill assessment
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='skill_profile'
    )
    
    # Overall skill rating (Elo-like, starts at 1000)
    overall_skill = models.FloatField(
        default=1000.0,
        help_text="Elo-style skill rating (800=novice, 1000=average, 1200+=advanced)"
    )
    
    # Category-specific skills (AI-determined categories)
    category_skills = models.JSONField(
        default=dict,
        help_text="AI-tracked skill per category: {'character_basics': 950, 'vowel_system': 1020, ...}"
    )
    
    # Learning velocity (how fast user improves)
    learning_rate = models.FloatField(
        default=1.0,
        help_text="AI-calculated learning speed multiplier (1.0 = normal, >1 = fast learner)"
    )
    
    # Confidence intervals
    skill_uncertainty = models.FloatField(
        default=350.0,
        help_text="AI's confidence in skill estimate (decreases with more questions answered)"
    )
    
    # Adaptive parameters
    optimal_difficulty_range = models.JSONField(
        default=default_difficulty_range,
        help_text="AI-calculated optimal challenge zone for this user"
    )
    
    # Performance history (for AI pattern detection)
    recent_performance = models.JSONField(
        default=list,
        help_text="Last 50 question results for AI analysis and pattern detection"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_played = models.DateTimeField(auto_now=True)
    total_questions = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "User Skill Profile (AI-Adaptive)"
        verbose_name_plural = "User Skill Profiles (AI-Adaptive)"
    
    def __str__(self):
        return f"{self.user.username} - Skill: {self.overall_skill:.0f} ({self.get_skill_level_description()})"
    
    @property
    def accuracy(self):
        """Overall accuracy rate"""
        if self.total_questions == 0:
            return 0.0
        return self.total_correct / self.total_questions
    
    def update_skill(self, question_difficulty: float, answered_correctly: bool, response_time: float):
        """
        AI automatically adjusts user skill based on performance
        Uses modified Elo rating system with learning rate decay
        
        Args:
            question_difficulty: Difficulty of the question (0-1)
            answered_correctly: Whether user answered correctly
            response_time: Time taken to answer in seconds
        
        Returns:
            float: Skill change amount
        """
        
        # Expected probability of getting it right (Elo formula)
        expected_score = 1 / (1 + 10 ** ((question_difficulty * 1000 - self.overall_skill) / 400))
        
        # Actual score
        actual_score = 1.0 if answered_correctly else 0.0
        
        # K-factor (learning rate) - decreases as user plays more
        # New users have higher K-factor (learn faster), experienced users have lower
        k_factor = 32 * self.learning_rate * (1 / (1 + self.total_questions / 100))
        
        # Calculate skill change
        skill_change = k_factor * (actual_score - expected_score)
        
        # Update overall skill
        self.overall_skill += skill_change
        
        # Clamp skill to reasonable bounds
        self.overall_skill = max(400, min(2000, self.overall_skill))
        
        # Update uncertainty (confidence improves with more data)
        self.skill_uncertainty = max(50, self.skill_uncertainty * 0.99)
        
        # Track performance
        self.recent_performance.append({
            'difficulty': question_difficulty,
            'correct': answered_correctly,
            'response_time': response_time,
            'skill_before': self.overall_skill - skill_change,
            'skill_after': self.overall_skill,
            'expected_score': expected_score,
            'timestamp': timezone.now().isoformat()
        })
        
        # Keep only last 50
        self.recent_performance = self.recent_performance[-50:]
        
        # Update counters
        self.total_questions += 1
        if answered_correctly:
            self.total_correct += 1
        
        self.save()
        
        return skill_change
    
    def get_recommended_difficulty(self) -> float:
        """
        AI calculates optimal difficulty for next question
        Based on 'Zone of Proximal Development' theory
        Adapts based on recent performance patterns
        """
        
        # Analyze recent performance (last 10 questions)
        if len(self.recent_performance) >= 10:
            recent_10 = self.recent_performance[-10:]
            recent_accuracy = sum(1 for r in recent_10 if r['correct']) / 10
            
            # Adjust difficulty zone based on performance
            if recent_accuracy > 0.8:
                # Too easy - increase difficulty
                self.optimal_difficulty_range['min'] += 0.05
                self.optimal_difficulty_range['max'] += 0.05
            elif recent_accuracy < 0.5:
                # Too hard - decrease difficulty
                self.optimal_difficulty_range['min'] = max(0.1, self.optimal_difficulty_range['min'] - 0.05)
                self.optimal_difficulty_range['max'] = max(0.3, self.optimal_difficulty_range['max'] - 0.05)
            
            # Clamp values to valid range
            self.optimal_difficulty_range['min'] = max(0.1, min(0.7, self.optimal_difficulty_range['min']))
            self.optimal_difficulty_range['max'] = max(0.3, min(0.9, self.optimal_difficulty_range['max']))
            
            self.save()
        
        # Return middle of optimal range
        return (self.optimal_difficulty_range['min'] + self.optimal_difficulty_range['max']) / 2
    
    def get_skill_level_description(self) -> str:
        """AI-generated skill description (no hardcoded levels)"""
        
        if self.overall_skill < 800:
            return "Novice Learner"
        elif self.overall_skill < 950:
            return "Developing Understanding"
        elif self.overall_skill < 1100:
            return "Competent Practitioner"
        elif self.overall_skill < 1300:
            return "Advanced Scholar"
        elif self.overall_skill < 1500:
            return "Expert Practitioner"
        else:
            return "Master of Baybayin"
    
    def predict_success_probability(self, question_difficulty: float) -> float:
        """
        AI predicts probability user will answer correctly
        Uses Elo-based expected score calculation
        """
        return 1 / (1 + 10 ** ((question_difficulty * 1000 - self.overall_skill) / 400))
    
    def get_category_skill(self, category: str) -> float:
        """Get skill level for a specific category"""
        return self.category_skills.get(category, self.overall_skill * 0.9)
    
    def update_category_skill(self, category: str, skill_change: float):
        """Update skill for a specific category"""
        if category:
            current_skill = self.get_category_skill(category)
            self.category_skills[category] = current_skill + skill_change
            self.save()


class TriviaQuestionAnswered(models.Model):
    """
    Enhanced to track detailed performance metrics for AI analysis
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='answered_questions'
    )
    question = models.ForeignKey(
        'TriviaQuestion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_answers'
    )
    source_fact = models.ForeignKey(
        'baybayin_codex_pdf.PDFCodexEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="PDF source for this question"
    )
    
    # Answer details
    selected_answer = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField()
    
    # Performance metrics
    response_time_seconds = models.FloatField(
        help_text="Time taken to answer in seconds"
    )
    question_difficulty = models.FloatField(
        null=True,
        blank=True,
        help_text="Difficulty of question at time of answering"
    )
    user_skill_at_time = models.FloatField(
        null=True,
        blank=True,
        help_text="User's skill level when they answered"
    )
    skill_change = models.FloatField(
        null=True,
        blank=True,
        help_text="How much skill changed from this answer"
    )
    
    # Metadata
    answered_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-answered_at']
        indexes = [
            models.Index(fields=['user', 'answered_at']),
            models.Index(fields=['is_correct']),
            models.Index(fields=['source_fact']),
        ]
        verbose_name = "Trivia Question Answered"
        verbose_name_plural = "Trivia Questions Answered"
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.user.username} - Q{self.question_id if self.question else 'N/A'} ({self.answered_at.strftime('%Y-%m-%d %H:%M')})"