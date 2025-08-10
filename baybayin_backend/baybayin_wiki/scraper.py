import requests
from bs4 import BeautifulSoup

# --- Wikipedia Scraper Section ---

def scrape_wikipedia_articles(topics):
    """
    Scrape Wikipedia for given topics.
    Returns a list of dicts with 'title', 'summary', 'content', etc.
    """
    results = []
    WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
    for topic in topics:
        try:
            resp = requests.get(WIKI_API_URL.format(topic.replace(' ', '_')))
            if resp.status_code == 200:
                data = resp.json()
                results.append({
                    'title': data.get('title'),
                    'summary': data.get('extract'),
                    'content': data.get('extract_html'),
                    'source': 'wikipedia',
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
                })
        except Exception as e:
            print(f"Error scraping Wikipedia topic '{topic}': {e}")
    return results

# --- Cultural Site Scraper Section ---

def scrape_cultural_site(url, article_selector, title_selector, content_selector):
    """
    Scrape a cultural site for articles.
    Returns a list of dicts with 'title', 'content', etc.
    """
    articles = []
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for article in soup.select(article_selector):
                title_elem = article.select_one(title_selector)
                content_elem = article.select_one(content_selector)
                title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                content = content_elem.get_text(strip=True) if content_elem else ""
                articles.append({
                    'title': title,
                    'content': content,
                    'source': url,
                    'url': url
                })
    except Exception as e:
        print(f"Error scraping cultural site '{url}': {e}")
    return articles

# --- Unified Scraper Interface ---

def scrape_all(wiki_topics, cultural_sites):
    """
    Scrape both Wikipedia and cultural sites.
    wiki_topics: list of Wikipedia topics (str)
    cultural_sites: list of dicts with keys: url, article_selector, title_selector, content_selector
    Returns: list of all articles found
    """
    all_articles = []
    # Wikipedia
    wiki_articles = scrape_wikipedia_articles(wiki_topics)
    all_articles.extend(wiki_articles)
    # Cultural sites
    for site in cultural_sites:
        site_articles = scrape_cultural_site(
            site['url'],
            site['article_selector'],
            site['title_selector'],
            site['content_selector']
        )
        all_articles.extend(site_articles)
    return all_articles

# --- Example Usage ---

if __name__ == "__main__":
    # Example Wikipedia topics
    wiki_topics = [
        "Baybayin",
        "Prehistory of the Philippines",
        "Philippine scripts"
    ]
    # Example cultural sites (update selectors as needed for real sites)
    cultural_sites = [
        {
            'url': 'https://www.nationalmuseum.gov.ph/exhibitions/anthropology/baybayin/',
            'article_selector': '.article-list .article',
            'title_selector': '.article-title',
            'content_selector': '.article-content'
        },
        {
            'url': 'https://narrastudio.com/blogs/journal/baybayin-the-ancient-filipino-script-lives-on',
            'article_selector': '.post',
            'title_selector': '.post-title',
            'content_selector': '.post-content'
        },
        {
            'url': 'https://blog.kabuay.com/about',
            'article_selector': 'article',
            'title_selector': 'h1.entry-title',
            'content_selector': 'div.entry-content'
        },
        {
            'url': 'http://paulmorrow.ca/bayeng1.htm',
            'article_selector': 'body',
            'title_selector': 'h1',
            'content_selector': 'body'
        },
        {
            'url': 'https://www.ust.edu.ph/the-baybayin-documents/?utm_source=chatgpt.com',
            'article_selector': 'article',
            'title_selector': 'h1',
            'content_selector': 'div.elementor-widget-container'
        }
        # Add more sites as needed
    ]
    articles = scrape_all(wiki_topics, cultural_sites)
    print(f"Scraped {len(articles)} articles.")
    for art in articles:
        print(f"- {art['title']} ({art['source']})")