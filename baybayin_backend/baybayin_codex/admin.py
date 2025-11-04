"""
Custom Django admin interface for BaybayinCodex content management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CodexCategory, CodexArticle, CodexTimeline, CodexGlossary, CodexQuiz, CodexBookmark, CodexReadingProgress

# Register your models here.

@admin.register(CodexCategory)
class CodexCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'article_count_display', 'color_display', 'order', 'created_at']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    
    def article_count_display(self, obj):
        count = obj.articles.filter(is_published=True).count()
        if count > 0:
            url = reverse('admin:baybayin_codex_codexarticle_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} articles</a>', url, count)
        return '0 articles'
    article_count_display.short_description = 'Articles'
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(CodexArticle)
class CodexArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty_level', 'reading_time', 'is_published', 'is_featured', 'created_at']
    list_filter = ['category', 'difficulty_level', 'is_published', 'is_featured', 'created_at']
    search_fields = ['title', 'summary', 'content', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'summary')
        }),
        ('Content', {
            'fields': ('content', 'featured_image', 'gallery_images', 'baybayin_examples', 'interactive_elements'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('tags', 'reading_time', 'difficulty_level', 'author'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')


@admin.register(CodexTimeline)
class CodexTimelineAdmin(admin.ModelAdmin):
    list_display = ['year', 'title', 'period', 'importance_display', 'created_at']
    list_filter = ['period', 'importance', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['year']
    
    def importance_display(self, obj):
        colors = {
            'low': '#6c757d',
            'medium': '#007bff', 
            'high': '#ffc107',
            'critical': '#dc3545'
        }
        color = colors.get(obj.importance, '#6c757d')
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.importance.upper()
        )
    importance_display.short_description = 'Importance'


@admin.register(CodexGlossary)
class CodexGlossaryAdmin(admin.ModelAdmin):
    list_display = ['term', 'category', 'difficulty_level', 'created_at']
    list_filter = ['category', 'difficulty_level', 'created_at']
    search_fields = ['term', 'definition']
    ordering = ['term']


@admin.register(CodexQuiz)
class CodexQuizAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'article', 'difficulty', 'created_at']
    list_filter = ['difficulty', 'article__category', 'created_at']
    search_fields = ['question', 'article__title']
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'

@admin.register(CodexBookmark)
class CodexBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'created_at']
    list_filter = ['article__category', 'created_at']
    search_fields = ['user__username', 'article__title']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'article']  # For better performance with large datasets
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'article')
    
@admin.register(CodexReadingProgress)
class CodexReadingProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'progress_percentage', 'completed_display', 'last_read_at']
    list_filter = ['completed', 'article__category', 'last_read_at']
    search_fields = ['user__username', 'article__title']
    ordering = ['-last_read_at']
    raw_id_fields = ['user', 'article']
    
    def completed_display(self, obj):
        if obj.completed:
            return format_html(
                '<span style="background-color: #28a745; padding: 2px 8px; border-radius: 3px; color: white;">✓ Completed</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; padding: 2px 8px; border-radius: 3px; color: black;">{}%</span>',
                obj.progress_percentage
            )
    completed_display.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'article')

# Custom admin site configuration
admin.site.site_header = 'BaybayinCodex Administration'
admin.site.site_title = 'BaybayinCodex Admin'
admin.site.index_title = 'Manage Baybayin Codex Content'
