from rest_framework import serializers
from .models import (
    WikiCategory, WikiArticle, WikiTimeline, WikiGlossary, 
    WikiQuiz, WikiBookmark, WikiReadingProgress
)

class WikiCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = WikiCategory
        fields = ['id', 'name', 'description', 'slug', 'icon', 'color', 'order', 'article_count']


class WikiArticleListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    
    class Meta:
        model = WikiArticle
        fields = [
            'id', 'title', 'slug', 'category_name', 'category_color',
            'summary', 'featured_image', 'tags', 'reading_time',
            'difficulty_level', 'is_featured', 'created_at', 'updated_at'
        ]


class WikiArticleDetailSerializer(serializers.ModelSerializer):
    category = WikiCategorySerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    reading_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = WikiArticle
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
            return WikiBookmark.objects.filter(user=request.user, article=obj).exists()
        return False
    
    def get_reading_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = WikiReadingProgress.objects.get(user=request.user, article=obj)
                return {
                    'percentage': progress.progress_percentage,
                    'completed': progress.completed,
                    'last_read_at': progress.last_read_at
                }
            except WikiReadingProgress.DoesNotExist:
                return None
        return None


class WikiTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiTimeline
        fields = [
            'id', 'title', 'year', 'period', 'description',
            'image', 'source', 'importance'
        ]


class WikiGlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiGlossary
        fields = [
            'id', 'term', 'pronunciation', 'definition',
            'baybayin_script', 'related_terms', 'examples', 'category'
        ]


class WikiQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiQuiz
        fields = [
            'id', 'question', 'options', 'correct_answer',
            'explanation', 'difficulty'
        ]


class WikiBookmarkSerializer(serializers.ModelSerializer):
    article = WikiArticleListSerializer(read_only=True)
    
    class Meta:
        model = WikiBookmark
        fields = ['id', 'article', 'created_at']


class WikiReadingProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiReadingProgress
        fields = ['article', 'progress_percentage', 'last_read_at', 'completed']
