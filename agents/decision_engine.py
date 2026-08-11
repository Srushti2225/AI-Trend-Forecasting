"""
DECISION ENGINE
---------------
Combines the outputs of all existing agents and produces:

INVEST
WAIT
AVOID

This is a rule-based / weighted decision engine.
It does NOT use machine learning.
"""

from datetime import datetime


# ============================================================
# WEIGHTS
# ============================================================

DECISION_WEIGHTS = {
    "weak_signal": 0.30,
    "lifecycle": 0.15,
    "authenticity": 0.15,
    "industry": 0.20,
    "financial": 0.20,
}


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def clamp(value, minimum=0.0, maximum=1.0):
    return max(
        minimum,
        min(maximum, float(value))
    )


def get_authenticity_score(level):

    level = str(level).upper()

    scores = {
        "GENUINE": 1.00,
        "LIKELY_GENUINE": 0.80,
        "SUSPICIOUS": 0.45,
        "ARTIFICIAL_HYPE": 0.20,
    }

    return scores.get(level, 0.50)


def get_lifecycle_score(phase):

    phase = str(phase).upper()

    scores = {
        "GROWTH": 1.00,
        "EMERGING": 0.85,
        "PEAK": 0.70,
        "STABLE": 0.55,
        "DECLINE": 0.25,
    }

    return scores.get(phase, 0.50)


# ============================================================
# DECISION SCORE
# ============================================================

def calculate_decision_score(signal):

    weak_signal = clamp(
        signal.get("final_score", 0)
    )

    industry = clamp(
        signal.get(
            "industry_impact_score",
            0
        )
    )

    financial = clamp(
        signal.get(
            "financial_validation_score",
            0
        )
    )

    authenticity = get_authenticity_score(
        signal.get(
            "authenticity_level",
            "UNKNOWN"
        )
    )

    lifecycle = get_lifecycle_score(
        signal.get(
            "phase",
            signal.get(
                "lifecycle_phase",
                "UNKNOWN"
            )
        )
    )

    score = (
        weak_signal
        * DECISION_WEIGHTS["weak_signal"]

        + lifecycle
        * DECISION_WEIGHTS["lifecycle"]

        + authenticity
        * DECISION_WEIGHTS["authenticity"]

        + industry
        * DECISION_WEIGHTS["industry"]

        + financial
        * DECISION_WEIGHTS["financial"]
    )

    return round(
        clamp(score),
        3
    )


# ============================================================
# DECISION LOGIC
# ============================================================

def generate_decision(
    decision_score,
    signal
):

    phase = str(
        signal.get(
            "phase",
            signal.get(
                "lifecycle_phase",
                ""
            )
        )
    ).upper()

    authenticity = str(
        signal.get(
            "authenticity_level",
            ""
        )
    ).upper()

    weak_signal = float(
        signal.get(
            "final_score",
            0
        ) or 0
    )

    industry = float(
        signal.get(
            "industry_impact_score",
            0
        ) or 0
    )

    financial = float(
        signal.get(
            "financial_validation_score",
            0
        ) or 0
    )

    # --------------------------------------------------------
    # HARD RISK CONDITIONS
    # --------------------------------------------------------

    if authenticity == "ARTIFICIAL_HYPE":

        if decision_score < 0.75:
            return "AVOID"

    if phase == "DECLINE":

        if decision_score < 0.65:
            return "AVOID"

    if (
        financial < 0.25
        and industry < 0.35
    ):
        return "AVOID"

    # --------------------------------------------------------
    # MAIN DECISION
    # --------------------------------------------------------

    if decision_score >= 0.70:

        return "INVEST"

    elif decision_score >= 0.50:

        return "WAIT"

    else:

        return "AVOID"


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    decision_score,
    decision
):

    # Distance from the neutral point.
    distance = abs(
        decision_score - 0.50
    )

    confidence = 50 + (
        distance * 100
    )

    # Keep confidence between 50 and 100
    confidence = max(
        50,
        min(100, confidence)
    )

    # Slightly increase confidence for
    # clear decisions.
    if decision in [
        "INVEST",
        "AVOID"
    ]:
        confidence += 3

    confidence = min(
        confidence,
        100
    )

    return round(
        confidence,
        2
    )


# ============================================================
# ACTION WINDOW
# ============================================================

def get_action_window(
    decision,
    phase
):

    phase = str(
        phase
    ).upper()

    if decision == "INVEST":

        if phase == "EMERGING":
            return "Early entry: 4-8 weeks"

        if phase == "GROWTH":
            return "Immediate action: 2-6 weeks"

        if phase == "PEAK":
            return "Short opportunity: 1-3 weeks"

        return "Near-term validation"

    if decision == "WAIT":

        if phase == "EMERGING":
            return "Monitor for 2-4 weeks"

        if phase == "GROWTH":
            return "Monitor for 1-3 weeks"

        return "Re-evaluate after new signals"

    return "No immediate action"


# ============================================================
# MAIN DECISION ENGINE
# ============================================================

def run_decision_engine(signals):

    print("\n")
    print("=" * 60)
    print("  DECISION ENGINE")
    print("=" * 60)

    if not signals:

        print(
            "No signals received."
        )

        return []

    results = []

    for signal in signals:

        keyword = signal.get(
            "keyword",
            "Unknown"
        )

        # Calculate combined score
        decision_score = (
            calculate_decision_score(
                signal
            )
        )

        # Generate decision
        decision = generate_decision(
            decision_score,
            signal
        )

        # Get lifecycle
        phase = signal.get(
            "phase",
            signal.get(
                "lifecycle_phase",
                "UNKNOWN"
            )
        )

        # Confidence
        confidence = (
            calculate_confidence(
                decision_score,
                decision
            )
        )

        # Action window
        action_window = (
            get_action_window(
                decision,
                phase
            )
        )

        # Create output
        result = dict(signal)

        result.update({

            "decision_score":
                decision_score,

            "decision":
                decision,

            "decision_confidence":
                confidence,

            "action_window":
                action_window,

            "decision_engine":
                "weighted_rule_based",

            "decision_generated_at":
                datetime.now().isoformat(),

        })

        results.append(
            result
        )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        print(
            f"\nKeyword: {keyword}"
        )

        print(
            f"Decision Score : "
            f"{decision_score:.3f}"
        )

        print(
            f"Decision        : "
            f"{decision}"
        )

        print(
            f"Confidence      : "
            f"{confidence:.2f}%"
        )

        print(
            f"Lifecycle       : "
            f"{phase}"
        )

        print(
            f"Action Window   : "
            f"{action_window}"
        )

    # Sort strongest first
    results.sort(
        key=lambda item:
        item.get(
            "decision_score",
            0
        ),
        reverse=True
    )

    return results