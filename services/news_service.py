import feedparser
import ssl

# Fix for potential SSL issues with some feeds
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

RSS_URL = "https://techcrunch.com/feed/"

def fetch_techcrunch_news(limit=10):
    """
    Fetches the latest news from TechCrunch RSS feed.
    Returns a list of dictionaries with title, link, and summary (from RSS).
    """
    feed = feedparser.parse(RSS_URL)
    articles = []
    
    for entry in feed.entries[:limit]:
        # Minimal cleanup
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "summary": entry.summary,  # This might be HTML
            "content": entry.content[0].value if 'content' in entry else entry.description
        })
        
    return articles
