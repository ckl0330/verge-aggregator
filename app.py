from flask import Flask, render_template
import feedparser
from datetime import datetime
import time

app = Flask(__name__)

# Global cache to store articles
CACHED_ARTICLES = []
LAST_SCRAPE_TIME = None
CACHE_DURATION = 3600  # Cache for 1 hour

def fetch_verge_articles():
    """
    Fetch articles from The Verge using RSS feeds.
    Fast, reliable, and returns real articles with proper titles.
    """
    articles = []
    
    # The Verge RSS feeds by category
    rss_feeds = [
        'https://www.theverge.com/rss/index.xml',          # Main feed
        'https://www.theverge.com/rss/tech/index.xml',     # Tech
        'https://www.theverge.com/rss/reviews/index.xml',  # Reviews
        'https://www.theverge.com/rss/science/index.xml',  # Science
        'https://www.theverge.com/rss/policy/index.xml',   # Policy
        'https://www.theverge.com/rss/creators/index.xml', # Creators
    ]
    
    print("Fetching articles from The Verge RSS feeds...")
    
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                try:
                    # Parse publication date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        continue
                    
                    # Filter: Only articles from January 1, 2022 onwards
                    if pub_date >= datetime(2022, 1, 1):
                        title = entry.title.strip() if hasattr(entry, 'title') else None
                        url = entry.link if hasattr(entry, 'link') else None
                        
                        # Validate data
                        if title and url and len(title) > 10:
                            articles.append({
                                'title': title,
                                'url': url,
                                'date': pub_date
                            })
                            
                except Exception as e:
                    continue
            
            # Be respectful to the server
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {str(e)}")
            continue
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_articles = []
    for article in articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    # Sort by date (newest first)
    unique_articles.sort(key=lambda x: x['date'], reverse=True)
    
    print(f"✓ Successfully fetched {len(unique_articles)} unique articles")
    return unique_articles

def get_articles():
    """Get articles with smart caching"""
    global CACHED_ARTICLES, LAST_SCRAPE_TIME
    
    current_time = time.time()
    
    # Return cached articles if still fresh
    if CACHED_ARTICLES and LAST_SCRAPE_TIME:
        cache_age = current_time - LAST_SCRAPE_TIME
        if cache_age < CACHE_DURATION:
            print(f"Returning cached articles (age: {int(cache_age)}s)")
            return CACHED_ARTICLES
    
    # Fetch fresh articles
    CACHED_ARTICLES = fetch_verge_articles()
    LAST_SCRAPE_TIME = current_time
    
    return CACHED_ARTICLES

@app.route('/')
def index():
    """Main page displaying all articles"""
    articles = get_articles()
    return render_template('index.html', 
                         articles=articles, 
                         total=len(articles))

if __name__ == '__main__':
    # Perform initial fetch on startup
    print("=" * 60)
    print("The Verge Article Aggregator - Starting Up")
    print("=" * 60)
    get_articles()
    print("=" * 60)
    print("Server ready! Visit: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)