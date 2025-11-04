from rest_framework import serializers
from .models import (
    CodexCategory, CodexArticle, CodexTimeline, CodexGlossary, 
    CodexQuiz, CodexBookmark, CodexReadingProgress
)

class CodexCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CodexCategory
        fields = ['id', 'name', 'description', 'slug', 'icon', 'color', 'order', 'article_count']


class CodexArticleListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    
    class Meta:
        model = CodexArticle
        fields = [
            'id', 'title', 'slug', 'category_name', 'category_color',
            'summary', 'featured_image', 'tags', 'reading_time',
            'difficulty_level', 'is_featured', 'created_at', 'updated_at'
        ]


class CodexArticleDetailSerializer(serializers.ModelSerializer):
    category = CodexCategorySerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    reading_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = CodexArticle
        fields = [
            'id', 'title', 'slug', 'category', 'summary', 'content',
            'featured_image', 'gallery_images', 'baybayin_examples',
            'interactive_elements', 'tags', 'reading_time',
            'difficulty_level', 'is_featured', 'meta_description',
            'keywords', 'created_at', 'updated_at', 'published_at',
            'is_bookmarked', 'reading_progress'
        ]
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CodexBookmark.objects.filter(user=request.user, article=obj).exists()
        return False
    
    def get_reading_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = CodexReadingProgress.objects.get(user=request.user, article=obj)
                return {
                    'percentage': progress.progress_percentage,
                    'completed': progress.completed,
                    'last_read_at': progress.last_read_at
                }
            except CodexReadingProgress.DoesNotExist:
                return None
        return None


class CodexTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodexTimeline
        fields = [
            'id', 'title', 'year', 'period', 'description',
            'image', 'source', 'importance'
        ]


class CodexGlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodexGlossary
        fields = [
            'id', 'term', 'pronunciation', 'definition',
            'baybayin_script', 'related_terms', 'examples', 'category'
        ]


class CodexQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodexQuiz
        fields = [
            'id', 'question', 'options', 'correct_answer',
            'explanation', 'difficulty'
        ]


class CodexBookmarkSerializer(serializers.ModelSerializer):
    article = CodexArticleListSerializer(read_only=True)
    
    class Meta:
        model = CodexBookmark
        fields = ['id', 'article', 'created_at']


class CodexReadingProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodexReadingProgress
        fields = ['article', 'progress_percentage', 'last_read_at', 'completed']
