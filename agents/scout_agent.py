import requests
import sys
import os
import json
import time
import feedparser
from datetime import datetime
from pytrends.request import TrendReq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    YOUTUBE_API_KEY,
    NEWS_API_KEY,
    FASHION_KEYWORDS,
    BEAUTY_KEYWORDS,
    FASHION_SUBREDDITS,
    BEAUTY_SUBREDDITS,
    DATA_DIR
)

# 1. YOUTUBE SHORTS

def fetch_youtube_shorts_trends(keywords, max_results=10):
    results = []

    for keyword in keywords:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": keyword + " shorts",
            "type": "video",
            "videoDuration": "short",
            "order": "date",
            "maxResults": max_results,
            "regionCode": "IN",
            "relevanceLanguage": "en",
            "key": YOUTUBE_API_KEY
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                results.append({
                    "source": "youtube_shorts",
                    "keyword": keyword,
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "video_id": item["id"].get("videoId", ""),
                    "description": item["snippet"]["description"][:200],
                    "fetched_at": datetime.now().isoformat()
                })

            print(f"  [YouTube] '{keyword}' -> {len(data.get('items', []))} results")

        except requests.exceptions.HTTPError as e:
            print(f"  [YouTube] HTTP error for '{keyword}': {e}")
        except Exception as e:
            print(f"  [YouTube] Error for '{keyword}': {e}")

    return results


# 2. GOOGLE TRENDS — INTEREST OVER TIME


def fetch_google_trends(keywords, timeframe="now 7-d", geo="IN"):
    pytrends = TrendReq(hl="en-IN", tz=330)
    results = []
    chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

    for chunk in chunks:
        try:
            pytrends.build_payload(chunk, timeframe=timeframe, geo=geo)
            interest_df = pytrends.interest_over_time()

            if not interest_df.empty:
                for keyword in chunk:
                    if keyword in interest_df.columns:
                        recent_avg = interest_df[keyword].tail(3).mean()
                        overall_avg = interest_df[keyword].mean()
                        velocity = recent_avg - overall_avg
                        peak_value = interest_df[keyword].max()

                        results.append({
                            "source": "google_trends",
                            "keyword": keyword,
                            "recent_avg": round(float(recent_avg), 2),
                            "overall_avg": round(float(overall_avg), 2),
                            "velocity": round(float(velocity), 2),
                            "peak_value": round(float(peak_value), 2),
                            "rising": bool(velocity > 5),
                            "geo": geo,
                            "timeframe": timeframe,
                            "fetched_at": datetime.now().isoformat()
                        })

            print(f"  [Google Trends] {chunk} -> fetched")
            time.sleep(1)

        except Exception as e:
            print(f"  [Google Trends] Error for {chunk}: {e}")

    return results


# 3. GOOGLE TRENDS — RISING QUERIES


def fetch_google_trends_rising_queries(keywords, geo="IN"):
    pytrends = TrendReq(hl="en-IN", tz=330)
    results = []
    chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

    for chunk in chunks:
        try:
            pytrends.build_payload(chunk, timeframe="today 1-m", geo=geo)
            related = pytrends.related_queries()

            for keyword in chunk:
                if keyword in related and related[keyword]["rising"] is not None:
                    rising_df = related[keyword]["rising"]
                    for _, row in rising_df.iterrows():
                        results.append({
                            "source": "google_trends_rising",
                            "parent_keyword": keyword,
                            "rising_query": row["query"],
                            "value": row["value"],
                            "fetched_at": datetime.now().isoformat()
                        })

            print(f"  [Google Rising] {chunk} -> fetched")
            time.sleep(1)

        except Exception as e:
            print(f"  [Google Rising] Error for {chunk}: {e}")

    return results



# 4. NEWSAPI — FASHION & BEAUTY ARTICLES

def fetch_news_articles(keywords):
    if not NEWS_API_KEY:
        print("  [NewsAPI] Skipping — NEWS_API_KEY not set")
        return []

    results = []

    # Separate queries for fashion and beauty
    queries = [
        ("fashion", "Indian fashion trends 2026"),
        ("beauty", "Indian beauty trends makeup skincare 2026"),
        ("fashion_india", "kurta co-ord set ethnic wear India"),
        ("beauty_india", "glass skin lip liner beauty India"),
    ]

    for category, query in queries:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": NEWS_API_KEY
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            articles = data.get("articles", [])
            all_keywords = FASHION_KEYWORDS + BEAUTY_KEYWORDS

            for article in articles:
                matched_keywords = []
                title_desc = (
                    str(article.get("title", "")) + " " +
                    str(article.get("description", ""))
                ).lower()

                for kw in all_keywords:
                    if kw.lower() in title_desc:
                        matched_keywords.append(kw)

                results.append({
                    "source": "newsapi",
                    "category": category,
                    "title": article.get("title", ""),
                    "description": str(article.get("description", ""))[:300],
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "source_name": article.get("source", {}).get("name", ""),
                    "matched_keywords": matched_keywords,
                    "fetched_at": datetime.now().isoformat()
                })

            print(f"  [NewsAPI] '{category}' -> {len(articles)} articles fetched")
            time.sleep(0.5)

        except requests.exceptions.HTTPError as e:
            print(f"  [NewsAPI] HTTP error for '{category}': {e}")
        except Exception as e:
            print(f"  [NewsAPI] Error for '{category}': {e}")

    return results


# 5. RSS FEEDS — INDIAN FASHION & BEAUTY


def fetch_rss_feeds():
    feeds = [
        {
            "name": "Vogue India",
            "url": "https://feeds.feedburner.com/VogueIndia",
            "category": "fashion"
        },
        {
            "name": "Femina India",
            "url": "https://www.femina.in/feed",
            "category": "fashion_beauty"
        },
        {
            "name": "Harper's Bazaar India",
            "url": "https://www.harpersbazaar.in/feed",
            "category": "fashion"
        },
        {
            "name": "Pinkvilla Fashion",
            "url": "https://www.pinkvilla.com/fashion/rss",
            "category": "fashion"
        },
        {
            "name": "Pinkvilla Beauty",
            "url": "https://www.pinkvilla.com/beauty/rss",
            "category": "beauty"
        },
        {
            "name": "BeBeautiful",
            "url": "https://www.bebeautiful.in/feed",
            "category": "beauty"
        },
        {
            "name": "Popxo Fashion",
            "url": "https://www.popxo.com/category/fashion/feed",
            "category": "fashion"
        },
        {
            "name": "Popxo Beauty",
            "url": "https://www.popxo.com/category/beauty/feed",
            "category": "beauty"
        },
        {
            "name": "Hauterfly",
            "url": "https://www.hauterfly.com/feed",
            "category": "fashion_beauty"
        },
        {
            "name": "Lifestyle Asia India",
            "url": "https://www.lifestyleasia.com/ind/feed",
            "category": "fashion_beauty"
        },
    ]

    results = []
    all_keywords = FASHION_KEYWORDS + BEAUTY_KEYWORDS

    for feed_info in feeds:
        try:
            # feedparser handles all RSS/Atom formats automatically
            feed = feedparser.parse(feed_info["url"])

            count = 0
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:300]
                published = entry.get("published", "")
                link = entry.get("link", "")

                # Skip empty entries
                if not title:
                    continue

                # Match keywords
                matched_keywords = []
                content = (title + " " + summary).lower()
                for kw in all_keywords:
                    if kw.lower() in content:
                        matched_keywords.append(kw)

                results.append({
                    "source": "rss_feed",
                    "feed_name": feed_info["name"],
                    "category": feed_info["category"],
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "published_at": published,
                    "matched_keywords": matched_keywords,
                    "fetched_at": datetime.now().isoformat()
                })
                count += 1

            print(f"  [RSS] {feed_info['name']:<25} -> {count} articles")

        except Exception as e:
            print(f"  [RSS] Error for {feed_info['name']}: {e}")

    return results


# MAIN RUNNER

def run_scout(industry="both"):
    print("\n" + "="*50)
    print("  SCOUT AGENT RUNNING")
    print("="*50)

    if industry == "fashion":
        keywords = FASHION_KEYWORDS
    elif industry == "beauty":
        keywords = BEAUTY_KEYWORDS
    else:
        keywords = FASHION_KEYWORDS + BEAUTY_KEYWORDS

    all_signals = []

    # 1. YouTube Shorts
    print("\n[1/5] Fetching YouTube Shorts...")
    youtube_data = fetch_youtube_shorts_trends(keywords[:5], max_results=10)
    all_signals.extend(youtube_data)
    print(f"  Total: {len(youtube_data)} signals")

    # 2. Google Trends interest
    print("\n[2/5] Fetching Google Trends (interest over time)...")
    trends_data = fetch_google_trends(keywords, timeframe="now 7-d", geo="IN")
    all_signals.extend(trends_data)
    print(f"  Total: {len(trends_data)} signals")

    # 3. Google Trends rising queries
    print("\n[3/5] Fetching Google Trends (rising queries)...")
    rising_data = fetch_google_trends_rising_queries(keywords[:5], geo="IN")
    all_signals.extend(rising_data)
    print(f"  Total: {len(rising_data)} signals")

    # 4. NewsAPI articles
    print("\n[4/5] Fetching news articles...")
    news_data = fetch_news_articles(keywords)
    all_signals.extend(news_data)
    print(f"  Total: {len(news_data)} signals")

    # 5. RSS Feeds
    print("\n[5/5] Fetching RSS feeds from Indian publications...")
    rss_data = fetch_rss_feeds()
    all_signals.extend(rss_data)
    print(f"  Total: {len(rss_data)} signals")

    print("\n" + "="*50)
    print(f"  SCOUT COMPLETE — {len(all_signals)} total signals collected")
    print("="*50)

    return all_signals


# SUMMARY PRINTER

def print_summary(signals):
    print("\n--- SIGNAL SUMMARY ---\n")

    sources = [
        "youtube_shorts",
        "google_trends",
        "google_trends_rising",
        "newsapi",
        "rss_feed"
    ]

    for source in sources:
        items = [s for s in signals if s["source"] == source]
        print(f"  {source:<25} : {len(items)} signals")

    print("\nTop rising Google Trends keywords:")
    trends = [s for s in signals if s["source"] == "google_trends"]
    for item in sorted(trends, key=lambda x: x["velocity"], reverse=True)[:5]:
        status = "RISING" if item["rising"] else "stable"
        print(f"  [{status}] {item['keyword']:<25} velocity: {item['velocity']}")

    print("\nTop rising queries:")
    rising = [s for s in signals if s["source"] == "google_trends_rising"]
    for item in sorted(rising, key=lambda x: x["value"], reverse=True)[:5]:
        print(f"  '{item['rising_query']}' from '{item['parent_keyword']}' — value: {item['value']}")

    print("\nLatest news articles:")
    news = [s for s in signals if s["source"] == "newsapi"]
    for item in news[:3]:
        print(f"  [{item['source_name']}] {item['title'][:70]}")
        if item["matched_keywords"]:
            print(f"    Matched: {item['matched_keywords']}")

    print("\nLatest RSS articles:")
    rss = [s for s in signals if s["source"] == "rss_feed"]
    for item in rss[:3]:
        print(f"  [{item['feed_name']}] {item['title'][:70]}")
        if item["matched_keywords"]:
            print(f"    Matched: {item['matched_keywords']}")


# ENTRY POINT

if __name__ == "__main__":
    signals = run_scout(industry="both")
    print_summary(signals)

    # Save to file
    os.makedirs(DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(DATA_DIR, f"signals_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)

    print(f"\nSignals saved to: {filepath}")