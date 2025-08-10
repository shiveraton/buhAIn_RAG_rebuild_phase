from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
import json

class WikiCategory(models.Model):
    """
    Categories for organizing wiki articles
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#3880ff')
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    article_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Wiki Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class WikiArticle(models.Model):
    """
    Main wiki articles containing Baybayin information
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(WikiCategory, on_delete=models.CASCADE, related_name='articles')
    
    # Content fields
    summary = models.TextField(max_length=500, help_text="Brief summary for article previews")
    content = models.TextField(help_text="Main article content (supports HTML)")
    
    # Source tracking
    source = models.CharField(max_length=100, default='manual')
    source_url = models.URLField(blank=True)
    url = models.URLField(blank=True)
    
    # Media fields
    featured_image = models.CharField(max_length=200, blank=True)
    gallery_images = models.JSONField(default=list, blank=True)
    
    # Interactive elements
    baybayin_examples = models.JSONField(default=list, blank=True)
    interactive_elements = models.JSONField(default=dict, blank=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    reading_time = models.IntegerField(default=0)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    # Publishing
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    keywords = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class WikiTimeline(models.Model):
    """
    Historical timeline events for Baybayin history
    """
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    period = models.CharField(max_length=100, blank=True)
    date = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    image = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(blank=True)
    
    # Additional fields for scraper
    importance_level = models.CharField(max_length=20, default='medium')
    related_articles = models.JSONField(default=list, blank=True)
    sources = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    importance = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['year']

    def __str__(self):
        return f"{self.year}: {self.title}"

class WikiGlossary(models.Model):
    """
    Glossary of Baybayin and Filipino terms
    """
    term = models.CharField(max_length=100, unique=True)
    definition = models.TextField()
    baybayin_script = models.CharField(max_length=100, blank=True)
    pronunciation = models.CharField(max_length=100, blank=True)
    etymology = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )
    
    # Source tracking
    source = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    usage_examples = models.JSONField(default=list, blank=True)
    related_terms = models.JSONField(default=list, blank=True)
    examples = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['term']
        verbose_name_plural = 'Wiki Glossary'

    def __str__(self):
        return self.term

class WikiQuiz(models.Model):
    """
    Quiz questions related to wiki content
    """
    article = models.ForeignKey(WikiArticle, on_delete=models.CASCADE, related_name='quizzes')
    question = models.TextField()
    options = models.JSONField(help_text="Array of answer options")
    correct_answer = models.IntegerField(help_text="Index of correct answer")
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['article', 'created_at']

    def __str__(self):
        return f"Quiz for {self.article.title}"
    
class WikiBookmark(models.Model):
    """
    User bookmarks for articles
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(WikiArticle, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'article']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.article.title}"
    
class WikiReadingProgress(models.Model):
    """
    Track user reading progress
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(WikiArticle, on_delete=models.CASCADE)
    progress_percentage = models.IntegerField(default=0)
    last_read_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'article']

    def __str__(self):
        return f"{self.user.username} - {self.article.title}: {self.progress_percentage}%"

class UserRepository(models.Model):
    """
    User document repositories for uploaded content
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    repository_path = models.CharField(max_length=500)
    total_files = models.IntegerField(default=0)
    total_size = models.BigIntegerField(default=0)  # Size in bytes
    processed_documents = models.IntegerField(default=0)
    extracted_articles = models.IntegerField(default=0)
    extracted_terms = models.IntegerField(default=0)
    extracted_events = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('deleted', 'Deleted'),
        ],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Repository for {self.user.username}"

class UserDocument(models.Model):
    """
    Individual documents uploaded by users
    """
    repository = models.ForeignKey(UserRepository, on_delete=models.CASCADE, related_name='documents')
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=10)
    content_hash = models.CharField(max_length=64)  # SHA-256 hash
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    processing_error = models.TextField(blank=True)
    
    # Analysis results metadata
    analysis_confidence = models.FloatField(default=0.0)
    baybayin_relevance = models.FloatField(default=0.0)
    content_quality = models.FloatField(default=0.0)
    extracted_text_length = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    upload_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} - {self.repository.user.username}"

class ExtractedContent(models.Model):
    """
    Content extracted from user documents
    """
    document = models.ForeignKey(UserDocument, on_delete=models.CASCADE, related_name='extracted_content')
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('article', 'Article'),
            ('term', 'Glossary Term'),
            ('event', 'Timeline Event'),
            ('example', 'Baybayin Example'),
        ]
    )
    
    # Content data
    title = models.CharField(max_length=200)
    content = models.TextField()
    extracted_data = models.JSONField(default=dict)
    
    # Quality metrics
    confidence_score = models.FloatField(default=0.0)
    relevance_score = models.FloatField(default=0.0)
    
    # Review status
    is_reviewed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_content')
    review_notes = models.TextField(blank=True)
    
    # Database integration
    is_integrated = models.BooleanField(default=False)
    integrated_object_id = models.IntegerField(null=True, blank=True)
    integrated_object_type = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    integrated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.content_type}: {self.title}"

class ProcessingJob(models.Model):
    """
    Background processing jobs for document analysis
    """
    repository = models.ForeignKey(UserRepository, on_delete=models.CASCADE, related_name='processing_jobs')
    job_type = models.CharField(
        max_length=30,
        choices=[
            ('single_document', 'Single Document'),
            ('repository_batch', 'Repository Batch'),
            ('content_extraction', 'Content Extraction'),
            ('database_integration', 'Database Integration'),
        ]
    )
    
    # Job status
    status = models.CharField(
        max_length=20,
        choices=[
            ('queued', 'Queued'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='queued'
    )
    
    # Progress tracking
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    failed_items = models.IntegerField(default=0)
    progress_percentage = models.FloatField(default=0.0)
    
    # Job configuration
    parameters = models.JSONField(default=dict, blank=True)
    
    # Results and errors
    results = models.JSONField(default=dict, blank=True)
    error_log = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_type} job for {self.repository.user.username} - {self.status}"