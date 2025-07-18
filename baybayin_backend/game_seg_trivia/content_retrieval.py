from baybayin_wiki.models import WikiArticle, WikiGlossary
from django.db.models import Q

def get_random_fact():
    # Example: get a random article or glossary entry
    import random
    articles = list(WikiArticle.objects.all())
    glossary = list(WikiGlossary.objects.all())
    all_facts = articles + glossary
    return random.choice(all_facts) if all_facts else None

def get_adaptive_fact(user_profile):
    # TODO: Use user_profile to select a fact based on weaknesses
    return get_random_fact()

def retrieve_relevant_facts(query, top_k=3):
    """
    Retrieve top_k relevant facts based on a query string.
    This is a simple keyword search; you can replace with vector search for better results.
    """
    articles = WikiArticle.objects.filter(
        Q(title__icontains=query) | Q(summary__icontains=query)
    )[:top_k]
    glossaries = WikiGlossary.objects.filter(
        Q(term__icontains=query) | Q(definition__icontains=query)
    )[:top_k]
    # Combine and return as a list
    return list(articles) + list(glossaries)