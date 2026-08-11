#!/usr/bin/env python3

"""
AI-Based Real-Time Trend Forecasting System
Main orchestrator for the multi-agent trend detection system.
"""

import os
import sys
from datetime import datetime

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "agents"
    )
)

from scout_agent import run_scout
from weak_signal_agent import run_weak_signal_detection
from lifecycle_agent import run_lifecycle_analysis
from authenticity_agent import run_authenticity_analysis
from industry_impact_agent import run_industry_impact_analysis
from financial_agent import run_financial_validation

# NEW
from decision_engine import run_decision_engine
from explainability_engine import run_explainability_engine


def merge_results(
    base_results,
    additional_results
):

    additional_by_keyword = {
        item.get("keyword"): item
        for item in additional_results
        if item.get("keyword")
    }

    merged_results = []

    for result in base_results:

        keyword = result.get(
            "keyword"
        )

        merged_result = dict(
            result
        )

        if keyword in additional_by_keyword:

            merged_result.update(
                additional_by_keyword[
                    keyword
                ]
            )

        merged_results.append(
            merged_result
        )

    return merged_results


def main():

    print("=" * 60)
    print("  AI TREND FORECASTING SYSTEM")
    print("=" * 60)

    print(
        f"  Started at: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # ========================================================
    # PHASE 1
    # ========================================================

    print(
        "\nPHASE 1: SCOUTING & WEAK SIGNAL DETECTION"
    )

    print("-" * 50)

    print(
        "1. Running Scout Agent..."
    )

    signals = run_scout()

    if not signals:

        print(
            "No signals returned from Scout Agent."
        )

        return

    print(
        f"Scout returned "
        f"{len(signals)} signals."
    )

    print(
        "\n2. Running Weak Signal Agent..."
    )

    weak_signals = (
        run_weak_signal_detection(
            signals
        )
    )

    if not weak_signals:

        print(
            "No weak signals returned."
        )

        return

    # ========================================================
    # PHASE 2
    # ========================================================

    print(
        "\n\nPHASE 2: TREND ANALYSIS"
    )

    print(
        "-" * 50
    )

    print(
        "3. Running Lifecycle Agent..."
    )

    lifecycle_results = (
        run_lifecycle_analysis(
            weak_signals
        )
    )

    signals_with_lifecycle = (
        merge_results(
            weak_signals,
            lifecycle_results
        )
    )

    print(
        "\n4. Running Authenticity Agent..."
    )

    authenticity_results = (
        run_authenticity_analysis(
            signals_with_lifecycle
        )
    )

    signals_with_authenticity = (
        merge_results(
            signals_with_lifecycle,
            authenticity_results
        )
    )

    # ========================================================
    # PHASE 3
    # ========================================================

    print(
        "\n\nPHASE 3: BUSINESS & FINANCIAL ANALYSIS"
    )

    print(
        "-" * 50
    )

    print(
        "5. Running Industry Impact Agent..."
    )

    industry_results = (
        run_industry_impact_analysis(
            signals_with_authenticity
        )
    )

    print(
        "\n6. Running Financial Validation Agent..."
    )

    financial_results = (
        run_financial_validation(
            industry_results
        )
    )

    if not financial_results:

        print(
            "No financial results returned."
        )

        return

    # ========================================================
    # PHASE 4 - NEW
    # ========================================================

    print(
        "\n\nPHASE 4: DECISION ENGINE"
    )

    print(
        "-" * 50
    )

    print(
        "7. Running Decision Engine..."
    )

    decision_results = (
        run_decision_engine(
            financial_results
        )
    )

    # ========================================================
    # PHASE 5 - NEW
    # ========================================================

    print(
        "\n\nPHASE 5: EXPLAINABILITY ENGINE"
    )

    print(
        "-" * 50
    )

    print(
        "8. Running Explainability Engine..."
    )

    final_results = (
        run_explainability_engine(
            decision_results
        )
    )

    # ========================================================
    # FINAL ANALYSIS
    # ========================================================

    print(
        "\n\n" + "=" * 60
    )

    print(
        "  ANALYSIS COMPLETE"
    )

    print(
        "=" * 60
    )

    print(
        "\nTOP TREND INSIGHTS:"
    )

    print(
        "-" * 30
    )

    # IMPORTANT:
    # Now sort using Decision Score
    top_trends = sorted(
        final_results,
        key=lambda item:
        item.get(
            "decision_score",
            0
        ),
        reverse=True
    )[:5]

    for index, trend in enumerate(
        top_trends,
        1
    ):

        keyword = trend.get(
            "keyword",
            "Unknown"
        )

        industry = trend.get(
            "primary_industry",
            trend.get(
                "industry",
                "unknown"
            )
        )

        signal_strength = trend.get(
            "signal_strength",
            "UNKNOWN"
        )

        phase = trend.get(
            "phase",
            trend.get(
                "lifecycle_phase",
                "UNKNOWN"
            )
        )

        authenticity = trend.get(
            "authenticity_level",
            "UNKNOWN"
        )

        impact_level = trend.get(
            "impact_level",
            "UNKNOWN"
        )

        financial_level = trend.get(
            "commercial_signal_level",
            "UNKNOWN"
        )

        final_score = trend.get(
            "final_score",
            0
        )

        impact_score = trend.get(
            "industry_impact_score",
            0
        )

        financial_score = trend.get(
            "financial_validation_score",
            0
        )

        # NEW
        decision_score = trend.get(
            "decision_score",
            0
        )

        decision = trend.get(
            "decision",
            "UNKNOWN"
        )

        confidence = trend.get(
            "decision_confidence",
            0
        )

        action_window = trend.get(
            "action_window",
            "UNKNOWN"
        )

        print(
            f"{index}. {keyword} "
            f"({industry})"
        )

        print(
            f"   Signal: {signal_strength} | "
            f"Phase: {phase} | "
            f"Authenticity: {authenticity}"
        )

        print(
            f"   Industry Impact: "
            f"{impact_level} "
            f"({impact_score:.3f})"
        )

        print(
            f"   Commercial Signal: "
            f"{financial_level} "
            f"({financial_score:.3f})"
        )

        print(
            f"   Weak Signal Score: "
            f"{final_score:.3f}"
        )

        # NEW
        print(
            f"   Decision Score: "
            f"{decision_score:.3f}"
        )

        print(
            f"   Decision: "
            f"{decision}"
        )

        print(
            f"   Confidence: "
            f"{confidence:.2f}%"
        )

        print(
            f"   Action Window: "
            f"{action_window}"
        )

        # NEW - Explainability
        explanation = trend.get(
            "explanation",
            {}
        )

        if explanation:

            print(
                f"   Explanation: "
                f"{explanation.get('summary', 'N/A')}"
            )

        print()

    print(
        "All results saved to "
        "data/processed/ directory."
    )

    print(
        f"Completed at: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    main()