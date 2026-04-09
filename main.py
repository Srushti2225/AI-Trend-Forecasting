#!/usr/bin/env python3
"""
AI-Based Real-Time Trend Forecasting System
Main orchestrator for the multi-agent trend detection system.
"""

import os
import sys
import json
from datetime import datetime

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from scout_agent import run_scout
from weak_signal_agent import run_weak_signal_detection
from lifecycle_agent import run_lifecycle_analysis
from authenticity_agent import run_authenticity_analysis

def main():
    print("="*60)
    print("  AI TREND FORECASTING SYSTEM")
    print("="*60)
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Phase 1: Data Collection & Weak Signal Detection
    print("PHASE 1: SCOUTING & WEAK SIGNAL DETECTION")
    print("-" * 50)

    # 1. Run scout agent
    print("1. Running Scout Agent...")
    signals = run_scout()

    # 2. Run weak signal detection
    print("\n2. Running Weak Signal Agent...")
    weak_signals = run_weak_signal_detection(signals)

    # Phase 2: Trend Analysis
    print("\n\nPHASE 2: TREND ANALYSIS")
    print("-" * 50)

    # 3. Run lifecycle analysis
    print("3. Running Lifecycle Agent...")
    lifecycle_results = run_lifecycle_analysis(weak_signals)

    # 4. Run authenticity analysis
    print("\n4. Running Authenticity Agent...")
    authenticity_results = run_authenticity_analysis(weak_signals)

    # Summary
    print("\n\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60)

    # Show top insights
    print("\nTOP TREND INSIGHTS:")
    print("-" * 30)

    # Get top 5 by final score
    top_trends = sorted(weak_signals, key=lambda x: x['final_score'], reverse=True)[:5]

    for i, trend in enumerate(top_trends, 1):
        # Find corresponding lifecycle and authenticity
        lifecycle = next((l for l in lifecycle_results if l['keyword'] == trend['keyword']), None)
        auth = next((a for a in authenticity_results if a['keyword'] == trend['keyword']), None)

        phase = lifecycle['phase'] if lifecycle else 'UNKNOWN'
        auth_level = auth['authenticity_level'] if auth else 'UNKNOWN'

        print(f"{i}. {trend['keyword']} ({trend['industry']})")
        print(f"   Signal: {trend['signal_strength']} | Phase: {phase} | Authenticity: {auth_level}")
        print(f"   Score: {trend['final_score']:.3f}")
        print()

    print("All results saved to data/processed/ directory.")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()