"""
PDF Analyzer for Baybayin Documents
Handles PDF processing, text extraction, and Baybayin content analysis
"""

import os
import logging
from typing import Dict, List, Optional, Any, BinaryIO
from pathlib import Path
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import pytesseract
from django.core.files.storage import default_storage
from django.conf import settings

logger = logging.getLogger(__name__)

class PDFAnalyzer:
    """Analyzes PDF files for Baybayin content"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.temp_dir = getattr(settings, 'TEMP_ROOT', '/tmp')
        
        # OCR configuration for Baybayin
        self.ocr_config = {
            'lang': 'eng+fil',  # English + Filipino
            'config': '--psm 6 --oem 3'  # Page segmentation mode
        }
    
    def analyze_pdf(self, file_path: str, user_id: int) -> Dict[str, Any]:
        """
        Analyze a PDF file for Baybayin content
        
        Args:
            file_path: Path to the PDF file
            user_id: ID of the user uploading the file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info(f"Starting PDF analysis for user {user_id}: {file_path}")
            
            # Validate file
            if not self._validate_file(file_path):
                return {'error': 'Invalid PDF file or file too large'}
            
            analysis_result = {
                'file_info': self._get_file_info(file_path),
                'text_content': self._extract_text_content(file_path),
                'images': self._extract_images(file_path),
                'baybayin_analysis': {},
                'metadata': {},
                'user_id': user_id
            }
            
            # Analyze extracted content for Baybayin
            analysis_result['baybayin_analysis'] = self._analyze_baybayin_content(
                analysis_result['text_content'],
                analysis_result['images']
            )
            
            # Extract metadata
            analysis_result['metadata'] = self._extract_metadata(file_path)
            
            logger.info(f"PDF analysis completed successfully for user {user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing PDF: {e}")
            return {'error': f'PDF analysis failed: {str(e)}'}
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate PDF file size and format"""
        try:
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"File too large: {file_size} bytes")
                return False
            
            # Check if it's a valid PDF
            with open(file_path, 'rb') as file:
                PyPDF2.PdfReader(file)
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Extract basic file information"""
        try:
            stat = os.stat(file_path)
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)
            
            return {
                'filename': os.path.basename(file_path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'page_count': page_count,
                'modified_time': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    def _extract_text_content(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from PDF"""
        try:
            text_content = {
                'pages': [],
                'full_text': '',
                'text_extraction_method': 'pdfplumber'
            }
            
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ''
                    text_content['pages'].append({
                        'page_number': i + 1,
                        'text': page_text,
                        'word_count': len(page_text.split())
                    })
                    text_content['full_text'] += page_text + '\n'
            
            # If no text found, try OCR
            if not text_content['full_text'].strip():
                logger.info("No text found with pdfplumber, trying OCR...")
                text_content = self._extract_text_with_ocr(file_path)
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return {'pages': [], 'full_text': '', 'error': str(e)}
    
    def _extract_text_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """Extract text using OCR when direct text extraction fails"""
        try:
            text_content = {
                'pages': [],
                'full_text': '',
                'text_extraction_method': 'ocr'
            }
            
            # Convert PDF to images
            images = convert_from_path(file_path, dpi=300)
            
            for i, image in enumerate(images):
                # Perform OCR on each page
                page_text = pytesseract.image_to_string(
                    image, 
                    lang=self.ocr_config['lang'],
                    config=self.ocr_config['config']
                )
                
                text_content['pages'].append({
                    'page_number': i + 1,
                    'text': page_text,
                    'word_count': len(page_text.split()),
                    'extraction_method': 'ocr'
                })
                text_content['full_text'] += page_text + '\n'
            
            return text_content
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {'pages': [], 'full_text': '', 'error': f'OCR failed: {str(e)}'}
    
    def _extract_images(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF for further analysis"""
        try:
            images = []
            
            # Convert PDF pages to images
            pdf_images = convert_from_path(file_path, dpi=200, first_page=1, last_page=5)  # Limit to first 5 pages
            
            for i, image in enumerate(pdf_images):
                # Save temporary image for analysis
                temp_image_path = os.path.join(self.temp_dir, f"pdf_page_{i+1}.png")
                image.save(temp_image_path, 'PNG')
                
                images.append({
                    'page_number': i + 1,
                    'temp_path': temp_image_path,
                    'size': image.size,
                    'mode': image.mode
                })
            
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    def _analyze_baybayin_content(self, text_content: Dict, images: List[Dict]) -> Dict[str, Any]:
        """Analyze content for Baybayin-specific information"""
        try:
            analysis = {
                'baybayin_keywords': [],
                'potential_baybayin_text': [],
                'historical_context': [],
                'linguistic_elements': [],
                'confidence_score': 0.0
            }
            
            # Keywords that suggest Baybayin content
            baybayin_keywords = [
                'baybayin', 'alibata', 'philippine script', 'ancient filipino',
                'pre-colonial', 'tagalog script', 'syllabic', 'abugida',
                'kudlit', 'diacritic', 'spanish colonization', 'pre-hispanic'
            ]
            
            full_text = text_content.get('full_text', '').lower()
            
            # Find Baybayin-related keywords
            found_keywords = [kw for kw in baybayin_keywords if kw in full_text]
            analysis['baybayin_keywords'] = found_keywords
            
            # Calculate confidence score based on keyword frequency
            total_keywords = sum(full_text.count(kw) for kw in found_keywords)
            text_length = len(full_text.split())
            
            if text_length > 0:
                analysis['confidence_score'] = min(total_keywords / text_length * 100, 100.0)
            
            # Extract sentences containing Baybayin keywords
            sentences = full_text.split('.')
            relevant_sentences = [
                s.strip() for s in sentences 
                if any(kw in s.lower() for kw in baybayin_keywords)
            ]
            analysis['potential_baybayin_text'] = relevant_sentences[:10]  # Limit to 10 sentences
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Baybayin content: {e}")
            return {'error': str(e)}
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata or {}
                
                return {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'creation_date': str(metadata.get('/CreationDate', '')),
                    'modification_date': str(metadata.get('/ModDate', ''))
                }
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files created during analysis"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temp file {file_path}: {e}")
