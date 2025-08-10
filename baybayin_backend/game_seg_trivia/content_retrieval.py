# baybayin_backend/game_seg_trivia/content_retrieval.py
from baybayin_wiki.models import WikiArticle, WikiGlossary
from django.db.models import Q
import random
from django.core.cache import cache

def get_random_fact(exclude_ids=None):
    """Get a random fact with optional exclusion"""
    articles = WikiArticle.objects.all()
    glossary = WikiGlossary.objects.all()
    
    if exclude_ids:
        articles = articles.exclude(id__in=exclude_ids)
        glossary = glossary.exclude(id__in=exclude_ids)
    
    all_facts = list(articles) + list(glossary)
    return random.choice(all_facts) if all_facts else None

def get_adaptive_fact(user_profile, exclude_ids=None):
    """Retrieve a fact based on user's weaknesses with exclusion"""
    # Get topics the user struggles with
    weak_topics = user_profile.top_weaknesses or []
    
    # Prioritize weak topics
    if weak_topics:
        articles = WikiArticle.objects.filter(
            Q(title__in=weak_topics) | Q(summary__icontains=weak_topics[0])
        )
        
        glossaries = WikiGlossary.objects.filter(
            Q(term__in=weak_topics) | Q(definition__icontains=weak_topics[0])
        )
        
        if exclude_ids:
            articles = articles.exclude(id__in=exclude_ids)
            glossaries = glossaries.exclude(id__in=exclude_ids)
            
        facts = list(articles) + list(glossaries)
        if facts:
            return random.choice(facts)
    
    # Fallback to random fact
    return get_random_fact(exclude_ids)

def retrieve_relevant_facts(query, user_profile=None, top_k=3, exclude_ids=None):
    """Retrieve facts with adaptive learning and exclusion support"""
    # Base query set with exclusion
    articles = WikiArticle.objects.filter(
        Q(title__icontains=query) | Q(summary__icontains=query)
    )
    
    glossaries = WikiGlossary.objects.filter(
        Q(term__icontains=query) | Q(definition__icontains=query)
    )
    
    if exclude_ids:
        articles = articles.exclude(id__in=exclude_ids)
        glossaries = glossaries.exclude(id__in=exclude_ids)
    
    # Combine results
    facts = list(articles) + list(glossaries)
    
    # If user profile available, prioritize weak areas
    if user_profile and user_profile.top_weaknesses:
        weak_facts = [
            f for f in facts 
            if any(
                topic in getattr(f, 'title', '') or topic in getattr(f, 'term', '')
                for topic in user_profile.top_weaknesses
            )
        ]
        other_facts = [f for f in facts if f not in weak_facts]
        facts = weak_facts + other_facts
    
    # Ensure diversity
    unique_facts = []
    seen_titles = set()
    for fact in facts:
        title = getattr(fact, 'title', None) or getattr(fact, 'term', None)
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_facts.append(fact)
    
    return unique_facts[:top_k]