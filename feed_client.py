import re
import feedparser


def fetch_feed(feed_url, max_articles=5):
    parsed = feedparser.parse(feed_url)
    articles = []
    for entry in parsed.entries[:max_articles]:
        title = entry.get('title', '').strip()
        summary = re.sub(r'<[^>]+>', '', entry.get('summary', entry.get('description', ''))).strip()
        summary = summary[:300] if summary else ''
        articles.append({'title': title, 'summary': summary, 'link': entry.get('link', '')})
    return articles, parsed.feed.get('title', feed_url)


def fetch_all_feeds(feeds, max_per_feed=5):
    results, errors = [], []
    for feed in feeds:
        try:
            articles, feed_title = fetch_feed(feed['url'], max_per_feed)
            name = feed.get('name') or feed_title
            if articles:
                results.append((name, articles))
        except Exception as e:
            errors.append(str(e))
    return results, errors
