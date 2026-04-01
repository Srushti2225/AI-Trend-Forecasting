import requests
import sys
import os
import json
import time
import re
import feedparser
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    YOUTUBE_API_KEY,
    NEWS_API_KEY,
    FASHION_KEYWORDS,
    BEAUTY_KEYWORDS,
    FASHION_SEED_TOPICS,
    BEAUTY_SEED_TOPICS,
    ALL_KEYWORDS,
    DATA_DIR
)



# NOISE FILTER

NOISE_PATTERNS = [
    r'\w+shorts\w*',      # trendingshorts, viralshorts etc
    r'\w+feed\w*',        # shortsfeed etc
    r'\w+reels\w*',       # trendingreels etc
    r'\w+viral\w*',       # goingviral etc
    r'[a-z]+makeup[a-z]+', # asokamakeup etc
    r'[a-z]+fashion[a-z]+', # indianfashion concatenated
    r'\w+india[a-z]+',    # makeupindia concatenated
]


# WIKIPEDIA PAGES TO TRACK

WIKIPEDIA_PAGES = {
    "fashion_aesthetics": [
        "Quiet luxury", "Cottagecore", "Dark academia", "Y2K fashion",
        "Mob wife aesthetic", "Old money aesthetic", "Balletcore",
        "Gorpcore", "Coastal grandmother", "Normcore",
        "Dopamine dressing", "Barbiecore", "Clean girl aesthetic",
    ],
    "indian_fashion": [
        "Kurta", "Lehenga", "Salwar kameez", "Saree",
        "Indo-western clothing", "Churidar", "Anarkali suit",
        "Bandhani", "Phulkari", "Ajrakh", "Fashion in India",
    ],
    "beauty_trends": [
        "Glass skin", "Skinimalism", "K-beauty", "Slugging (skincare)",
        "Double cleansing", "Skin care", "Korean beauty",
        "Contouring", "Lip liner", "Eyebrow shaping",
    ],
    "general_fashion": [
        "Fast fashion", "Sustainable fashion", "Streetwear",
        "Athleisure", "Capsule wardrobe", "Vintage clothing",
    ]
}



# WIKIPEDIA — PAGE VIEW VELOCITY

def fetch_wikipedia_pageviews(days_back=30):
    results = []
    headers = {
        "User-Agent": "TrendForecaster/1.0 (academic-capstone-project)"
    }

    end = datetime.now()
    start = end - timedelta(days=days_back)
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    all_pages = []
    for category, pages in WIKIPEDIA_PAGES.items():
        for page in pages:
            all_pages.append((page, category))

    print(f"  [Wikipedia] Checking {len(all_pages)} pages...")

    for page_title, category in all_pages:
        try:
            page_encoded = page_title.replace(" ", "_")
            url = (
                f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
                f"en.wikipedia/all-access/all-agents/{page_encoded}/daily/"
                f"{start_str}/{end_str}"
            )

            response = requests.get(url, headers=headers, timeout=8)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                if items:
                    views_list = [i.get("views", 0) for i in items]
                    total_views = sum(views_list)

                    recent = views_list[-7:] if len(views_list) >= 7 else views_list
                    older = views_list[:-7] if len(views_list) > 7 else views_list

                    recent_avg = sum(recent) / len(recent) if recent else 0
                    older_avg = sum(older) / len(older) if older else 0
                    velocity = recent_avg - older_avg

                    matched = [
                        kw for kw in ALL_KEYWORDS
                        if kw.lower() in page_title.lower()
                        or page_title.lower() in kw.lower()
                    ]

                    results.append({
                        "source": "wikipedia_pageviews",
                        "page": page_title,
                        "category": category,
                        "total_views": total_views,
                        "recent_avg_daily": round(recent_avg, 1),
                        "older_avg_daily": round(older_avg, 1),
                        "velocity": round(velocity, 2),
                        "peak_views": max(views_list),
                        "rising": bool(velocity > 50),
                        "matched_keywords": matched,
                        "fetched_at": datetime.now().isoformat()
                    })

                    status = "RISING" if velocity > 50 else "stable"
                    print(
                        f"  [Wikipedia] {page_title:<32} "
                        f"avg: {round(recent_avg):>6}/day  "
                        f"velocity: {velocity:>8.1f}  [{status}]"
                    )

            elif response.status_code == 404:
                print(f"  [Wikipedia] '{page_title}' — no page found")

            time.sleep(0.2)

        except Exception as e:
            print(f"  [Wikipedia] Error for '{page_title}': {e}")

    rising = [r for r in results if r["rising"]]
    print(f"  [Wikipedia] {len(results)} pages tracked | {len(rising)} rising")

    return results


def fetch_wikipedia_top_trending():
    results = []
    headers = {
        "User-Agent": "TrendForecaster/1.0 (academic-capstone-project)"
    }

    fashion_beauty_words = [
        "fashion", "style", "beauty", "makeup", "skin", "hair",
        "dress", "outfit", "aesthetic", "trend", "clothing",
        "kurta", "saree", "lehenga", "ethnic", "western",
        "cosmetic", "skincare", "lipstick", "blush", "cottagecore",
        "luxury", "vintage", "streetwear", "athleisure"
    ]

    date = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
        f"en.wikipedia/all-access/{date}"
    )

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("items", [{}])[0].get("articles", [])

            print(f"  [Wikipedia Top] Scanning top {len(articles)} trending pages...")

            for article in articles[:300]:
                title = article.get("article", "").replace("_", " ")
                views = article.get("views", 0)
                rank = article.get("rank", 0)

                if any(title.startswith(p) for p in [
                    "Special:", "Wikipedia:", "Portal:",
                    "Main Page", "File:", "Help:", "Talk:"
                ]):
                    continue

                if any(kw in title.lower() for kw in fashion_beauty_words):
                    results.append({
                        "source": "wikipedia_top_trending",
                        "page": title,
                        "views_today": views,
                        "global_rank": rank,
                        "fetched_at": datetime.now().isoformat()
                    })

            print(f"  [Wikipedia Top] {len(results)} fashion/beauty pages found")

    except Exception as e:
        print(f"  [Wikipedia Top] Error: {e}")

    return results

def is_noise(phrase):
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, phrase.lower()):
            return True
    if any(len(w) > 14 for w in phrase.split()):
        return True
    return False



# 1. YOUTUBE SHORTS — BROAD FETCH

def fetch_youtube_shorts(seed_topics, max_results=15):
    results = []

    for topic in seed_topics:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": topic,
            "type": "video",
            "videoDuration": "short",
            "order": "viewCount",
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
                    "seed_topic": topic,
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "video_id": item["id"].get("videoId", ""),
                    "description": item["snippet"]["description"][:200],
                    "fetched_at": datetime.now().isoformat()
                })

            print(f"  [YouTube] '{topic}' -> {len(data.get('items', []))} videos")

        except Exception as e:
            print(f"  [YouTube] Error for '{topic}': {e}")

    return results



# 2. GOOGLE TRENDS — CURATED KEYWORDS
# Scores all known trend keywords by velocity

def fetch_google_trends_velocity(keywords, geo="IN"):
    pytrends = TrendReq(hl="en-IN", tz=330)
    results = []
    chunks = [keywords[i:i + 5] for i in range(0, len(keywords), 5)]

    for chunk in chunks:
        try:
            pytrends.build_payload(chunk, timeframe="now 7-d", geo=geo)
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
                            "fetched_at": datetime.now().isoformat()
                        })

            print(f"  [Google Trends] Scored: {chunk}")
            time.sleep(1)

        except Exception as e:
            print(f"  [Google Trends] Error: {e}")

    return results


def fetch_google_trends_rising_queries(keywords, geo="IN"):
    pytrends = TrendReq(hl="en-IN", tz=330)
    results = []
    chunks = [keywords[i:i + 5] for i in range(0, len(keywords), 5)]

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
            print(f"  [Google Rising] Error: {e}")

    return results



# 3. NEWSAPI — CHECK KEYWORD MENTIONS

def fetch_news_articles(keywords):
    if not NEWS_API_KEY:
        print("  [NewsAPI] Skipping — NEWS_API_KEY not set")
        return []

    results = []

    queries = [
        "indian fashion trends 2026",
        "india beauty makeup skincare",
        "bollywood fashion outfit style",
        "gen z india fashion beauty"
    ]

    for query in queries:
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

            for article in articles:
                title = str(article.get("title", ""))
                description = str(article.get("description", ""))[:300]

                # Check which curated keywords appear in this article
                matched = [
                    kw for kw in keywords
                    if kw.lower() in (title + " " + description).lower()
                ]

                results.append({
                    "source": "newsapi",
                    "title": title,
                    "description": description,
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "source_name": article.get("source", {}).get("name", ""),
                    "matched_keywords": matched,
                    "fetched_at": datetime.now().isoformat()
                })

            print(f"  [NewsAPI] '{query}' -> {len(articles)} articles")
            time.sleep(0.5)

        except Exception as e:
            print(f"  [NewsAPI] Error: {e}")

    return results



# 4. RSS FEEDS

def fetch_rss_feeds(keywords):
    feeds = [
        {"name": "Vogue India",       "url": "https://feeds.feedburner.com/VogueIndia"},
        {"name": "Femina",            "url": "https://www.femina.in/feed"},
        {"name": "Harper's Bazaar",   "url": "https://www.harpersbazaar.in/feed"},
        {"name": "Pinkvilla Fashion", "url": "https://www.pinkvilla.com/fashion/rss"},
        {"name": "Pinkvilla Beauty",  "url": "https://www.pinkvilla.com/beauty/rss"},
        {"name": "Popxo Fashion",     "url": "https://www.popxo.com/category/fashion/feed"},
        {"name": "Popxo Beauty",      "url": "https://www.popxo.com/category/beauty/feed"},
        {"name": "Hauterfly",         "url": "https://www.hauterfly.com/feed"},
        {"name": "Lifestyle Asia",    "url": "https://www.lifestyleasia.com/ind/feed"},
        {"name": "BeBeautiful",       "url": "https://www.bebeautiful.in/feed"},
    ]

    results = []

    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            count = 0

            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:300]

                if not title:
                    continue

                matched = [
                    kw for kw in keywords
                    if kw.lower() in (title + " " + summary).lower()
                ]

                results.append({
                    "source": "rss_feed",
                    "feed_name": feed_info["name"],
                    "title": title,
                    "summary": summary,
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "matched_keywords": matched,
                    "fetched_at": datetime.now().isoformat()
                })
                count += 1

            print(f"  [RSS] {feed_info['name']:<22} -> {count} articles")

        except Exception as e:
            print(f"  [RSS] Error for {feed_info['name']}: {e}")

    return results



# MAIN RUNNER

def run_scout():
    print("\n" + "="*50)
    print("  SCOUT AGENT RUNNING")
    print("="*50)

    all_signals = []
    all_seed_topics = FASHION_SEED_TOPICS + BEAUTY_SEED_TOPICS

    # 1. YouTube Shorts — broad fetch
    print("\n[1/5] Fetching YouTube Shorts...")
    youtube_data = fetch_youtube_shorts(all_seed_topics, max_results=15)
    all_signals.extend(youtube_data)
    print(f"  Total: {len(youtube_data)} videos collected")

    # 2. Google Trends — score ALL curated keywords
    print("\n[2/5] Scoring curated keywords via Google Trends...")
    trends_data = fetch_google_trends_velocity(ALL_KEYWORDS, geo="IN")
    all_signals.extend(trends_data)

    # Show rising ones immediately
    rising = [s for s in trends_data if s.get("rising")]
    print(f"  Total: {len(trends_data)} keywords scored")
    print(f"  Currently RISING in India: {[s['keyword'] for s in rising]}")

    # 3. Google Trends rising queries — for top rising keywords only
    print("\n[3/5] Fetching rising queries for top keywords...")
    top_keywords = [
        s["keyword"] for s in
        sorted(trends_data, key=lambda x: x["velocity"], reverse=True)[:10]
    ]
    rising_data = fetch_google_trends_rising_queries(top_keywords, geo="IN")
    all_signals.extend(rising_data)
    print(f"  Total: {len(rising_data)} rising queries found")

    # 4. NewsAPI — check curated keywords in news
    print("\n[4/5] Fetching news articles...")
    news_data = fetch_news_articles(ALL_KEYWORDS)
    all_signals.extend(news_data)
    news_with_matches = [n for n in news_data if n.get("matched_keywords")]
    print(f"  Total: {len(news_data)} articles | {len(news_with_matches)} matched keywords")

    # 5. RSS feeds
    print("\n[5/7] Fetching RSS feeds...")
    rss_data = fetch_rss_feeds(ALL_KEYWORDS)
    all_signals.extend(rss_data)
    rss_with_matches = [r for r in rss_data if r.get("matched_keywords")]
    print(f"  Total: {len(rss_data)} articles | {len(rss_with_matches)} matched keywords")

    # 6. Wikipedia page view velocity
    print("\n[6/7] Checking Wikipedia page view velocity...")
    wiki_pageviews = fetch_wikipedia_pageviews(days_back=30)
    all_signals.extend(wiki_pageviews)

    # 7. Wikipedia today's top trending
    print("\n[7/7] Fetching Wikipedia top trending pages today...")
    wiki_trending = fetch_wikipedia_top_trending()
    all_signals.extend(wiki_trending)
    wiki_rising = [w for w in wiki_pageviews if w.get("rising")]
    print(f"  Wikipedia rising: {[w['page'] for w in wiki_rising]}")

    print("\n" + "="*50)
    print(f"  SCOUT COMPLETE — {len(all_signals)} total signals collected")
    print("="*50)

    return all_signals



# SUMMARY PRINTER

def print_summary(signals):
    print("\n--- SIGNAL SUMMARY ---\n")

    sources = ["youtube_shorts", "google_trends",
               "google_trends_rising", "newsapi", "rss_feed"]

    for source in sources:
        items = [s for s in signals if s["source"] == source]
        print(f"  {source:<25} : {len(items)} signals")

    print("\n  Keywords RISING in India right now:")
    trends = [s for s in signals if s["source"] == "google_trends"]
    rising = [t for t in trends if t.get("rising")]

    if rising:
        for item in sorted(rising, key=lambda x: x["velocity"], reverse=True):
            print(f"    RISING  {item['keyword']:<30} velocity: {item['velocity']}")
    else:
        print("    None above threshold right now")

    print("\n  All keyword velocities:")
    for item in sorted(trends, key=lambda x: x["velocity"], reverse=True):
        status = "RISING" if item["rising"] else "stable"
        bar = "+" * max(0, int(item["velocity"])) if item["velocity"] > 0 else ""
        print(f"    [{status:<6}] {item['keyword']:<30} {item['velocity']:>7.2f}  {bar}")

    print("\n  Top rising breakout queries:")
    rising_q = sorted(
        [s for s in signals if s["source"] == "google_trends_rising"],
        key=lambda x: x["value"],
        reverse=True
    )[:8]
    for item in rising_q:
        print(f"    '{item['rising_query']}' <- '{item['parent_keyword']}' (value: {item['value']})")

    print("\n  Keywords mentioned in news/RSS:")
    all_matched = []
    for s in signals:
        if s["source"] in ["newsapi", "rss_feed"]:
            all_matched.extend(s.get("matched_keywords", []))
    mention_counts = Counter(all_matched)
    for kw, count in mention_counts.most_common(10):
        print(f"    {kw:<30} mentions: {count}")
    print("\n  Wikipedia RISING pages:")
    wiki_rising = [
        s for s in signals
        if s["source"] == "wikipedia_pageviews" and s.get("rising")
    ]
    if wiki_rising:
        for item in sorted(wiki_rising, key=lambda x: x["velocity"], reverse=True):
            print(
                f"    {item['page']:<32} "
                f"+{item['velocity']:.0f} views/day  "
                f"({item['recent_avg_daily']:.0f} avg/day)"
            )
    else:
        print("    None rising above threshold")

    print("\n  Wikipedia top trending today (fashion/beauty):")
    wiki_top = sorted(
        [s for s in signals if s["source"] == "wikipedia_top_trending"],
        key=lambda x: x["views_today"],
        reverse=True
    )[:5]
    if wiki_top:
        for item in wiki_top:
            print(
                f"    #{item['global_rank']} "
                f"{item['page']:<32} "
                f"{item['views_today']:,} views"
            )
    else:
        print("    None found in today's top")



# ENTRY POINT

if __name__ == "__main__":
    signals = run_scout()
    print_summary(signals)

    os.makedirs(DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(DATA_DIR, f"signals_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)

    print(f"\n  Signals saved to: {filepath}")