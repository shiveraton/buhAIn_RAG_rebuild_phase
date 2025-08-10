"""
Views for the Baybayin Document Analyzer
Provides API endpoints for document upload, processing, and repository management
"""

import os
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.conf import settings

from .user_repository import UserRepository
from .content_extractor import ContentExtractor
from .pdf_analyzer import PDFAnalyzer
from .image_analyzer import ImageAnalyzer

logger = logging.getLogger(__name__)

# Initialize analyzer components
user_repository = UserRepository()
content_extractor = ContentExtractor()
pdf_analyzer = PDFAnalyzer()
image_analyzer = ImageAnalyzer()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Upload a document to user's repository for analysis
    """
    try:
        user_id = request.user.id
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        metadata = {
            'upload_timestamp': request.data.get('timestamp'),
            'description': request.data.get('description', ''),
            'tags': request.data.get('tags', [])
        }
        
        # Upload and process the document
        result = user_repository.upload_document(
            user_id=user_id,
            file_data=uploaded_file,
            filename=uploaded_file.name,
            metadata=metadata
        )
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in upload_document view: {e}")
        return Response(
            {'error': f'Upload failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_repository_info(request):
    """
    Get information about user's repository
    """
    try:
        user_id = request.user.id
        repo_info = user_repository.get_repository_info(user_id)
        
        if 'error' in repo_info:
            return Response(repo_info, status=status.HTTP_404_NOT_FOUND)
        
        return Response(repo_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_repository_info view: {e}")
        return Response(
            {'error': f'Failed to get repository info: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """
    List all documents in user's repository
    """
    try:
        user_id = request.user.id
        documents = user_repository.list_user_documents(user_id)
        
        if 'error' in documents:
            return Response(documents, status=status.HTTP_404_NOT_FOUND)
        
        return Response(documents, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in list_documents view: {e}")
        return Response(
            {'error': f'Failed to list documents: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_repository(request):
    """
    Process all documents in user's repository and extract content
    """
    try:
        user_id = request.user.id
        auto_save = request.data.get('auto_save', True)
        
        # Process repository content
        results = user_repository.process_repository_content(
            user_id=user_id,
            auto_save=auto_save
        )
        
        if 'error' in results:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in process_repository view: {e}")
        return Response(
            {'error': f'Repository processing failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_processing_results(request):
    """
    Get processing results for user's documents
    """
    try:
        user_id = request.user.id
        filename = request.GET.get('filename')
        
        results = user_repository.get_processing_results(user_id, filename)
        
        if 'error' in results:
            return Response(results, status=status.HTTP_404_NOT_FOUND)
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_processing_results view: {e}")
        return Response(
            {'error': f'Failed to get processing results: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_single_document(request):
    """
    Analyze a single document without saving to repository
    """
    try:
        user_id = request.user.id
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Save temporary file for analysis
        temp_path = default_storage.save(
            f'temp_analysis/{uploaded_file.name}',
            uploaded_file
        )
        temp_file_path = default_storage.path(temp_path)
        
        try:
            # Analyze based on file type
            if file_extension == '.pdf':
                analysis_result = pdf_analyzer.analyze_pdf(temp_file_path, user_id)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
                analysis_result = image_analyzer.analyze_image(temp_file_path, user_id)
            else:
                return Response(
                    {'error': f'Unsupported file type: {file_extension}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract structured content if analysis successful
            if 'error' not in analysis_result:
                structured_content = content_extractor.extract_structured_content(
                    analysis_result, user_id
                )
                analysis_result['structured_content'] = structured_content
            
            return Response(analysis_result, status=status.HTTP_200_OK)
            
        finally:
            # Clean up temporary file
            if default_storage.exists(temp_path):
                default_storage.delete(temp_path)
        
    except Exception as e:
        logger.error(f"Error in analyze_single_document view: {e}")
        return Response(
            {'error': f'Document analysis failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_extracted_content(request):
    """
    Save extracted content to the database
    """
    try:
        user_id = request.user.id
        extracted_content = request.data.get('extracted_content')
        
        if not extracted_content:
            return Response(
                {'error': 'No extracted content provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save content to database
        save_result = user_repository.save_extracted_content_to_database(
            user_id, extracted_content
        )
        
        if 'error' in save_result:
            return Response(save_result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(save_result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in save_extracted_content view: {e}")
        return Response(
            {'error': f'Failed to save content: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_repository(request):
    """
    Delete user's repository and all its contents
    """
    try:
        user_id = request.user.id
        
        # Confirm deletion (require confirmation parameter)
        if not request.data.get('confirm_deletion', False):
            return Response(
                {'error': 'Deletion not confirmed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = user_repository.delete_repository(user_id)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in delete_repository view: {e}")
        return Response(
            {'error': f'Repository deletion failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analyzer_status(request):
    """
    Get status information about the analyzer system
    """
    try:
        # Check if required dependencies are available
        dependencies_status = {
            'PyPDF2': True,
            'pdfplumber': True,
            'pdf2image': True,
            'PIL': True,
            'pytesseract': True,
            'cv2': True,
            'numpy': True
        }
        
        # Try importing each dependency
        try:
            import PyPDF2
        except ImportError:
            dependencies_status['PyPDF2'] = False
        
        try:
            import pdfplumber
        except ImportError:
            dependencies_status['pdfplumber'] = False
        
        try:
            from pdf2image import convert_from_path
        except ImportError:
            dependencies_status['pdf2image'] = False
        
        try:
            from PIL import Image
        except ImportError:
            dependencies_status['PIL'] = False
        
        try:
            import pytesseract
        except ImportError:
            dependencies_status['pytesseract'] = False
        
        try:
            import cv2
        except ImportError:
            dependencies_status['cv2'] = False
        
        try:
            import numpy
        except ImportError:
            dependencies_status['numpy'] = False
        
        # Check OCR availability
        ocr_available = False
        try:
            import pytesseract
            # Try a simple OCR test
            pytesseract.get_tesseract_version()
            ocr_available = True
        except Exception:
            pass
        
        status_info = {
            'analyzer_available': all(dependencies_status.values()),
            'dependencies': dependencies_status,
            'ocr_available': ocr_available,
            'supported_formats': {
                'pdf': ['.pdf'],
                'images': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            },
            'system_limits': {
                'max_file_size_mb': 25,
                'max_repository_size_mb': 500,
                'max_files_per_user': 100
            }
        }
        
        return Response(status_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_analyzer_status view: {e}")
        return Response(
            {'error': f'Failed to get analyzer status: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
