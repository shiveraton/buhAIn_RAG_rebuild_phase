import os
import random
import hashlib
import numpy as np
from django.db.models import Q
from django.core.cache import cache

from baybayin_codex.models import CodexArticle, CodexGlossary
from baybayin_codex_pdf.models import PDFCodexEntry
from game_seg_trivia.retrieval_service import get_embedding_model

# PHASE 8: 100% PDF MIGRATION
# Trivia now uses exclusively PDF-based facts for better quality
# Web articles (CodexArticle/CodexGlossary) remain for UI browsing only
USE_PDF_RATIO = float(os.getenv("USE_PDF_RATIO", "1.0"))
CACHE_TIMEOUT = 300  # seconds

# -----------------------------
# Utilities
# -----------------------------
def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two embedding vectors"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm_v1 * norm_v2))


def compute_identifier(fact):
    """Create a unique identifier for deduplication"""
    text = getattr(fact, "text", None) or getattr(fact, "title", None) or getattr(fact, "term", "")
    return hashlib.md5(text.encode("utf-8")).hexdigest() if text else None


# -----------------------------
# PDF Retrieval
# -----------------------------
def retrieve_from_pdf(query_embedding, top_k=5):
    """Retrieve facts from PDFCodexEntry using cosine similarity"""
    cache_key = f"pdf_results_{hashlib.md5(str(query_embedding).encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached[:top_k]

    entries = PDFCodexEntry.objects.all()
    scored = []

    for entry in entries:
        score = cosine_similarity(query_embedding, entry.embedding)
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [e for s, e in scored[:top_k]]
    cache.set(cache_key, results, CACHE_TIMEOUT)
    return results


# -----------------------------
# Web Retrieval (legacy)
# -----------------------------
def retrieve_from_web(query_embedding=None, top_k=5):
    """Retrieve facts from legacy CodexArticle/CodexGlossary"""
    articles = list(CodexArticle.objects.all()[:top_k])
    glossaries = list(CodexGlossary.objects.all()[:top_k])
    combined = articles + glossaries
    random.shuffle(combined)
    return combined[:top_k]


# -----------------------------
# Random / Adaptive Fact Selection
# -----------------------------
def get_random_fact(exclude_ids=None):
    """Get a random fact from web sources"""
    articles = CodexArticle.objects.all()
    glossaries = CodexGlossary.objects.all()
    if exclude_ids:
        articles = articles.exclude(id__in=exclude_ids)
        glossaries = glossaries.exclude(id__in=exclude_ids)
    all_facts = list(articles) + list(glossaries)
    return random.choice(all_facts) if all_facts else None


def get_adaptive_fact(user_profile, exclude_ids=None, use_pdf=False):
    """Retrieve fact based on user weaknesses"""
    weak_topics = user_profile.top_weaknesses or []
    if not weak_topics:
        return get_random_fact(exclude_ids)

    if use_pdf:
        # PDF-aware adaptive selection
        entries = PDFCodexEntry.objects.filter(
            Q(text__icontains=weak_topics[0])
        )
    else:
        entries = CodexArticle.objects.filter(
            Q(title__in=weak_topics) | Q(summary__icontains=weak_topics[0])
        )
        glossaries = CodexGlossary.objects.filter(
            Q(term__in=weak_topics) | Q(definition__icontains=weak_topics[0])
        )
        entries = list(entries) + list(glossaries)

    if exclude_ids:
        entries = [e for e in entries if getattr(e, "id", None) not in exclude_ids]

    return random.choice(entries) if entries else get_random_fact(exclude_ids)


# -----------------------------
# Main Retrieval
# -----------------------------
def retrieve_relevant_facts(query, user_profile=None, top_k=3, exclude_ids=None, use_pdf_ratio=None):
    """
    Retrieve facts using shadow mode (PDF + Web)
    """
    pdf_ratio = use_pdf_ratio if use_pdf_ratio is not None else USE_PDF_RATIO
    pdf_count = int(top_k * pdf_ratio)
    web_count = top_k - pdf_count

    # Generate query embedding for PDF
    model = get_embedding_model()
    query_embedding = model.encode([query])[0].tolist()

    # Retrieve PDF and Web facts
    pdf_results = retrieve_from_pdf(query_embedding, top_k=pdf_count) if pdf_count > 0 else []
    web_results = retrieve_from_web(query_embedding, top_k=web_count) if web_count > 0 else []

    combined_results = pdf_results + web_results

    # Exclusion filter
    if exclude_ids:
        combined_results = [f for f in combined_results if getattr(f, "id", None) not in exclude_ids]

    # Adaptive prioritization
    if user_profile and user_profile.top_weaknesses:
        weak_facts = [
            f for f in combined_results
            if any(
                topic.lower() in (getattr(f, "text", "") or getattr(f, "title", "") or getattr(f, "term", "")).lower()
                for topic in user_profile.top_weaknesses
            )
        ]
        other_facts = [f for f in combined_results if f not in weak_facts]
        combined_results = weak_facts + other_facts

    # Deduplicate facts
    unique_facts = []
    seen_identifiers = set()
    for fact in combined_results:
        identifier = compute_identifier(fact)
        if identifier and identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
            unique_facts.append(fact)

    return unique_facts[:top_k]