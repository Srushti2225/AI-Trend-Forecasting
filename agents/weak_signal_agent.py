import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    FASHION_KEYWORDS,
    BEAUTY_KEYWORDS,
    VELOCITY_THRESHOLD,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    DATA_DIR
)



# SCORING WEIGHTS
# Each source contributes differently to
# the overall trend score


WEIGHTS = {
    "youtube_shorts":       0.25,
    "google_trends":        0.30,
    "google_trends_rising": 0.20,
    "newsapi":              0.15,
    "rss_feed":             0.10,
}


# LOAD LATEST SIGNALS FILE


def load_latest_signals():
    """
    Loads the most recently saved signals JSON file from data/raw/
    """
    if not os.path.exists(DATA_DIR):
        print(f"  [WeakSignal] Data directory not found: {DATA_DIR}")
        return []

    files = [
        f for f in os.listdir(DATA_DIR)
        if f.startswith("signals_") and f.endswith(".json")
    ]

    if not files:
        print("  [WeakSignal] No signal files found. Run scout_agent.py first.")
        return []

    # Sort by filename (timestamp is in filename) and pick latest
    latest_file = sorted(files)[-1]
    filepath = os.path.join(DATA_DIR, latest_file)

    with open(filepath, "r", encoding="utf-8") as f:
        signals = json.load(f)

    print(f"  [WeakSignal] Loaded {len(signals)} signals from {latest_file}")
    return signals



# SCORE: YOUTUBE


def score_youtube(signals, keyword):
    """
    Scores a keyword based on how many recent YouTube Shorts
    videos exist for it. More recent videos = stronger signal.
    """
    youtube_signals = [
        s for s in signals
        if s["source"] == "youtube_shorts"
        and s.get("keyword", "").lower() == keyword.lower()
    ]

    count = len(youtube_signals)

    # Count how many were published in last 48 hours
    recent_count = 0
    for s in youtube_signals:
        try:
            pub = datetime.fromisoformat(s["published_at"].replace("Z", "+00:00"))
            now = datetime.now().astimezone()
            hours_ago = (now - pub).total_seconds() / 3600
            if hours_ago <= 48:
                recent_count += 1
        except Exception:
            pass

    # Score: base count + bonus for recency
    raw_score = (count * 0.5) + (recent_count * 2.0)

    # Normalize to 0-1 range (cap at 20 videos = max score)
    normalized = min(raw_score / 20.0, 1.0)

    return round(normalized, 3), {
        "total_videos": count,
        "recent_48h": recent_count,
        "raw_score": raw_score
    }


# SCORE: GOOGLE TRENDS


def score_google_trends(signals, keyword):
    """
    Scores a keyword based on its Google Trends velocity.
    Higher velocity = more rapidly rising interest in India.
    """
    trend_signals = [
        s for s in signals
        if s["source"] == "google_trends"
        and s.get("keyword", "").lower() == keyword.lower()
    ]

    if not trend_signals:
        return 0.0, {"velocity": 0, "recent_avg": 0}

    signal = trend_signals[0]
    velocity = signal.get("velocity", 0)
    recent_avg = signal.get("recent_avg", 0)
    peak_value = signal.get("peak_value", 0)

    # Velocity score: normalize between -30 and +30
    velocity_score = (velocity + 30) / 60.0
    velocity_score = max(0.0, min(1.0, velocity_score))

    # Recency bonus: if recent average is high, trend is active
    recency_bonus = min(recent_avg / 100.0, 0.3)

    raw_score = (velocity_score * 0.7) + recency_bonus

    return round(min(raw_score, 1.0), 3), {
        "velocity": velocity,
        "recent_avg": recent_avg,
        "peak_value": peak_value
    }



# SCORE: RISING QUERIES


def score_rising_queries(signals, keyword):
    """
    Scores a keyword based on breakout related search queries.
    A high breakout value means people are actively discovering
    this trend for the first time — strongest early signal.
    """
    rising_signals = [
        s for s in signals
        if s["source"] == "google_trends_rising"
        and s.get("parent_keyword", "").lower() == keyword.lower()
    ]

    if not rising_signals:
        return 0.0, {"rising_queries": [], "max_value": 0}

    # Get top breakout value
    max_value = max(s.get("value", 0) for s in rising_signals)
    query_count = len(rising_signals)

    # Breakout values can be very large (200000+) for truly viral terms
    # Normalize: 200000 = max score
    value_score = min(max_value / 200000.0, 1.0)

    # Bonus for having multiple rising queries
    count_bonus = min(query_count / 10.0, 0.2)

    raw_score = (value_score * 0.8) + count_bonus

    top_queries = sorted(rising_signals, key=lambda x: x.get("value", 0), reverse=True)[:3]

    return round(min(raw_score, 1.0), 3), {
        "rising_queries": [q["rising_query"] for q in top_queries],
        "max_value": max_value,
        "query_count": query_count
    }


# SCORE: NEWS MENTIONS

def score_news(signals, keyword):
    """
    Scores a keyword based on how many news articles mention it.
    News coverage = trend is reaching mainstream awareness.
    """
    news_signals = [
        s for s in signals
        if s["source"] in ["newsapi", "rss_feed"]
    ]

    # Count direct keyword mentions in titles and descriptions
    mention_count = 0
    for s in news_signals:
        content = (
            str(s.get("title", "")) + " " +
            str(s.get("description", "")) + " " +
            str(s.get("summary", ""))
        ).lower()

        if keyword.lower() in content:
            mention_count += 1

        # Also check matched_keywords field
        if keyword in s.get("matched_keywords", []):
            mention_count += 1

    # Normalize: 5+ mentions = max score
    normalized = min(mention_count / 5.0, 1.0)

    return round(normalized, 3), {
        "mention_count": mention_count
    }


# CROSS-PLATFORM BONUS

def calculate_cross_platform_bonus(source_scores):
    """
    Bonus score when a trend appears across multiple platforms.
    A trend on YouTube + Google Trends + News = much stronger signal
    than the same trend on just one platform.
    """
    active_sources = sum(1 for score in source_scores.values() if score > 0.1)

    if active_sources >= 4:
        return 0.20   # Very strong — appearing everywhere
    elif active_sources == 3:
        return 0.12   # Strong — multi-platform
    elif active_sources == 2:
        return 0.05   # Moderate — two platforms
    else:
        return 0.0    # Weak — single platform only


# CLASSIFY TREND STRENGTH


def classify_signal(final_score):
    """
    Classifies overall signal strength into
    human-readable categories for the research team.
    """
    if final_score >= CONFIDENCE_HIGH:
        return "STRONG", "High confidence emerging trend"
    elif final_score >= CONFIDENCE_MEDIUM:
        return "MODERATE", "Possible emerging trend — monitor closely"
    elif final_score >= 0.20:
        return "WEAK", "Early whisper — not yet confirmed"
    else:
        return "NOISE", "Insufficient signal across sources"



# DETECT INDUSTRY

def detect_industry(keyword):
    """
    Tags each keyword with its industry category.
    """
    if keyword in FASHION_KEYWORDS:
        return "fashion"
    elif keyword in BEAUTY_KEYWORDS:
        return "beauty"
    else:
        return "unknown"


# MAIN: ANALYSE ALL KEYWORDS


def run_weak_signal_detection(signals=None):
    """
    Runs weak signal detection across all keywords.
    Scores each keyword from every source and combines
    into a single ranked list of emerging trends.
    """
    print("\n" + "="*50)
    print("  WEAK SIGNAL AGENT RUNNING")
    print("="*50)

    if signals is None:
        signals = load_latest_signals()

    if not signals:
        print("  No signals to analyse.")
        return []

    all_keywords = FASHION_KEYWORDS + BEAUTY_KEYWORDS
    trend_scores = []

    print(f"\n  Analysing {len(all_keywords)} keywords across {len(signals)} signals...\n")

    for keyword in all_keywords:
        # Score from each source
        yt_score, yt_detail = score_youtube(signals, keyword)
        gt_score, gt_detail = score_google_trends(signals, keyword)
        rq_score, rq_detail = score_rising_queries(signals, keyword)
        news_score, news_detail = score_news(signals, keyword)

        source_scores = {
            "youtube":        yt_score,
            "google_trends":  gt_score,
            "rising_queries": rq_score,
            "news":           news_score,
        }

        # Weighted sum
        weighted_score = (
            yt_score    * WEIGHTS["youtube_shorts"] +
            gt_score    * WEIGHTS["google_trends"] +
            rq_score    * WEIGHTS["google_trends_rising"] +
            news_score  * (WEIGHTS["newsapi"] + WEIGHTS["rss_feed"])
        )

        # Cross-platform bonus
        cross_bonus = calculate_cross_platform_bonus(source_scores)
        final_score = min(weighted_score + cross_bonus, 1.0)

        # Classify
        signal_strength, description = classify_signal(final_score)

        # Industry tag
        industry = detect_industry(keyword)

        trend_scores.append({
            "keyword":          keyword,
            "industry":         industry,
            "final_score":      round(final_score, 3),
            "signal_strength":  signal_strength,
            "description":      description,
            "source_scores":    source_scores,
            "cross_bonus":      cross_bonus,
            "details": {
                "youtube":        yt_detail,
                "google_trends":  gt_detail,
                "rising_queries": rq_detail,
                "news":           news_detail,
            },
            "analysed_at": datetime.now().isoformat()
        })

    # Sort by final score descending
    trend_scores.sort(key=lambda x: x["final_score"], reverse=True)

    print("  ANALYSIS COMPLETE\n")
    return trend_scores


# SUMMARY PRINTER

def print_weak_signal_summary(trend_scores):
    print("\n" + "="*50)
    print("  TREND SIGNAL RANKINGS")
    print("="*50)

    categories = ["STRONG", "MODERATE", "WEAK", "NOISE"]

    for category in categories:
        items = [t for t in trend_scores if t["signal_strength"] == category]
        if not items:
            continue

        print(f"\n  [{category}] — {len(items)} keywords")
        print("  " + "-"*46)

        for item in items:
            industry_tag = "F" if item["industry"] == "fashion" else "B"
            print(f"  [{industry_tag}] {item['keyword']:<25} score: {item['final_score']}")

            scores = item["source_scores"]
            print(
                f"       YT:{scores['youtube']:.2f}  "
                f"GT:{scores['google_trends']:.2f}  "
                f"RQ:{scores['rising_queries']:.2f}  "
                f"News:{scores['news']:.2f}  "
                f"Bonus:{item['cross_bonus']:.2f}"
            )

            # Show rising queries if any
            rq = item["details"]["rising_queries"].get("rising_queries", [])
            if rq:
                print(f"       Rising queries: {', '.join(rq[:2])}")

        print()


# ENTRY POINT

if __name__ == "__main__":
    import json

    # Load signals and run detection
    signals = load_latest_signals()
    trend_scores = run_weak_signal_detection(signals)
    print_weak_signal_summary(trend_scores)

    # Save results
    output_dir = os.path.join(os.path.dirname(DATA_DIR), "processed")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"weak_signals_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(trend_scores, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to: {filepath}")