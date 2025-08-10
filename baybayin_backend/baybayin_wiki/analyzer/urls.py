"""
URL configuration for the Baybayin Document Analyzer
"""

from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    # Repository management
    path('repository/info/', views.get_repository_info, name='repository-info'),
    path('repository/delete/', views.delete_repository, name='repository-delete'),
    
    # Document management
    path('upload/', views.upload_document, name='upload-document'),
    path('documents/', views.list_documents, name='list-documents'),
    path('analyze/', views.analyze_single_document, name='analyze-document'),
    
    # Processing and extraction
    path('process/', views.process_repository, name='process-repository'),
    path('results/', views.get_processing_results, name='processing-results'),
    path('save-content/', views.save_extracted_content, name='save-content'),
    
    # System status
    path('status/', views.get_analyzer_status, name='analyzer-status'),
]
