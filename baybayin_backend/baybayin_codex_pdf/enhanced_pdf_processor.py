"""
Enhanced PDF processing with integrated OCR text sanitization
Updates the existing PDF ingestion pipeline to use the new sanitization capabilities
"""

import logging
from django.utils import timezone
from .models import PDFCodexEntry
from .pdf_ingestion.ocr import run_ocr_with_fallback
from .text_sanitizer import sanitize_ocr_text

logger = logging.getLogger(__name__)

def process_pdf_with_enhanced_ocr(pdf_path, use_enhanced_ocr=True, save_stats=True):
    """
    Enhanced PDF processing that integrates the new OCR sanitization pipeline
    
    Args:
        pdf_path: Path to the PDF file
        use_enhanced_ocr: Whether to use the enhanced OCR with sanitization
        save_stats: Whether to save sanitization statistics to the database
        
    Returns:
        List of PDFCodexEntry objects with enhanced text cleaning
    """
    
    logger.info(f"Processing PDF with enhanced OCR: {pdf_path}")
    
    # Import PDF processing components (assuming they exist)
    try:
        from .pdf_ingestion.extractor import extract_pages_from_pdf
        from .pdf_ingestion.chunker import chunk_text
        from .pdf_ingestion.preprocess import preprocess_image
    except ImportError as e:
        logger.error(f"PDF processing components not available: {e}")
        return []
    
    entries = []
    
    try:
        # Extract pages from PDF
        pages = extract_pages_from_pdf(pdf_path)
        logger.info(f"Extracted {len(pages)} pages from PDF")
        
        for page_num, page_image in enumerate(pages, 1):
            logger.debug(f"Processing page {page_num}")
            
            try:
                # Preprocess image for better OCR
                processed_image = preprocess_image(page_image)
                
                if use_enhanced_ocr:
                    # Use enhanced OCR with fallback and sanitization
                    raw_text, ocr_stats = run_ocr_with_fallback(
                        processed_image, 
                        use_sanitizer=True
                    )
                    
                    # Extract sanitization statistics
                    sanitization_stats = ocr_stats
                    confidence_score = ocr_stats.get('confidence_score', 0.0)
                    ocr_config_used = ocr_stats.get('ocr_config_used', 'enhanced')
                    
                    cleaned_text = raw_text  # Already cleaned by the enhanced OCR
                    
                else:
                    # Legacy OCR processing
                    from .pdf_ingestion.ocr import run_ocr
                    raw_text = run_ocr(processed_image, use_sanitizer=False)
                    
                    # Apply sanitization separately
                    cleaned_text, sanitization_stats = sanitize_ocr_text(raw_text)
                    confidence_score = sanitization_stats['confidence_score']
                    ocr_config_used = 'legacy'
                
                # Skip pages with very low confidence or empty content
                if confidence_score < 0.1 or len(cleaned_text.strip()) < 10:
                    logger.warning(f"Skipping page {page_num}: low confidence ({confidence_score:.2f}) or insufficient content")
                    continue
                
                # Chunk the cleaned text
                chunks = chunk_text(cleaned_text)
                
                for chunk_index, chunk_text in enumerate(chunks):
                    if len(chunk_text.strip()) < 20:  # Skip very short chunks
                        continue
                    
                    # Create database entry
                    entry = PDFCodexEntry(
                        text=raw_text,  # Store original OCR output
                        cleaned_text=chunk_text,  # Store sanitized chunk
                        page_number=page_num,
                        chunk_index=chunk_index,
                        source=f"pdf:{pdf_path}",
                        embedding={}  # Will be populated later by embedding generation
                    )
                    
                    # Add OCR sanitization metadata if requested
                    if save_stats:
                        entry.ocr_sanitization_stats = sanitization_stats
                        entry.ocr_confidence_score = confidence_score
                        entry.ocr_config_used = ocr_config_used
                    
                    entry.save()
                    entries.append(entry)
                    
                    logger.debug(f"Created entry for page {page_num}, chunk {chunk_index} (confidence: {confidence_score:.2f})")
                
            except Exception as e:
                logger.error(f"Failed to process page {page_num}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed PDF: {len(entries)} entries created")
        
    except Exception as e:
        logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
        return []
    
    return entries

def reprocess_existing_entries_with_sanitization(entry_ids=None, min_confidence=0.3):
    """
    Reprocess existing PDF entries with the new sanitization pipeline
    
    Args:
        entry_ids: List of specific entry IDs to reprocess (None for all)
        min_confidence: Minimum confidence threshold to trigger reprocessing
        
    Returns:
        Dictionary with processing statistics
    """
    
    logger.info("Starting batch reprocessing of existing entries")
    
    # Build queryset
    queryset = PDFCodexEntry.objects.all()
    
    if entry_ids:
        queryset = queryset.filter(id__in=entry_ids)
    else:
        # Only reprocess entries with low or missing confidence scores
        from django.db.models import Q
        queryset = queryset.filter(
            Q(ocr_confidence_score__isnull=True) |
            Q(ocr_confidence_score__lt=min_confidence)
        )
    
    total_entries = queryset.count()
    processed = 0
    improved = 0
    errors = 0
    
    logger.info(f"Found {total_entries} entries to reprocess")
    
    for entry in queryset:
        try:
            # Apply sanitization to the original text
            if entry.text:
                cleaned_text, stats = sanitize_ocr_text(entry.text)
                
                # Check if this is an improvement
                current_confidence = entry.ocr_confidence_score or 0.0
                new_confidence = stats['confidence_score']
                
                if new_confidence > current_confidence or len(cleaned_text.strip()) > len(entry.cleaned_text.strip()):
                    # Update the entry
                    entry.cleaned_text = cleaned_text
                    entry.ocr_sanitization_stats = stats
                    entry.ocr_confidence_score = new_confidence
                    entry.ocr_config_used = 'sanitizer_reprocess'
                    entry.save()
                    
                    improved += 1
                    logger.debug(f"Improved entry {entry.id}: confidence {current_confidence:.2f} -> {new_confidence:.2f}")
            
            processed += 1
            
        except Exception as e:
            errors += 1
            logger.error(f"Failed to reprocess entry {entry.id}: {str(e)}")
    
    results = {
        'total_entries': total_entries,
        'processed': processed,
        'improved': improved,
        'errors': errors,
        'success_rate': (processed - errors) / max(1, processed) * 100
    }
    
    logger.info(f"Reprocessing complete: {results}")
    return results

def generate_sanitization_report():
    """
    Generate a report on the current state of OCR sanitization across all entries
    
    Returns:
        Dictionary containing sanitization statistics and insights
    """
    
    from django.db.models import Avg, Count, Max, Min
    
    # Overall statistics
    total_entries = PDFCodexEntry.objects.count()
    sanitized_entries = PDFCodexEntry.objects.filter(
        ocr_confidence_score__isnull=False
    ).count()
    
    # Confidence statistics
    confidence_stats = PDFCodexEntry.objects.filter(
        ocr_confidence_score__isnull=False
    ).aggregate(
        avg_confidence=Avg('ocr_confidence_score'),
        min_confidence=Min('ocr_confidence_score'),
        max_confidence=Max('ocr_confidence_score')
    )
    
    # Confidence distribution
    confidence_ranges = {
        'excellent': PDFCodexEntry.objects.filter(ocr_confidence_score__gte=0.8).count(),
        'good': PDFCodexEntry.objects.filter(
            ocr_confidence_score__gte=0.6, 
            ocr_confidence_score__lt=0.8
        ).count(),
        'fair': PDFCodexEntry.objects.filter(
            ocr_confidence_score__gte=0.4, 
            ocr_confidence_score__lt=0.6
        ).count(),
        'poor': PDFCodexEntry.objects.filter(
            ocr_confidence_score__lt=0.4
        ).count(),
    }
    
    # OCR configuration usage
    config_usage = PDFCodexEntry.objects.filter(
        ocr_config_used__isnull=False
    ).values('ocr_config_used').annotate(
        count=Count('ocr_config_used')
    ).order_by('-count')
    
    # Entries needing attention (low confidence)
    low_confidence_entries = PDFCodexEntry.objects.filter(
        ocr_confidence_score__lt=0.4
    ).order_by('ocr_confidence_score')[:10]
    
    # Recent sanitization activity
    recent_sanitized = PDFCodexEntry.objects.filter(
        ocr_sanitization_stats__isnull=False
    ).order_by('-id')[:5]
    
    report = {
        'overview': {
            'total_entries': total_entries,
            'sanitized_entries': sanitized_entries,
            'sanitization_coverage': sanitized_entries / max(1, total_entries) * 100,
        },
        'confidence_statistics': confidence_stats,
        'confidence_distribution': confidence_ranges,
        'ocr_config_usage': list(config_usage),
        'low_confidence_samples': [
            {
                'id': entry.id,
                'confidence': entry.ocr_confidence_score,
                'text_preview': entry.cleaned_text[:100] if entry.cleaned_text else '',
                'stats': entry.ocr_sanitization_stats
            }
            for entry in low_confidence_entries
        ],
        'recent_activity': [
            {
                'id': entry.id,
                'confidence': entry.ocr_confidence_score,
                'config_used': entry.ocr_config_used,
                'total_fixes': entry.ocr_sanitization_stats.get('total_fixes', 0) if entry.ocr_sanitization_stats else 0
            }
            for entry in recent_sanitized
        ]
    }
    
    return report

def get_sanitization_recommendations():
    """
    Generate recommendations for improving OCR quality based on current data
    
    Returns:
        List of actionable recommendations
    """
    
    report = generate_sanitization_report()
    recommendations = []
    
    # Coverage recommendations
    coverage = report['overview']['sanitization_coverage']
    if coverage < 50:
        recommendations.append({
            'priority': 'high',
            'type': 'coverage',
            'message': f"Only {coverage:.1f}% of entries have been sanitized. Run batch sanitization to improve RAG quality.",
            'action': "python manage.py sanitize_ocr_text"
        })
    elif coverage < 90:
        recommendations.append({
            'priority': 'medium',
            'type': 'coverage',
            'message': f"{coverage:.1f}% coverage is good, but consider processing remaining entries for completeness.",
            'action': "python manage.py sanitize_ocr_text --min-confidence 0.5"
        })
    
    # Quality recommendations
    avg_confidence = report['confidence_statistics'].get('avg_confidence', 0)
    if avg_confidence < 0.6:
        recommendations.append({
            'priority': 'high',
            'type': 'quality',
            'message': f"Average confidence ({avg_confidence:.2f}) is low. Consider re-scanning PDFs with higher quality settings.",
            'action': "Review PDF scanning parameters or source quality"
        })
    
    # Distribution recommendations
    poor_quality = report['confidence_distribution']['poor']
    total_sanitized = report['overview']['sanitized_entries']
    
    if poor_quality > total_sanitized * 0.2:  # More than 20% poor quality
        recommendations.append({
            'priority': 'medium',
            'type': 'quality',
            'message': f"{poor_quality} entries have poor OCR quality. Consider manual review or re-OCR.",
            'action': "python manage.py sanitize_ocr_text --force --min-confidence 0.0"
        })
    
    # Configuration recommendations
    config_usage = {item['ocr_config_used']: item['count'] for item in report['ocr_config_usage']}
    
    if config_usage.get('fallback', 0) > total_sanitized * 0.1:
        recommendations.append({
            'priority': 'medium',
            'type': 'configuration',
            'message': "Many entries required fallback OCR configuration. Consider improving image preprocessing.",
            'action': "Review PDF image quality and preprocessing pipeline"
        })
    
    return recommendations
