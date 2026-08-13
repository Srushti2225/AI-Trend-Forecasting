#!/usr/bin/env python3

"""
AI-Based Real-Time Trend Forecasting System
Main orchestrator — with option to use cached signals.
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))

from agents.scout_agent import run_scout
from agents.weak_signal_agent import run_weak_signal_detection
from agents.lifecycle_agent import run_lifecycle_analysis
from agents.authenticity_agent import run_authenticity_analysis
from agents.industry_impact_agent import run_industry_impact_analysis
from agents.financial_agent import run_financial_validation
from agents.decision_engine import run_decision_engine
from agents.explainability_engine import run_explainability_engine

from config import PROCESSED_DIR, DATA_DIR


# ─────────────────────────────────────────
# MERGE HELPER
# ─────────────────────────────────────────

def merge_results(base_results, additional_results):
    additional_by_keyword = {
        item.get("keyword"): item
        for item in additional_results
        if item.get("keyword")
    }
    merged = []
    for result in base_results:
        keyword = result.get("keyword")
        merged_result = dict(result)
        if keyword in additional_by_keyword:
            merged_result.update(additional_by_keyword[keyword])
        merged.append(merged_result)
    return merged


# ─────────────────────────────────────────
# LOAD CACHED SIGNALS
# ─────────────────────────────────────────

def load_cached_signals():
    """
    Loads the most recent signals file from data/raw/
    instead of re-fetching from APIs.
    Useful when Google Trends is rate limiting.
    """
    if not os.path.exists(DATA_DIR):
        return None

    files = [
        f for f in os.listdir(DATA_DIR)
        if f.startswith("signals_") and f.endswith(".json")
    ]

    if not files:
        return None

    latest = sorted(files)[-1]
    filepath = os.path.join(DATA_DIR, latest)

    with open(filepath, "r", encoding="utf-8") as f:
        signals = json.load(f)

    print(f"  Loaded cached signals from: {latest}")
    print(f"  Total signals: {len(signals)}")
    return signals


# ─────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────

def save_results(data, prefix):
    """
    Saves any results dict/list to data/processed/
    with a timestamp filename.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(PROCESSED_DIR, f"{prefix}_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {filepath}")
    return filepath


# ─────────────────────────────────────────
# PRINT FINAL SUMMARY
# ─────────────────────────────────────────

def print_final_summary(final_results):
    print("\n\n" + "="*60)
    print("  FINAL TREND INTELLIGENCE REPORT")
    print("="*60)

    invest = [t for t in final_results if t.get("decision") == "INVEST"]
    wait   = [t for t in final_results if t.get("decision") == "WAIT"]
    avoid  = [t for t in final_results if t.get("decision") == "AVOID"]

    print(f"\n  INVEST : {len(invest)} trends")
    print(f"  WAIT   : {len(wait)} trends")
    print(f"  AVOID  : {len(avoid)} trends")

    if invest:
        print("\n  ► INVEST RECOMMENDATIONS:")
        print("  " + "-"*58)
        for t in invest:
            print(
                f"  {t.get('keyword'):<28} "
                f"score: {t.get('decision_score', 0):.3f}  "
                f"confidence: {t.get('decision_confidence', 0):.1f}%  "
                f"window: {t.get('action_window', 'N/A')}"
            )

    if wait:
        print("\n  ► WAIT / MONITOR:")
        print("  " + "-"*58)
        for t in wait:
            print(
                f"  {t.get('keyword'):<28} "
                f"score: {t.get('decision_score', 0):.3f}  "
                f"confidence: {t.get('decision_confidence', 0):.1f}%"
            )

    print("\n  TOP 10 BY DECISION SCORE:")
    print("  " + "-"*58)

    top = sorted(
        final_results,
        key=lambda x: x.get("decision_score", 0),
        reverse=True
    )[:10]

    for i, trend in enumerate(top, 1):
        keyword         = trend.get("keyword", "Unknown")
        industry        = trend.get("primary_industry", trend.get("industry", "?"))
        signal_strength = trend.get("signal_strength", "?")
        phase           = trend.get("phase", "?")
        authenticity    = trend.get("authenticity_level", "?")
        impact_level    = trend.get("impact_level", "?")
        financial_level = trend.get("commercial_signal_level", "?")
        final_score     = trend.get("final_score", 0)
        impact_score    = trend.get("industry_impact_score", 0)
        financial_score = trend.get("financial_validation_score", 0)
        decision_score  = trend.get("decision_score", 0)
        decision        = trend.get("decision", "?")
        confidence      = trend.get("decision_confidence", 0)
        action_window   = trend.get("action_window", "?")
        explanation     = trend.get("explanation", {})

        print(f"\n  {i}. {keyword.upper()} [{industry}]")
        print(f"     Signal: {signal_strength} | Phase: {phase} | Auth: {authenticity}")
        print(f"     Weak Signal Score  : {final_score:.3f}")
        print(f"     Industry Impact    : {impact_level} ({impact_score:.3f})")
        print(f"     Financial Signal   : {financial_level} ({financial_score:.3f})")
        print(f"     Decision Score     : {decision_score:.3f}")
        print(f"     DECISION           : ► {decision} ({confidence:.1f}% confidence)")
        print(f"     Action Window      : {action_window}")

        if explanation.get("summary"):
            print(f"     Summary            : {explanation['summary']}")
        if explanation.get("reasons"):
            print(f"     Key reason         : {explanation['reasons'][0]}")
        if explanation.get("warnings"):
            print(f"     Key warning        : {explanation['warnings'][0]}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main(use_cache=False):
    print("="*60)
    print("  AI TREND FORECASTING SYSTEM — TrendSense")
    print("="*60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ─────────────────────────────────────
    # PHASE 1 — DATA COLLECTION
    # ─────────────────────────────────────
    print("\n\nPHASE 1: DATA COLLECTION")
    print("-"*50)

    if use_cache:
        print("  Using cached signals (skipping API fetch)...")
        signals = load_cached_signals()
        if not signals:
            print("  No cached signals found. Running Scout Agent...")
            signals, _ = run_scout()
    else:
        print("  [1/8] Running Scout Agent...")
        signals = run_scout()

    if not signals:
        print("  ERROR: No signals collected. Exiting.")
        return

    print(f"  Total signals: {len(signals)}")

    # ─────────────────────────────────────
    # PHASE 2 — WEAK SIGNAL DETECTION
    # ─────────────────────────────────────
    print("\n\nPHASE 2: WEAK SIGNAL DETECTION")
    print("-"*50)

    print("  [2/8] Running Weak Signal Agent...")
    weak_signals = run_weak_signal_detection(signals)

    if not weak_signals:
        print("  ERROR: No weak signals. Exiting.")
        return

    save_results(weak_signals, "weak_signals")
    print(f"  Scored {len(weak_signals)} keywords.")

    # ─────────────────────────────────────
    # PHASE 3 — TREND ANALYSIS
    # ─────────────────────────────────────
    print("\n\nPHASE 3: TREND ANALYSIS")
    print("-"*50)

    print("  [3/8] Running Lifecycle Agent...")
    lifecycle_results = run_lifecycle_analysis(weak_signals)
    signals_with_lifecycle = merge_results(weak_signals, lifecycle_results)
    save_results(lifecycle_results, "lifecycle")

    print("  [4/8] Running Authenticity Agent...")
    authenticity_results = run_authenticity_analysis(signals_with_lifecycle)
    signals_with_authenticity = merge_results(
        signals_with_lifecycle, authenticity_results
    )
    save_results(authenticity_results, "authenticity")

    # ─────────────────────────────────────
    # PHASE 4 — BUSINESS ANALYSIS
    # ─────────────────────────────────────
    print("\n\nPHASE 4: BUSINESS ANALYSIS")
    print("-"*50)

    print("  [5/8] Running Industry Impact Agent...")
    industry_results = run_industry_impact_analysis(signals_with_authenticity)
    save_results(industry_results, "industry_impact")

    print("  [6/8] Running Financial Validation Agent...")
    financial_results = run_financial_validation(industry_results)

    if not financial_results:
        print("  ERROR: No financial results. Exiting.")
        return

    save_results(financial_results, "financial_validation")

    # ─────────────────────────────────────
    # PHASE 5 — DECISION ENGINE
    # ─────────────────────────────────────
    print("\n\nPHASE 5: DECISION ENGINE")
    print("-"*50)

    print("  [7/8] Running Decision Engine...")
    decision_results = run_decision_engine(financial_results)
    save_results(decision_results, "decision_results")

    # ─────────────────────────────────────
    # PHASE 6 — EXPLAINABILITY
    # ─────────────────────────────────────
    print("\n\nPHASE 6: EXPLAINABILITY ENGINE")
    print("-"*50)

    print("  [8/8] Running Explainability Engine...")
    final_results = run_explainability_engine(decision_results)

    # ─────────────────────────────────────
    # SAVE FINAL OUTPUT
    # ─────────────────────────────────────
    print("\n\nSAVING RESULTS")
    print("-"*50)

    final_path = save_results(final_results, "final_results")

    # Save human readable summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(PROCESSED_DIR, f"summary_{timestamp}.txt")

    with open(summary_path, "w", encoding="utf-8") as f:
        invest = [t for t in final_results if t.get("decision") == "INVEST"]
        wait   = [t for t in final_results if t.get("decision") == "WAIT"]
        avoid  = [t for t in final_results if t.get("decision") == "AVOID"]

        f.write("="*60 + "\n")
        f.write("  TRENDSENSE — FINAL REPORT\n")
        f.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        f.write(f"INVEST : {len(invest)} trends\n")
        f.write(f"WAIT   : {len(wait)} trends\n")
        f.write(f"AVOID  : {len(avoid)} trends\n\n")

        top = sorted(
            final_results,
            key=lambda x: x.get("decision_score", 0),
            reverse=True
        )[:20]

        f.write("TOP 20 TRENDS\n")
        f.write("-"*60 + "\n")

        for i, t in enumerate(top, 1):
            f.write(f"\n{i}. {t.get('keyword', '?').upper()}\n")
            f.write(f"   Decision      : {t.get('decision', '?')}\n")
            f.write(f"   Decision Score: {t.get('decision_score', 0):.3f}\n")
            f.write(f"   Confidence    : {t.get('decision_confidence', 0):.1f}%\n")
            f.write(f"   Signal        : {t.get('signal_strength', '?')}\n")
            f.write(f"   Phase         : {t.get('phase', '?')}\n")
            f.write(f"   Authenticity  : {t.get('authenticity_level', '?')}\n")
            f.write(f"   Action Window : {t.get('action_window', '?')}\n")
            exp = t.get("explanation", {})
            if exp.get("summary"):
                f.write(f"   Summary       : {exp['summary']}\n")

    print(f"  Summary saved: {summary_path}")
    print_final_summary(final_results)

    print(f"\n\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    # Set use_cache=True to use previously saved signals
    # Set use_cache=False to fetch fresh data
    main(use_cache=False)