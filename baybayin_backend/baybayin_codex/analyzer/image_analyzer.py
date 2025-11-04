"""
Image Analyzer for Baybayin Documents
Handles image processing, OCR, and Baybayin script recognition
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from django.core.files.storage import default_storage
from django.conf import settings

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """Analyzes images for Baybayin content and script recognition"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        self.max_file_size = 25 * 1024 * 1024  # 25MB
        self.temp_dir = getattr(settings, 'TEMP_ROOT', '/tmp')
        
        # OCR configuration optimized for Baybayin
        self.ocr_config = {
            'lang': 'eng+fil',
            'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 '
        }
        
        # Baybayin character patterns (basic set)
        self.baybayin_unicode_range = (0x1700, 0x171F)  # Tagalog Unicode block
    
    def analyze_image(self, file_path: str, user_id: int) -> Dict[str, Any]:
        """
        Analyze an image file for Baybayin content
        
        Args:
            file_path: Path to the image file
            user_id: ID of the user uploading the file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info(f"Starting image analysis for user {user_id}: {file_path}")
            
            # Validate file
            if not self._validate_image(file_path):
                return {'error': 'Invalid image file or file too large'}
            
            # Load and preprocess image
            original_image = self._load_image(file_path)
            processed_images = self._preprocess_image(original_image)
            
            analysis_result = {
                'file_info': self._get_image_info(file_path, original_image),
                'text_content': {},
                'baybayin_analysis': {},
                'visual_analysis': {},
                'metadata': {},
                'user_id': user_id
            }
            
            # Extract text using OCR with different preprocessing
            analysis_result['text_content'] = self._extract_text_from_image(processed_images)
            
            # Analyze for Baybayin content
            analysis_result['baybayin_analysis'] = self._analyze_baybayin_content(
                analysis_result['text_content'],
                original_image
            )
            
            # Visual analysis for script characteristics
            analysis_result['visual_analysis'] = self._analyze_visual_characteristics(original_image)
            
            # Extract image metadata
            analysis_result['metadata'] = self._extract_image_metadata(file_path)
            
            logger.info(f"Image analysis completed successfully for user {user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {'error': f'Image analysis failed: {str(e)}'}
    
    def _validate_image(self, file_path: str) -> bool:
        """Validate image file size and format"""
        try:
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"Image file too large: {file_size} bytes")
                return False
            
            # Check if it's a valid image
            with Image.open(file_path) as img:
                img.verify()
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False
    
    def _load_image(self, file_path: str) -> np.ndarray:
        """Load image using OpenCV"""
        return cv2.imread(file_path)
    
    def _get_image_info(self, file_path: str, image: np.ndarray) -> Dict[str, Any]:
        """Extract basic image information"""
        try:
            stat = os.stat(file_path)
            height, width = image.shape[:2]
            
            return {
                'filename': os.path.basename(file_path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'dimensions': {'width': width, 'height': height},
                'aspect_ratio': round(width / height, 2),
                'channels': image.shape[2] if len(image.shape) > 2 else 1,
                'modified_time': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}
    
    def _preprocess_image(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Preprocess image for better OCR results"""
        try:
            processed_images = {}
            
            # Original image
            processed_images['original'] = image
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            processed_images['grayscale'] = gray
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            processed_images['blurred'] = blurred
            
            # Apply thresholding
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images['threshold'] = thresh
            
            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed_images['cleaned'] = cleaned
            
            # Enhance contrast
            enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
            processed_images['enhanced'] = enhanced
            
            # Edge detection for script analysis
            edges = cv2.Canny(gray, 50, 150)
            processed_images['edges'] = edges
            
            return processed_images
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return {'original': image}
    
    def _extract_text_from_image(self, processed_images: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Extract text using OCR on different processed versions"""
        try:
            text_results = {
                'extraction_methods': [],
                'combined_text': '',
                'confidence_scores': {}
            }
            
            # Try OCR on different preprocessed images
            for method, image in processed_images.items():
                if method in ['original', 'grayscale', 'threshold', 'enhanced']:
                    try:
                        # Convert OpenCV image to PIL for Tesseract
                        if len(image.shape) == 3:
                            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                        else:
                            pil_image = Image.fromarray(image)
                        
                        # Extract text with confidence data
                        ocr_data = pytesseract.image_to_data(
                            pil_image,
                            lang=self.ocr_config['lang'],
                            config=self.ocr_config['config'],
                            output_type=pytesseract.Output.DICT
                        )
                        
                        # Filter high-confidence text
                        confident_text = []
                        for i, conf in enumerate(ocr_data['conf']):
                            if int(conf) > 30:  # Confidence threshold
                                text = ocr_data['text'][i].strip()
                                if text:
                                    confident_text.append(text)
                        
                        method_text = ' '.join(confident_text)
                        if method_text:
                            text_results['extraction_methods'].append({
                                'method': method,
                                'text': method_text,
                                'word_count': len(confident_text),
                                'avg_confidence': np.mean([int(c) for c in ocr_data['conf'] if int(c) > 0])
                            })
                            
                            text_results['combined_text'] += method_text + ' '
                            
                    except Exception as e:
                        logger.warning(f"OCR failed for method {method}: {e}")
            
            # Remove duplicates and clean combined text
            text_results['combined_text'] = ' '.join(set(text_results['combined_text'].split()))
            
            return text_results
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return {'extraction_methods': [], 'combined_text': '', 'error': str(e)}
    
    def _analyze_baybayin_content(self, text_content: Dict, image: np.ndarray) -> Dict[str, Any]:
        """Analyze content for Baybayin-specific characteristics"""
        try:
            analysis = {
                'baybayin_keywords': [],
                'script_characteristics': {},
                'potential_baybayin_regions': [],
                'confidence_score': 0.0,
                'visual_indicators': []
            }
            
            # Keywords that suggest Baybayin content
            baybayin_keywords = [
                'baybayin', 'alibata', 'philippine script', 'ancient filipino',
                'pre-colonial', 'tagalog script', 'syllabic', 'abugida',
                'kudlit', 'diacritic', 'kulitan', 'surat'
            ]
            
            combined_text = text_content.get('combined_text', '').lower()
            
            # Find Baybayin-related keywords
            found_keywords = [kw for kw in baybayin_keywords if kw in combined_text]
            analysis['baybayin_keywords'] = found_keywords
            
            # Analyze script characteristics from visual features
            analysis['script_characteristics'] = self._analyze_script_characteristics(image)
            
            # Look for potential Baybayin Unicode characters
            analysis['potential_baybayin_regions'] = self._detect_baybayin_characters(image)
            
            # Calculate confidence score
            keyword_score = len(found_keywords) * 20
            visual_score = analysis['script_characteristics'].get('syllabic_likelihood', 0) * 50
            analysis['confidence_score'] = min(keyword_score + visual_score, 100.0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Baybayin content: {e}")
            return {'error': str(e)}
    
    def _analyze_script_characteristics(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze visual characteristics that might indicate Baybayin script"""
        try:
            characteristics = {
                'syllabic_likelihood': 0.0,
                'character_density': 0.0,
                'stroke_patterns': [],
                'text_regions': []
            }
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image
            
            # Find contours (potential characters)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze character-like contours
            character_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 5000:  # Filter by size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    if 0.2 < aspect_ratio < 3.0:  # Reasonable aspect ratio for characters
                        character_contours.append({
                            'area': area,
                            'bbox': (x, y, w, h),
                            'aspect_ratio': aspect_ratio
                        })
            
            characteristics['character_density'] = len(character_contours) / (image.shape[0] * image.shape[1]) * 1000000
            
            # Analyze if characters have syllabic-like properties
            if character_contours:
                avg_aspect_ratio = np.mean([c['aspect_ratio'] for c in character_contours])
                # Baybayin characters tend to be more square-like than linear alphabets
                if 0.7 < avg_aspect_ratio < 1.5:
                    characteristics['syllabic_likelihood'] = min(avg_aspect_ratio * 50, 100)
            
            characteristics['text_regions'] = character_contours[:20]  # Limit to first 20
            
            return characteristics
            
        except Exception as e:
            logger.error(f"Error analyzing script characteristics: {e}")
            return {}
    
    def _detect_baybayin_characters(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Attempt to detect potential Baybayin character regions"""
        try:
            regions = []
            
            # This is a simplified approach - in practice, you'd need a trained model
            # for accurate Baybayin character detection
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image
            
            # Use template matching for common Baybayin character shapes
            # This is a placeholder - you'd need actual Baybayin character templates
            
            # For now, just detect text-like regions
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours[:10]):  # Limit to 10 regions
                area = cv2.contourArea(contour)
                if area > 100:
                    x, y, w, h = cv2.boundingRect(contour)
                    regions.append({
                        'region_id': i,
                        'bbox': (x, y, w, h),
                        'area': area,
                        'confidence': 0.1  # Low confidence without proper trained model
                    })
            
            return regions
            
        except Exception as e:
            logger.error(f"Error detecting Baybayin characters: {e}")
            return []
    
    def _analyze_visual_characteristics(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze overall visual characteristics of the image"""
        try:
            visual_analysis = {
                'color_analysis': {},
                'texture_analysis': {},
                'layout_analysis': {}
            }
            
            # Color analysis
            if len(image.shape) == 3:
                mean_color = np.mean(image, axis=(0, 1))
                visual_analysis['color_analysis'] = {
                    'mean_bgr': mean_color.tolist(),
                    'is_color': True,
                    'dominant_channel': np.argmax(mean_color)
                }
            else:
                visual_analysis['color_analysis'] = {
                    'mean_intensity': float(np.mean(image)),
                    'is_color': False
                }
            
            # Basic texture analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            visual_analysis['texture_analysis'] = {
                'sharpness': float(laplacian_var),
                'is_blurry': laplacian_var < 100
            }
            
            # Layout analysis
            height, width = image.shape[:2]
            visual_analysis['layout_analysis'] = {
                'orientation': 'portrait' if height > width else 'landscape',
                'aspect_ratio': width / height,
                'resolution_category': self._categorize_resolution(width, height)
            }
            
            return visual_analysis
            
        except Exception as e:
            logger.error(f"Error in visual analysis: {e}")
            return {}
    
    def _categorize_resolution(self, width: int, height: int) -> str:
        """Categorize image resolution"""
        total_pixels = width * height
        if total_pixels > 8000000:  # > 8MP
            return 'high'
        elif total_pixels > 2000000:  # > 2MP
            return 'medium'
        else:
            return 'low'
    
    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract image EXIF metadata"""
        try:
            with Image.open(file_path) as img:
                metadata = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    metadata['exif'] = {k: str(v) for k, v in exif.items() if k < 1000}  # Limit to basic tags
                
                return metadata
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            return {}
