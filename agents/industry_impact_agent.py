import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
	PROCESSED_DIR,
)


# INDUSTRY IMPACT LEVELS
IMPACT_LEVELS = {
	"CRITICAL": "High and immediate business impact across core value chains",
	"HIGH": "Strong business impact with clear commercial relevance",
	"MODERATE": "Meaningful but contained business impact",
	"LOW": "Limited or early-stage business impact",
	"MINIMAL": "Weak or uncertain business impact",
}


INDUSTRY_BUSINESS_AREAS = {
	"fashion": [
		"product_design",
		"merchandising",
		"retail",
		"ecommerce",
		"supply_chain",
		"social_commerce",
		"influencer_marketing",
	],
	"beauty": [
		"product_formulation",
		"retail",
		"ecommerce",
		"salon_services",
		"consumer_goods",
		"social_commerce",
		"influencer_marketing",
	],
	"retail": ["retail", "merchandising", "store_operations"],
	"ecommerce": ["ecommerce", "marketplaces", "search_conversion"],
	"consumer_goods": ["consumer_goods", "brand_marketing", "distribution"],
	"media": ["content_creation", "publishing", "editorial_coverage"],
	"marketing": ["brand_marketing", "performance_marketing", "creator_partnerships"],
	"salons": ["salon_services", "appointments", "local_services"],
}


AUTHENTICITY_FACTORS = {
	"GENUINE": 1.00,
	"LIKELY_GENUINE": 0.80,
	"SUSPICIOUS": 0.45,
	"ARTIFICIAL_HYPE": 0.20,
}


PHASE_FACTORS = {
	"GROWTH": 1.00,
	"EMERGING": 0.85,
	"PEAK": 0.75,
	"STABLE": 0.55,
	"DECLINE": 0.25,
}


def load_authenticity_results():
	if not os.path.exists(PROCESSED_DIR):
		print(f"  [IndustryImpact] Processed directory not found: {PROCESSED_DIR}")
		return []

	files = [
		f for f in os.listdir(PROCESSED_DIR)
		if f.startswith("authenticity_") and f.endswith(".json")
	]

	if not files:
		print("  No authenticity files found. Run authenticity_agent.py first.")
		return []

	for latest_file in sorted(files, reverse=True):
		filepath = os.path.join(PROCESSED_DIR, latest_file)
		try:
			with open(filepath, "r", encoding="utf-8") as f:
				signals = json.load(f)

			if isinstance(signals, list):
				print(f"  Loaded {len(signals)} authenticity records from {latest_file}")
				return signals
		except Exception as e:
			print(f"  [IndustryImpact] Skipping invalid file {latest_file}: {e}")

	print("  No valid authenticity files found.")
	return []


def clamp(value, minimum=0.0, maximum=1.0):
	return max(minimum, min(maximum, value))


def unique_preserve_order(items):
	seen = set()
	ordered = []
	for item in items:
		if item and item not in seen:
			seen.add(item)
			ordered.append(item)
	return ordered


def get_source_diversity(signal):
	source_scores = signal.get("source_scores", {}) or {}
	active_sources = sum(1 for value in source_scores.values() if value > 0.05)
	total_sources = max(len(source_scores), 1)
	return active_sources, active_sources / total_sources


def infer_business_areas(signal, affected_industries):
	areas = []
	keyword = str(signal.get("keyword", "")).lower()

	for industry in affected_industries:
		areas.extend(INDUSTRY_BUSINESS_AREAS.get(industry, []))

	if "aesthetic" in keyword or "style" in keyword or "makeup" in keyword:
		areas.append("brand_marketing")
		areas.append("creator_partnerships")

	if signal.get("signal_strength") in ["STRONG", "MODERATE"]:
		areas.append("retail")
		areas.append("ecommerce")

	lifecycle_phase = str(signal.get("phase", signal.get("lifecycle_phase", ""))).upper()
	if lifecycle_phase in ["GROWTH", "PEAK"]:
		areas.append("inventory_planning")
		areas.append("demand_forecasting")

	if signal.get("authenticity_level") in ["GENUINE", "LIKELY_GENUINE"]:
		areas.append("product_strategy")

	return unique_preserve_order(areas)


def infer_affected_industries(signal):
	primary_industry = str(signal.get("industry", "unknown")).lower()
	affected = []

	if primary_industry in ["fashion", "beauty"]:
		affected.append(primary_industry)

	if primary_industry == "fashion":
		affected.extend(["retail", "ecommerce", "consumer_goods", "media", "marketing"])
	elif primary_industry == "beauty":
		affected.extend(["consumer_goods", "retail", "ecommerce", "salons", "marketing"])
	else:
		affected.extend(["retail", "ecommerce", "marketing"])

	if signal.get("signal_strength") == "STRONG":
		affected.append(primary_industry)

	if signal.get("authenticity_level") in ["GENUINE", "LIKELY_GENUINE"]:
		affected.append("consumer_goods")

	return unique_preserve_order(affected)


def determine_primary_industry(signal, affected_industries):
	declared_industry = str(signal.get("industry", "unknown")).lower()
	if declared_industry in affected_industries:
		return declared_industry

	if affected_industries:
		return affected_industries[0]

	return declared_industry if declared_industry else "unknown"


def determine_impact_direction(signal):
	phase = str(signal.get("phase", signal.get("lifecycle_phase", ""))).upper()
	authenticity_level = str(signal.get("authenticity_level", "")).upper()
	signal_strength = str(signal.get("signal_strength", "")).upper()

	if authenticity_level == "ARTIFICIAL_HYPE" or phase == "DECLINE":
		return "negative"

	if authenticity_level == "SUSPICIOUS" and signal_strength in ["WEAK", "NOISE"]:
		return "negative"

	if phase in ["GROWTH", "EMERGING", "PEAK"] and authenticity_level in ["GENUINE", "LIKELY_GENUINE"]:
		return "positive"

	if signal_strength == "STRONG":
		return "positive"

	return "mixed"


def calculate_industry_impact_score(signal, affected_industries, business_areas):
	final_score = float(signal.get("final_score", 0.0) or 0.0)
	source_scores = signal.get("source_scores", {}) or {}
	active_sources, source_diversity = get_source_diversity(signal)

	gt_detail = signal.get("details", {}).get("google_trends", {}) or {}
	velocity = float(gt_detail.get("velocity", 0.0) or 0.0)
	recent_avg = float(gt_detail.get("recent_avg", 0.0) or 0.0)

	lifecycle_phase = str(signal.get("phase", signal.get("lifecycle_phase", "STABLE"))).upper()
	phase_factor = PHASE_FACTORS.get(lifecycle_phase, 0.55)

	authenticity_level = str(signal.get("authenticity_level", "SUSPICIOUS")).upper()
	authenticity_factor = AUTHENTICITY_FACTORS.get(authenticity_level, 0.45)

	momentum = clamp((max(velocity, 0.0) / 25.0) * 0.65 + (min(recent_avg, 100.0) / 100.0) * 0.35)
	commercial_applicability = 0.0
	if business_areas:
		commercial_applicability += 0.35
	if signal.get("signal_strength") in ["STRONG", "MODERATE"]:
		commercial_applicability += 0.20
	if active_sources >= 3:
		commercial_applicability += 0.15
	if signal.get("description") and signal.get("signal_strength") != "NOISE":
		commercial_applicability += 0.10
	if len(affected_industries) > 2:
		commercial_applicability += 0.10

	commercial_applicability = clamp(commercial_applicability)

	raw_score = (
		final_score * 0.30
		+ momentum * 0.20
		+ source_diversity * 0.15
		+ authenticity_factor * 0.15
		+ phase_factor * 0.10
		+ commercial_applicability * 0.10
	)

	if authenticity_level == "ARTIFICIAL_HYPE":
		raw_score *= 0.70

	if signal.get("signal_strength") == "NOISE":
		raw_score *= 0.60

	return round(clamp(raw_score), 3), {
		"final_score": final_score,
		"source_count": active_sources,
		"source_diversity": round(source_diversity, 3),
		"momentum": round(momentum, 3),
		"commercial_applicability": round(commercial_applicability, 3),
		"authenticity_factor": authenticity_factor,
		"phase_factor": phase_factor,
	}


def classify_impact_level(score, direction):
	if direction == "negative":
		if score >= 0.75:
			return "CRITICAL", IMPACT_LEVELS["CRITICAL"]
		if score >= 0.50:
			return "HIGH", IMPACT_LEVELS["HIGH"]
		if score >= 0.30:
			return "MODERATE", IMPACT_LEVELS["MODERATE"]
		if score >= 0.15:
			return "LOW", IMPACT_LEVELS["LOW"]
		return "MINIMAL", IMPACT_LEVELS["MINIMAL"]

	if score >= 0.75:
		return "CRITICAL", IMPACT_LEVELS["CRITICAL"]
	if score >= 0.55:
		return "HIGH", IMPACT_LEVELS["HIGH"]
	if score >= 0.35:
		return "MODERATE", IMPACT_LEVELS["MODERATE"]
	if score >= 0.18:
		return "LOW", IMPACT_LEVELS["LOW"]
	return "MINIMAL", IMPACT_LEVELS["MINIMAL"]


def build_reasoning(signal, affected_industries, business_areas, details):
	reasoning = []

	if affected_industries:
		reasoning.append(f"Affected industries: {', '.join(affected_industries[:4])}")
	if business_areas:
		reasoning.append(f"Business areas: {', '.join(business_areas[:5])}")

	signal_strength = signal.get("signal_strength", "UNKNOWN")
	reasoning.append(f"Weak-signal strength: {signal_strength}")

	phase = signal.get("phase", signal.get("lifecycle_phase", "UNKNOWN"))
	reasoning.append(f"Lifecycle phase: {phase}")

	authenticity_level = signal.get("authenticity_level", "UNKNOWN")
	reasoning.append(f"Authenticity: {authenticity_level}")

	source_count = details.get("source_count", 0)
	source_diversity = details.get("source_diversity", 0)
	reasoning.append(f"Source breadth: {source_count} active sources, diversity {source_diversity}")

	momentum = details.get("momentum", 0)
	reasoning.append(f"Momentum proxy: {momentum}")

	if signal.get("authenticity_level") == "ARTIFICIAL_HYPE":
		reasoning.append("Hype risk reduced confidence in commercial durability")

	return reasoning


def run_industry_impact_analysis(signals=None):
	print("\n" + "=" * 50)
	print("  INDUSTRY IMPACT AGENT RUNNING")
	print("=" * 50)

	if signals is None:
		signals = load_authenticity_results()

	if not signals:
		print("  No signals to analyse.")
		return []

	print(f"\n  Analysing industry impact for {len(signals)} trends...\n")

	impact_results = []

	for signal in signals:
		affected_industries = infer_affected_industries(signal)
		primary_industry = determine_primary_industry(signal, affected_industries)
		business_areas = infer_business_areas(signal, affected_industries)
		direction = determine_impact_direction(signal)
		impact_score, score_details = calculate_industry_impact_score(signal, affected_industries, business_areas)
		impact_level, impact_description = classify_impact_level(impact_score, direction)
		reasoning = build_reasoning(signal, affected_industries, business_areas, score_details)

		result = dict(signal)
		result.update({
			"affected_industries": affected_industries,
			"primary_industry": primary_industry,
			"industry_impact_score": impact_score,
			"impact_level": impact_level,
			"impact_direction": direction,
			"affected_business_areas": business_areas,
			"industry_impact_reasoning": reasoning,
			"industry_impact_description": impact_description,
			"industry_impact_details": score_details,
			"analysed_at": datetime.now().isoformat(),
		})
		impact_results.append(result)

	impact_results.sort(key=lambda x: (x.get("industry_impact_score", 0), x.get("final_score", 0)), reverse=True)

	print("  Industry impact analysis complete.\n")
	return impact_results


def print_industry_impact_summary(impact_results):
	print("\n" + "=" * 50)
	print("  INDUSTRY IMPACT ANALYSIS")
	print("=" * 50)

	levels = ["CRITICAL", "HIGH", "MODERATE", "LOW", "MINIMAL"]

	for level in levels:
		items = [item for item in impact_results if item.get("impact_level") == level]
		if not items:
			continue

		print(f"\n  [{level}] — {len(items)} trends")
		print("  " + "-" * 48)

		for item in items[:5]:
			industry_label = item.get("primary_industry", "unknown")
			print(
				f"  [{industry_label[:1].upper()}] {item['keyword']:<28} "
				f"score: {item['industry_impact_score']:.3f}  "
				f"direction: {item['impact_direction']}"
			)
			print(
				f"       Industries: {', '.join(item.get('affected_industries', [])[:4])}"
			)

	print("\n  Top 10 overall by industry impact:")
	print("  " + "-" * 48)
	for i, item in enumerate(impact_results[:10], 1):
		print(
			f"  {i:2}. {item['keyword']:<28} "
			f"{item['impact_level']:<9} {item['industry_impact_score']:.3f}"
		)


if __name__ == "__main__":
	signals = load_authenticity_results()
	impact_results = run_industry_impact_analysis(signals)
	print_industry_impact_summary(impact_results)

	os.makedirs(PROCESSED_DIR, exist_ok=True)
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	filepath = os.path.join(PROCESSED_DIR, f"industry_impact_{timestamp}.json")

	with open(filepath, "w", encoding="utf-8") as f:
		json.dump(impact_results, f, indent=2, ensure_ascii=False)

	print(f"\n  Results saved to: {filepath}")
