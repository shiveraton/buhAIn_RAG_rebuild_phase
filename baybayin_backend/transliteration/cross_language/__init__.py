# lazy import to avoid startup issues with ML libraries
def get_cross_transliterator():
    """Lazy import of cross-transliteration functionality"""
    try:
        from .cross_transliterator import cross_transliterate_en_to_baybayin
        return cross_transliterate_en_to_baybayin
    except ImportError as e:
        return None
