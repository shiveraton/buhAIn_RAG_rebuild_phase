"""
User Repository Management for Baybayin Documents
Handles user-curated content repositories, document management, and database operations
"""

import os
import logging
from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db import transaction
from .content_extractor import ContentExtractor
from .pdf_analyzer import PDFAnalyzer
from .image_analyzer import ImageAnalyzer
from ..models import CodexArticle, CodexCategory, CodexGlossary, CodexTimeline
from baybayin_codex.semantic_search import SemanticSearch

logger = logging.getLogger(__name__)

class UserRepository:
    """Manages user-curated Baybayin document repositories"""
    
    def __init__(self):
        self.content_extractor = ContentExtractor()
        self.pdf_analyzer = PDFAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        
        # Repository settings
        self.max_repo_size = 500 * 1024 * 1024  # 500MB per user
        self.max_files_per_user = 100
        self.supported_file_types = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        
        # Storage paths
        self.user_storage_root = getattr(settings, 'USER_REPOSITORIES_ROOT', 'user_repositories')
        
    def create_user_repository(self, user_id: int) -> Dict[str, Any]:
        """
        Create a new repository for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing repository information
        """
        try:
            user = User.objects.get(id=user_id)
            repo_path = os.path.join(self.user_storage_root, f"user_{user_id}")
            
            # Create directory structure
            os.makedirs(repo_path, exist_ok=True)
            os.makedirs(os.path.join(repo_path, 'documents'), exist_ok=True)
            os.makedirs(os.path.join(repo_path, 'processed'), exist_ok=True)
            os.makedirs(os.path.join(repo_path, 'metadata'), exist_ok=True)
            
            repo_info = {
                'user_id': user_id,
                'username': user.username,
                'repository_path': repo_path,
                'created_at': datetime.now().isoformat(),
                'total_files': 0,
                'total_size': 0,
                'processed_documents': 0,
                'extracted_articles': 0,
                'status': 'active'
            }
            
            # Save repository metadata
            self._save_repository_metadata(user_id, repo_info)
            
            logger.info(f"Created repository for user {user_id}")
            return repo_info
            
        except Exception as e:
            logger.error(f"Error creating repository for user {user_id}: {e}")
            return {'error': f'Repository creation failed: {str(e)}'}
    
    def upload_document(self, user_id: int, file_data: BinaryIO, filename: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload and process a document to user's repository
        
        Args:
            user_id: ID of the user
            file_data: File data to upload
            filename: Name of the file
            metadata: Optional metadata about the file
            
        Returns:
            Dictionary containing upload and processing results
        """
        try:
            # Validate user and repository
            repo_info = self.get_repository_info(user_id)
            if 'error' in repo_info:
                return repo_info
            
            # Validate file
            validation_result = self._validate_upload(user_id, file_data, filename)
            if 'error' in validation_result:
                return validation_result
            
            # Save file to repository
            file_path = self._save_file_to_repository(user_id, file_data, filename)
            
            # Process the document
            processing_result = self._process_document(user_id, file_path, metadata)
            
            # Update repository metadata
            self._update_repository_stats(user_id, file_path, processing_result)
            
            result = {
                'upload_success': True,
                'file_path': file_path,
                'filename': filename,
                'processing_result': processing_result,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully uploaded and processed {filename} for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading document for user {user_id}: {e}")
            return {'error': f'Document upload failed: {str(e)}'}
    
    def process_repository_content(self, user_id: int, auto_save: bool = True) -> Dict[str, Any]:
        """
        Process all content in a user's repository and optionally save to database
        
        Args:
            user_id: ID of the user
            auto_save: Whether to automatically save extracted content to database
            
        Returns:
            Dictionary containing processing results
        """
        try:
            repo_info = self.get_repository_info(user_id)
            if 'error' in repo_info:
                return repo_info
            
            documents_path = os.path.join(repo_info['repository_path'], 'documents')
            processing_results = {
                'processed_files': [],
                'extracted_content': {
                    'articles': [],
                    'glossary_terms': [],
                    'timeline_events': []
                },
                'errors': [],
                'statistics': {
                    'total_files': 0,
                    'successful_processing': 0,
                    'failed_processing': 0,
                    'articles_extracted': 0,
                    'terms_extracted': 0,
                    'events_extracted': 0
                }
            }
            
            # Process all files in the repository
            for root, dirs, files in os.walk(documents_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    processing_results['statistics']['total_files'] += 1
                    
                    try:
                        # Process the file
                        result = self._process_document(user_id, file_path)
                        
                        if 'error' not in result:
                            processing_results['processed_files'].append({
                                'filename': file,
                                'result': result
                            })
                            processing_results['statistics']['successful_processing'] += 1
                            
                            # Extract structured content
                            structured_content = self.content_extractor.extract_structured_content(
                                result, user_id
                            )
                            
                            if 'error' not in structured_content:
                                # Accumulate extracted content
                                processing_results['extracted_content']['articles'].extend(
                                    structured_content.get('articles', [])
                                )
                                processing_results['extracted_content']['glossary_terms'].extend(
                                    structured_content.get('glossary_terms', [])
                                )
                                processing_results['extracted_content']['timeline_events'].extend(
                                    structured_content.get('timeline_events', [])
                                )
                        else:
                            processing_results['errors'].append({
                                'filename': file,
                                'error': result['error']
                            })
                            processing_results['statistics']['failed_processing'] += 1
                            
                    except Exception as e:
                        processing_results['errors'].append({
                            'filename': file,
                            'error': str(e)
                        })
                        processing_results['statistics']['failed_processing'] += 1
            
            # Update statistics
            processing_results['statistics']['articles_extracted'] = len(
                processing_results['extracted_content']['articles']
            )
            processing_results['statistics']['terms_extracted'] = len(
                processing_results['extracted_content']['glossary_terms']
            )
            processing_results['statistics']['events_extracted'] = len(
                processing_results['extracted_content']['timeline_events']
            )
            
            # Save to database if requested
            if auto_save and processing_results['extracted_content']:
                save_result = self.save_extracted_content_to_database(
                    user_id, processing_results['extracted_content']
                )
                processing_results['database_save_result'] = save_result
            
            logger.info(f"Repository processing completed for user {user_id}")
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing repository for user {user_id}: {e}")
            return {'error': f'Repository processing failed: {str(e)}'}
    
    def save_extracted_content_to_database(self, user_id: int, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save extracted content to the database
        
        Args:
            user_id: ID of the user
            extracted_content: Extracted content from documents
            
        Returns:
            Dictionary containing save results
        """
        try:
            user = User.objects.get(id=user_id)
            save_results = {
                'articles_saved': 0,
                'terms_saved': 0,
                'events_saved': 0,
                'errors': []
            }
            semantic_search = SemanticSearch()
            texts_to_embed = []
            meta_to_embed = []
            with transaction.atomic():
                # Save articles
                articles = extracted_content.get('articles', [])
                for article_data in articles:
                    try:
                        # Get or create category for user-uploaded content
                        category, created = CodexCategory.objects.get_or_create(
                            name='User Contributions',
                            defaults={
                                'description': 'Content contributed by users',
                                'slug': 'user-contributions',
                                'color': '#28a745'
                            }
                        )
                        
                        # Create article
                        article = CodexArticle.objects.create(
                            title=article_data['title'],
                            category=category,
                            summary=article_data.get('summary', ''),
                            content=article_data['content'],
                            source=article_data.get('source', 'user_upload'),
                            author=user,
                            tags=article_data.get('tags', []),
                            difficulty_level=article_data.get('difficulty_level', 'beginner'),
                            baybayin_examples=article_data.get('baybayin_examples', []),
                            metadata=article_data.get('metadata', {}),
                            is_published=False  # Require review before publishing
                        )
                        
                        save_results['articles_saved'] += 1
                        # Add to vector store
                        texts_to_embed.append(article.content)
                        meta_to_embed.append({
                            'type': 'article',
                            'user_id': user_id,
                            'article_id': article.id,
                            'title': article.title,
                            'tags': article.tags,
                            'difficulty_level': article.difficulty_level
                        })
                    except Exception as e:
                        save_results['errors'].append({
                            'type': 'article',
                            'title': article_data.get('title', 'Unknown'),
                            'error': str(e)
                        })
                
                # Save glossary terms
                terms = extracted_content.get('glossary_terms', [])
                for term_data in terms:
                    try:
                        # Check if term already exists
                        existing_term = CodexGlossary.objects.filter(
                            term__iexact=term_data['term']
                        ).first()
                        
                        if not existing_term:
                            term = CodexGlossary.objects.create(
                                term=term_data['term'],
                                definition=term_data['definition'],
                                baybayin_script=term_data.get('baybayin_script', ''),
                                source=term_data.get('source', 'user_upload'),
                                metadata=term_data.get('metadata', {})
                            )
                            save_results['terms_saved'] += 1
                            # Add to vector store
                            texts_to_embed.append(term.definition)
                            meta_to_embed.append({
                                'type': 'glossary',
                                'user_id': user_id,
                                'term_id': term.id,
                                'term': term.term
                            })
                    except Exception as e:
                        save_results['errors'].append({
                            'type': 'term',
                            'term': term_data.get('term', 'Unknown'),
                            'error': str(e)
                        })
                
                # Save timeline events
                events = extracted_content.get('timeline_events', [])
                for event_data in events:
                    try:
                        # Check if similar event already exists
                        existing_event = CodexTimeline.objects.filter(
                            year=event_data.get('year', 0),
                            title__icontains=event_data.get('title', '')[:50]
                        ).first()
                        
                        if not existing_event:
                            event = CodexTimeline.objects.create(
                                title=event_data['title'],
                                year=event_data.get('year', 0),
                                period=event_data.get('period', ''),
                                description=event_data['description'],
                                source=event_data.get('source', 'user_upload'),
                                importance=event_data.get('importance', 'medium'),
                                metadata=event_data.get('metadata', {})
                            )
                            save_results['events_saved'] += 1
                            # Add to vector store
                            texts_to_embed.append(event.description)
                            meta_to_embed.append({
                                'type': 'timeline',
                                'user_id': user_id,
                                'event_id': event.id,
                                'title': event.title,
                                'year': event.year
                            })
                    except Exception as e:
                        save_results['errors'].append({
                            'type': 'event',
                            'title': event_data.get('title', 'Unknown'),
                            'error': str(e)
                        })
            
            # embed and add to vector store after db save
            if texts_to_embed:
                semantic_search.add_documents(texts_to_embed, meta_to_embed)
            logger.info(f"Content saved to database and vector store for user {user_id}: {save_results}")
            return save_results
        except Exception as e:
            logger.error(f"Error saving content to database for user {user_id}: {e}")
            return {'error': f'Database save failed: {str(e)}'}
    
    def get_repository_info(self, user_id: int) -> Dict[str, Any]:
        """Get information about a user's repository"""
        try:
            repo_path = os.path.join(self.user_storage_root, f"user_{user_id}")
            metadata_file = os.path.join(repo_path, 'metadata', 'repository_info.json')
            
            if not os.path.exists(repo_path):
                # Repository doesn't exist, create it
                return self.create_user_repository(user_id)
            
            # Load existing metadata if available
            if os.path.exists(metadata_file):
                import json
                with open(metadata_file, 'r') as f:
                    repo_info = json.load(f)
                
                # Update current statistics
                repo_info.update(self._calculate_repository_stats(repo_path))
                return repo_info
            else:
                # Create metadata for existing repository
                user = User.objects.get(id=user_id)
                repo_info = {
                    'user_id': user_id,
                    'username': user.username,
                    'repository_path': repo_path,
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                }
                repo_info.update(self._calculate_repository_stats(repo_path))
                self._save_repository_metadata(user_id, repo_info)
                return repo_info
                
        except Exception as e:
            logger.error(f"Error getting repository info for user {user_id}: {e}")
            return {'error': f'Failed to get repository info: {str(e)}'}
    
    def delete_repository(self, user_id: int) -> Dict[str, Any]:
        """Delete a user's repository and all its contents"""
        try:
            repo_path = os.path.join(self.user_storage_root, f"user_{user_id}")
            
            if os.path.exists(repo_path):
                import shutil
                shutil.rmtree(repo_path)
                logger.info(f"Deleted repository for user {user_id}")
                return {'success': True, 'message': 'Repository deleted successfully'}
            else:
                return {'error': 'Repository does not exist'}
                
        except Exception as e:
            logger.error(f"Error deleting repository for user {user_id}: {e}")
            return {'error': f'Repository deletion failed: {str(e)}'}
    
    def _validate_upload(self, user_id: int, file_data: BinaryIO, filename: str) -> Dict[str, Any]:
        """Validate file upload requirements"""
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_file_types:
            return {'error': f'Unsupported file type: {file_ext}'}
        
        # Check file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset to beginning
        
        if file_size > 25 * 1024 * 1024:  # 25MB limit per file
            return {'error': 'File too large (max 25MB)'}
        
        # Check user's total repository size
        repo_info = self.get_repository_info(user_id)
        if 'error' not in repo_info:
            current_size = repo_info.get('total_size', 0)
            if current_size + file_size > self.max_repo_size:
                return {'error': 'Repository size limit exceeded'}
            
            # Check file count
            current_files = repo_info.get('total_files', 0)
            if current_files >= self.max_files_per_user:
                return {'error': 'Maximum file count reached'}
        
        return {'valid': True}
    
    def _save_file_to_repository(self, user_id: int, file_data: BinaryIO, filename: str) -> str:
        """Save file to user's repository"""
        repo_path = os.path.join(self.user_storage_root, f"user_{user_id}", 'documents')
        os.makedirs(repo_path, exist_ok=True)
        
        # Generate unique filename if needed
        file_path = os.path.join(repo_path, filename)
        counter = 1
        base_name, ext = os.path.splitext(filename)
        
        while os.path.exists(file_path):
            new_filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(repo_path, new_filename)
            counter += 1
        
        # Save file
        with open(file_path, 'wb') as f:
            file_data.seek(0)
            f.write(file_data.read())
        
        return file_path
    
    def _process_document(self, user_id: int, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a document using appropriate analyzer"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self.pdf_analyzer.analyze_pdf(file_path, user_id)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
            return self.image_analyzer.analyze_image(file_path, user_id)
        else:
            return {'error': f'Unsupported file type for processing: {file_ext}'}
    
    def _calculate_repository_stats(self, repo_path: str) -> Dict[str, Any]:
        """Calculate current repository statistics"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'processed_documents': 0,
            'last_updated': datetime.now().isoformat()
        }
        
        documents_path = os.path.join(repo_path, 'documents')
        processed_path = os.path.join(repo_path, 'processed')
        
        if os.path.exists(documents_path):
            for root, dirs, files in os.walk(documents_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    stats['total_files'] += 1
                    stats['total_size'] += os.path.getsize(file_path)
        
        if os.path.exists(processed_path):
            stats['processed_documents'] = len([
                f for f in os.listdir(processed_path) 
                if f.endswith('.json')
            ])
        
        return stats
    
    def _save_repository_metadata(self, user_id: int, repo_info: Dict[str, Any]):
        """Save repository metadata to file"""
        repo_path = os.path.join(self.user_storage_root, f"user_{user_id}")
        metadata_dir = os.path.join(repo_path, 'metadata')
        os.makedirs(metadata_dir, exist_ok=True)
        
        metadata_file = os.path.join(metadata_dir, 'repository_info.json')
        
        import json
        with open(metadata_file, 'w') as f:
            json.dump(repo_info, f, indent=2)
    
    def _update_repository_stats(self, user_id: int, file_path: str, processing_result: Dict[str, Any]):
        """Update repository statistics after processing"""
        try:
            repo_info = self.get_repository_info(user_id)
            if 'error' not in repo_info:
                # Save processing result
                processed_dir = os.path.join(repo_info['repository_path'], 'processed')
                os.makedirs(processed_dir, exist_ok=True)
                
                result_filename = f"{Path(file_path).stem}_result.json"
                result_path = os.path.join(processed_dir, result_filename)
                
                import json
                with open(result_path, 'w') as f:
                    json.dump(processing_result, f, indent=2)
                
                # Update repository metadata
                repo_info['processed_documents'] += 1
                repo_info['last_updated'] = datetime.now().isoformat()
                self._save_repository_metadata(user_id, repo_info)
                
        except Exception as e:
            logger.error(f"Error updating repository stats: {e}")
    
    def list_user_documents(self, user_id: int) -> Dict[str, Any]:
        """List all documents in a user's repository"""
        try:
            repo_info = self.get_repository_info(user_id)
            if 'error' in repo_info:
                return repo_info
            
            documents_path = os.path.join(repo_info['repository_path'], 'documents')
            documents = []
            
            if os.path.exists(documents_path):
                for root, dirs, files in os.walk(documents_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        documents.append({
                            'filename': file,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                            'extension': Path(file).suffix.lower()
                        })
            
            return {
                'documents': documents,
                'total_count': len(documents),
                'repository_info': repo_info
            }
            
        except Exception as e:
            logger.error(f"Error listing documents for user {user_id}: {e}")
            return {'error': f'Failed to list documents: {str(e)}'}
    
    def get_processing_results(self, user_id: int, filename: Optional[str] = None) -> Dict[str, Any]:
        """Get processing results for documents"""
        try:
            repo_info = self.get_repository_info(user_id)
            if 'error' in repo_info:
                return repo_info
            
            processed_path = os.path.join(repo_info['repository_path'], 'processed')
            results = {}
            
            if os.path.exists(processed_path):
                import json
                
                if filename:
                    # Get result for specific file
                    result_filename = f"{Path(filename).stem}_result.json"
                    result_path = os.path.join(processed_path, result_filename)
                    
                    if os.path.exists(result_path):
                        with open(result_path, 'r') as f:
                            results[filename] = json.load(f)
                    else:
                        return {'error': f'No processing results found for {filename}'}
                else:
                    # Get all results
                    for result_file in os.listdir(processed_path):
                        if result_file.endswith('_result.json'):
                            result_path = os.path.join(processed_path, result_file)
                            original_filename = result_file.replace('_result.json', '')
                            
                            with open(result_path, 'r') as f:
                                results[original_filename] = json.load(f)
            
            return {
                'processing_results': results,
                'total_processed': len(results),
                'repository_info': repo_info
            }
            
        except Exception as e:
            logger.error(f"Error getting processing results for user {user_id}: {e}")
            return {'error': f'Failed to get processing results: {str(e)}'}
