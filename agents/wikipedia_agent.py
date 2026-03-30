import requests
import sys
import os
import json
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR


# ─────────────────────────────────────────
# WIKIPEDIA PAGES TO TRACK
# Fashion and beauty trends that have
# Wikipedia articles
# ─────────────────────────────────────────

WIKIPEDIA_PAGES = {
    "fashion_aesthetics": [
        "Quiet luxury",
        "Cottagecore",
        "Dark academia",
        "Y2K fashion",
        "Mob wife aesthetic",
        "Old money aesthetic",
        "Balletcore",
        "Gorpcore",
        "Coastal grandmother",
        "Normcore",
        "Dopamine dressing",
        "Barbiecore",
        "Indie sleaze",
        "Clean girl aesthetic",
    ],
    "indian_fashion": [
        "Kurta",
        "Lehenga",
        "Salwar kameez",
        "Saree",
        "Indo-western clothing",
        "Churidar",
        "Anarkali suit",
        "Bandhani",
        "Phulkari",
        "Ajrakh",
        "Fashion in India",
        "Indian fashion",
    ],
    "beauty_trends": [
        "Glass skin",
        "Skinimalism",
        "K-beauty",
        "Slugging (skincare)",
        "Double cleansing",
        "Skin care",
        "Korean beauty",
        "Natural beauty",
        "Contouring",
        "Lip liner",
        "Eyebrow shaping",
    ],
    "general": [
        "Fast fashion",
        "Sustainable fashion",
        "Streetwear",
        "Athleisure",
        "Capsule wardrobe",
        "Vintage clothing",
        "Thrift shopping",
    ]
}


# ─────────────────────────────────────────
# DATE HELPERS
# ─────────────────────────────────────────

def get_date_range(days_back=30):
    """Returns start and end dates for Wikipedia API."""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


# ─────────────────────────────────────────
# FETCH PAGE VIEWS
# ─────────────────────────────────────────

def fetch_page_views(page_title, days_back=30):
    """
    Fetches daily page view counts for a Wikipedia article.
    Completely free, no API key needed.
    """
    start_date, end_date = get_date_range(days_back)
    page_encoded = page_title.replace(" ", "_")

    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/all-agents/{page_encoded}/daily/"
        f"{start_date}/{end_date}"
    )

    headers = {
        "User-Agent": "TrendForecaster/1.0 (academic-capstone-project)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=8)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if not items:
                return None

            # Calculate metrics
            views_list = [i.get("views", 0) for i in items]
            total_views = sum(views_list)

            # Recent 7 days vs previous period
            recent_views = views_list[-7:]
            older_views = views_list[:-7] if len(views_list) > 7 else views_list

            recent_avg = sum(recent_views) / len(recent_views) if recent_views else 0
            older_avg = sum(older_views) / len(older_views) if older_views else 0

            velocity = recent_avg - older_avg
            peak = max(views_list)
            trend_direction = "rising" if velocity > 50 else "declining" if velocity < -50 else "stable"

            return {
                "page": page_title,
                "total_views": total_views,
                "recent_avg_daily": round(recent_avg, 1),
                "older_avg_daily": round(older_avg, 1),
                "velocity": round(velocity, 2),
                "peak_views": peak,
                "trend_direction": trend_direction,
                "rising": bool(velocity > 50),
                "days_tracked": len(views_list),
                "daily_views": views_list
            }

        elif response.status_code == 404:
            return None  # Page doesn't exist

        else:
            return None

    except Exception as e:
        return None


# ─────────────────────────────────────────
# FETCH WIKIPEDIA TRENDING — TOP PAGES
# Gets globally trending Wikipedia pages
# for today
# ─────────────────────────────────────────

def fetch_wikipedia_top_pages(date=None):
    """
    Fetches the most viewed Wikipedia pages for a given date.
    We then filter these for fashion and beauty relevance.
    This tells us what people are reading about most.
    """
    if date is None:
        # Use yesterday since today may not be complete
        date = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")

    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
        f"en.wikipedia/all-access/{date}"
    )

    headers = {
        "User-Agent": "TrendForecaster/1.0 (academic-capstone-project)"
    }

    fashion_beauty_keywords = [
        "fashion", "style", "beauty", "makeup", "skin", "hair",
        "dress", "outfit", "aesthetic", "trend", "clothing", "wear",
        "kurta", "saree", "lehenga", "ethnic", "western", "indian",
        "cosmetic", "skincare", "lipstick", "foundation", "blush",
        "cottagecore", "luxury", "vintage", "streetwear", "athleisure"
    ]

    results = []

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("items", [{}])[0].get("articles", [])

            print(f"  [Wikipedia Top] Total trending pages today: {len(articles)}")

            for article in articles[:200]:  # check top 200
                title = article.get("article", "").replace("_", " ")
                views = article.get("views", 0)
                rank = article.get("rank", 0)

                # Filter for fashion and beauty relevance
                title_lower = title.lower()
                if any(kw in title_lower for kw in fashion_beauty_keywords):
                    # Skip Wikipedia utility pages
                    if title.startswith("Special:") or title.startswith("Wikipedia:"):
                        continue
                    if title in ["Main Page", "Deaths in", "Portal:"]:
                        continue

                    results.append({
                        "source": "wikipedia_top",
                        "page": title,
                        "views_today": views,
                        "global_rank": rank,
                        "fetched_at": datetime.now().isoformat()
                    })

            print(f"  [Wikipedia Top] Fashion/beauty relevant pages: {len(results)}")

    except Exception as e:
        print(f"  [Wikipedia Top] Error: {e}")

    return results


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_wikipedia_agent(days_back=30):
    """
    Main function — fetches Wikipedia page views
    for all tracked fashion and beauty pages,
    identifies which ones are rising.
    """
    print("\n" + "="*50)
    print("  WIKIPEDIA AGENT RUNNING")
    print("="*50)

    all_results = []

    # 1. Check trending top pages first
    print("\n[1/2] Fetching today's trending Wikipedia pages...")
    top_pages = fetch_wikipedia_top_pages()
    for page in top_pages:
        all_results.append({
            "source": "wikipedia_trending",
            **page
        })
    print(f"  Found {len(top_pages)} fashion/beauty pages in today's top")

    # 2. Check page view velocity for our tracked pages
    print(f"\n[2/2] Checking page view velocity for tracked pages...")
    print(f"  Tracking {sum(len(v) for v in WIKIPEDIA_PAGES.values())} pages across {len(WIKIPEDIA_PAGES)} categories\n")

    rising_pages = []
    stable_pages = []
    not_found = []

    for category, pages in WIKIPEDIA_PAGES.items():
        print(f"  Category: {category}")
        for page in pages:
            result = fetch_page_views(page, days_back=days_back)

            if result:
                result["source"] = "wikipedia_pageviews"
                result["category"] = category
                result["fetched_at"] = datetime.now().isoformat()
                all_results.append(result)

                status = "RISING" if result["rising"] else result["trend_direction"].upper()
                print(
                    f"    {page:<35} "
                    f"views/day: {result['recent_avg_daily']:>8.0f}  "
                    f"velocity: {result['velocity']:>8.1f}  "
                    f"[{status}]"
                )

                if result["rising"]:
                    rising_pages.append(result)
                else:
                    stable_pages.append(result)

            else:
                not_found.append(page)
                print(f"    {page:<35} no data found")

            time.sleep(0.2)  # be polite to Wikipedia API

    # Summary
    print("\n" + "="*50)
    print(f"  WIKIPEDIA AGENT COMPLETE")
    print(f"  Total pages tracked  : {len(rising_pages) + len(stable_pages)}")
    print(f"  Rising pages         : {len(rising_pages)}")
    print(f"  Stable pages         : {len(stable_pages)}")
    print(f"  Not found            : {len(not_found)}")
    print("="*50)

    if rising_pages:
        print("\n  RISING pages (people increasingly reading about these):")
        for p in sorted(rising_pages, key=lambda x: x["velocity"], reverse=True):
            print(
                f"    {p['page']:<35} "
                f"+{p['velocity']:.0f} views/day velocity  "
                f"({p['recent_avg_daily']:.0f} avg/day)"
            )

    if not_found:
        print(f"\n  Pages with no Wikipedia data: {not_found}")

    return all_results


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    results = run_wikipedia_agent(days_back=30)

    # Save results
    os.makedirs(DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(DATA_DIR, f"wikipedia_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to: {filepath}")