"""
Explainability Engine

Explains why the Decision Engine produced:
INVEST
WAIT
AVOID
"""

from datetime import datetime


# ============================================================
# EXPLANATION GENERATOR
# ============================================================

def generate_explanation(signal):

    keyword = signal.get(
        "keyword",
        "Unknown"
    )

    decision = signal.get(
        "decision",
        "UNKNOWN"
    )

    decision_score = float(
        signal.get(
            "decision_score",
            0
        ) or 0
    )

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

    authenticity = str(
        signal.get(
            "authenticity_level",
            "UNKNOWN"
        )
    ).upper()

    phase = str(
        signal.get(
            "phase",
            signal.get(
                "lifecycle_phase",
                "UNKNOWN"
            )
        )
    ).upper()

    reasons = []
    warnings = []


    # ========================================================
    # WEAK SIGNAL
    # ========================================================

    if weak_signal >= 0.70:

        reasons.append(
            f"Strong multi-source trend signal "
            f"({weak_signal:.2f})."
        )

    elif weak_signal >= 0.50:

        reasons.append(
            f"Moderate multi-source trend signal "
            f"({weak_signal:.2f})."
        )

    else:

        warnings.append(
            f"Weak trend signal "
            f"({weak_signal:.2f})."
        )


    # ========================================================
    # INDUSTRY
    # ========================================================

    if industry >= 0.70:

        reasons.append(
            f"High industry impact "
            f"({industry:.2f})."
        )

    elif industry >= 0.50:

        reasons.append(
            f"Moderate industry impact "
            f"({industry:.2f})."
        )

    else:

        warnings.append(
            f"Low industry impact "
            f"({industry:.2f})."
        )


    # ========================================================
    # FINANCIAL
    # ========================================================

    if financial >= 0.70:

        reasons.append(
            f"Strong financial/commercial validation "
            f"({financial:.2f})."
        )

    elif financial >= 0.50:

        reasons.append(
            f"Moderate financial validation "
            f"({financial:.2f})."
        )

    else:

        warnings.append(
            f"Low financial validation "
            f"({financial:.2f})."
        )


    # ========================================================
    # AUTHENTICITY
    # ========================================================

    if authenticity == "GENUINE":

        reasons.append(
            "Signals appear genuine."
        )

    elif authenticity == "LIKELY_GENUINE":

        reasons.append(
            "Signals are likely genuine."
        )

    elif authenticity == "SUSPICIOUS":

        warnings.append(
            "Some signals may be suspicious."
        )

    elif authenticity == "ARTIFICIAL_HYPE":

        warnings.append(
            "The trend shows signs of artificial hype."
        )


    # ========================================================
    # LIFECYCLE
    # ========================================================

    if phase == "EMERGING":

        reasons.append(
            "The trend is in the emerging phase."
        )

    elif phase == "GROWTH":

        reasons.append(
            "The trend is currently in the growth phase."
        )

    elif phase == "PEAK":

        warnings.append(
            "The trend is near its peak."
        )

    elif phase == "DECLINE":

        warnings.append(
            "The trend is currently declining."
        )

    elif phase == "STABLE":

        warnings.append(
            "The trend is stable rather than rapidly growing."
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    if decision == "INVEST":

        summary = (
            f"{keyword} is recommended for INVESTMENT "
            f"because the combined evidence is strong."
        )

    elif decision == "WAIT":

        summary = (
            f"{keyword} shows potential, but additional "
            f"evidence should be collected before investment."
        )

    elif decision == "AVOID":

        summary = (
            f"{keyword} is not recommended for immediate "
            f"investment because the combined evidence "
            f"is weak or risk factors are significant."
        )

    else:

        summary = (
            f"No clear decision could be generated "
            f"for {keyword}."
        )


    # ========================================================
    # RETURN EXPLANATION
    # ========================================================

    return {

        "keyword": keyword,

        "decision": decision,

        "decision_score": decision_score,

        "summary": summary,

        "reasons": reasons,

        "warnings": warnings,

        "generated_at": datetime.now().isoformat(),

    }


# ============================================================
# RUN ENGINE
# ============================================================

def run_explainability_engine(signals):

    print("\n")
    print("=" * 60)
    print("  EXPLAINABILITY ENGINE")
    print("=" * 60)

    results = []

    for signal in signals:

        explanation = generate_explanation(
            signal
        )

        result = dict(signal)

        result["explanation"] = explanation

        results.append(result)

        print(
            f"\n{explanation['keyword']}"
        )

        print(
            f"Decision: "
            f"{explanation['decision']}"
        )

        print(
            f"Score: "
            f"{explanation['decision_score']:.3f}"
        )

        print(
            f"Summary: "
            f"{explanation['summary']}"
        )

        if explanation["reasons"]:

            print("\nReasons:")

            for reason in explanation["reasons"]:

                print(
                    f"  + {reason}"
                )

        if explanation["warnings"]:

            print("\nWarnings:")

            for warning in explanation["warnings"]:

                print(
                    f"  - {warning}"
                )

    return results