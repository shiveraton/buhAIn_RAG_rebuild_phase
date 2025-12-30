from rest_framework import serializers
from .models import PDFCodexEntry


class PDFCodexEntryListSerializer(serializers.ModelSerializer):
    """
    Serializer that mimics CodexArticleListSerializer structure
    Allows frontend to consume PDF content without changes
    """
    
    # Map PDF fields to article fields expected by frontend
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    content = serializers.CharField(source='text')
    category = serializers.SerializerMethodField()  # For detail view compatibility
    category_name = serializers.SerializerMethodField()
    category_color = serializers.SerializerMethodField()
    reading_time = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    difficulty_level = serializers.SerializerMethodField()
    is_featured = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = PDFCodexEntry
        fields = [
            'id', 'title', 'slug', 'category', 'category_name', 'category_color',
            'summary', 'content', 'featured_image', 'tags', 'reading_time',
            'difficulty_level', 'is_featured', 'created_at', 'updated_at',
            'page_number', 'chunk_index'  # Include PDF-specific fields
        ]
    
    def get_title(self, obj):
        """Generate title from page number and chunk"""
        if obj.chunk_index == 0:
            return f"Baybayin Codex - Page {obj.page_number}"
        return f"Baybayin Codex - Page {obj.page_number} (Part {obj.chunk_index + 1})"
    
    def get_slug(self, obj):
        """Generate slug from page and chunk"""
        return f"page-{obj.page_number}-chunk-{obj.chunk_index}"
    
    def get_summary(self, obj):
        """First 150 characters as summary"""
        text = obj.text.strip()
        return text[:150] + "..." if len(text) > 150 else text
    
    def get_category(self, obj):
        """Category object for detail view"""
        return {
            "id": 1,
            "name": "PDF Content",
            "color": "#4F46E5",
            "slug": "pdf-content"
        }
    
    def get_category_name(self, obj):
        return "PDF Content"
    
    def get_category_color(self, obj):
        return "#4F46E5"  # Indigo color
    
    def get_reading_time(self, obj):
        """Estimate reading time (200 words per minute)"""
        word_count = len(obj.text.split())
        return max(1, word_count // 200)
    
    def get_tags(self, obj):
        """Generate tags based on page number"""
        return [f"Page {obj.page_number}", "PDF"]
    
    def get_difficulty_level(self, obj):
        """Default difficulty"""
        return "intermediate"
    
    def get_is_featured(self, obj):
        """Mark first chunk of each page as featured"""
        return obj.chunk_index == 0
    
    def get_featured_image(self, obj):
        """No featured image for PDF content"""
        return None
    
    def get_updated_at(self, obj):
        """Use created_at as updated_at"""
        return obj.created_at


class PDFCodexEntryDetailSerializer(PDFCodexEntryListSerializer):
    """
    Detail serializer that mimics CodexArticleDetailSerializer
    """
    
    gallery_images = serializers.SerializerMethodField()
    baybayin_examples = serializers.SerializerMethodField()
    interactive_elements = serializers.SerializerMethodField()
    meta_description = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()
    published_at = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    reading_progress = serializers.SerializerMethodField()
    
    class Meta(PDFCodexEntryListSerializer.Meta):
        fields = PDFCodexEntryListSerializer.Meta.fields + [
            'gallery_images', 'baybayin_examples', 'interactive_elements',
            'meta_description', 'keywords', 'published_at',
            'is_bookmarked', 'reading_progress'
        ]
    
    def get_gallery_images(self, obj):
        return []
    
    def get_baybayin_examples(self, obj):
        return {}
    
    def get_interactive_elements(self, obj):
        return {}
    
    def get_meta_description(self, obj):
        return self.get_summary(obj)
    
    def get_keywords(self, obj):
        return ["Baybayin", "PDF", f"Page {obj.page_number}"]
    
    def get_published_at(self, obj):
        return obj.created_at
    
    def get_is_bookmarked(self, obj):
        """Not implemented for PDF content yet"""
        return False
    
    def get_reading_progress(self, obj):
        """Not implemented for PDF content yet"""
        return None
