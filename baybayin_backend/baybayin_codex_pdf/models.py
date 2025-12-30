from django.db import models

class PDFCodexEntry(models.Model):
    text = models.TextField()
    page_number = models.IntegerField()
    cleaned_text = models.TextField()
    chunk_index = models.IntegerField()
    embedding = models.JSONField()
    source = models.CharField(max_length=100, default="pdf")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # AI-Generated Metadata (100% automated)
    ai_difficulty_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="AI-calculated difficulty (0=easiest, 1=hardest)"
    )
    ai_category = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="AI-determined learning category"
    )
    ai_prerequisites = models.JSONField(
        default=list, 
        blank=True,
        help_text="AI-identified prerequisite concepts"
    )
    ai_cognitive_level = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="AI-determined cognitive complexity"
    )
    ai_estimated_minutes = models.IntegerField(
        null=True, 
        blank=True,
        help_text="AI-estimated study time in minutes"
    )
    ai_analysis_reasoning = models.TextField(
        null=True, 
        blank=True,
        help_text="AI explanation of difficulty rating"
    )
    ai_analyzed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When AI last analyzed this content"
    )
    
    # OCR Sanitization Metadata
    ocr_sanitization_stats = models.JSONField(
        default=dict,
        blank=True,
        help_text="Statistics from OCR text sanitization process"
    )
    ocr_confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="OCR text quality confidence score (0.0-1.0)"
    )
    ocr_config_used = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Tesseract configuration that produced the best result"
    )
    
    # Performance tracking (automated)
    times_asked = models.IntegerField(default=0)
    times_answered_correctly = models.IntegerField(default=0)
    average_response_time = models.FloatField(null=True, blank=True)
    
    @property
    def actual_difficulty(self):
        """Calculate REAL difficulty based on user performance"""
        if self.times_asked == 0:
            return self.ai_difficulty_score or 0.5
        
        # Real difficulty = how many people get it wrong
        return 1.0 - (self.times_answered_correctly / self.times_asked)
    
    @property
    def calibrated_difficulty(self):
        """Blend AI prediction with actual performance"""
        if self.times_asked < 10:
            # Trust AI more when we have little data
            return self.ai_difficulty_score or 0.5
        
        # Blend: 30% AI prediction, 70% actual performance
        ai_score = self.ai_difficulty_score or 0.5
        actual_score = self.actual_difficulty
        return (0.3 * ai_score) + (0.7 * actual_score)
    
    def __str__(self):
        return f"PDF Entry {self.id} - Page {self.page_number} (Difficulty: {self.calibrated_difficulty:.2f})"
