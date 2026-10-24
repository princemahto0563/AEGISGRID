"""
AegisGrid - Local End-to-End Simulation Script
Simulates full ACP natural-language chat interactions across all challenge scenarios.
All operations are simulated only.
"""

from __future__ import annotations
import json
from pathlib import Path
from agent import AegisAgentState, process_chat_command
from recovery import load_incident_history


def run_simulation():
    print("=" * 70)
    print("AEGISGRID LOCAL END-TO-END ACP CHAT AGENT SIMULATION")
    print("Fetch-A-Thon 3.0 ASI:One Agent Challenge")
    print("=" * 70)

    sim_history_file = Path(__file__).parent / "incident_history.json"
    if sim_history_file.exists():
        sim_history_file.unlink()

    state = AegisAgentState(history_path=sim_history_file)

    script = [
        ("User", "Analyze outage at S-01"),
        ("User", "Show affected assets"),
        ("User", "Plan recovery"),
        ("User", "G-01 is unavailable"),
        ("User", "Plan recovery"),
        ("User", "Analyze outage at UNKNOWN-999"),
        ("User", "Verify RA-05"),
        ("User", "Duplicate incident report for S-01"),
    ]

    for speaker, text in script:
        print(f"\n💬 [{speaker}]: {text}")
        reply = process_chat_command(text, state)
        print(f"🤖 [AegisGrid ACP Agent]:\n{reply}")
        print("-" * 70)

    # Inspect persistent history
    history = load_incident_history(sim_history_file)
    print(f"\n📂 PERSISTENT AUDIT TRAIL SUMMARY ({len(history)} events recorded):")
    for i, event in enumerate(history, 1):
        evt_type = event.get("event_type", "EVENT")
        inc_id = event.get("incident_id", "N/A")
        ev_id = event.get("evidence_id", "N/A")
        print(f"  {i}. [{ev_id}] {evt_type} | Incident: {inc_id} | Time: {event.get('timestamp_utc')}")

    print("\n✅ Local end-to-end simulation completed successfully.")


if __name__ == "__main__":
    run_simulation()
