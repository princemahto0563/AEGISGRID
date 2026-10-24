"""
Unit tests for deterministic recovery planning, action verification, and persistence.
"""

import json
from pathlib import Path
from analysis import analyze_cascade, load_model
from recovery import (
    load_incident_history,
    plan_recovery,
    save_incident_history,
    verify_proposed_action,
)


def test_recovery_plan_s01():
    model = load_model()
    cascade = analyze_cascade("S-01", model)
    plan = plan_recovery("S-01", cascade, model)

    assert plan["is_valid"] is True
    assert plan["status"] == "PLANNED"
    assert len(plan["actions"]) >= 4

    action_ids = [a["action_id"] for a in plan["actions"]]
    # S-01 plan should prioritize feeder isolation, generator backup check, water, and traffic
    assert action_ids == ["RA-01", "RA-04", "RA-02", "RA-03"]

    # First action should be In Progress / Verified
    assert plan["actions"][0]["verified"] is True
    assert plan["actions"][0]["status"] == "In Progress"


def test_g01_unavailable_plan_recalculation():
    model = load_model()
    # When G-01 is unavailable, primary generator verification RA-04 cannot proceed.
    # Instead, RA-07 (mobile emergency generator unit) must be dispatched.
    cascade = analyze_cascade("G-01", model, unavailable_resources={"G-01"})
    plan = plan_recovery("G-01", cascade, model, unavailable_resources={"G-01"})

    assert plan["is_valid"] is True
    action_ids = [a["action_id"] for a in plan["actions"]]
    assert "RA-07" in action_ids
    assert "RA-04" not in action_ids  # RA-04 is omitted because G-01 is unavailable

    # RA-07 targets H-01
    ra07 = next(a for a in plan["actions"] if a["action_id"] == "RA-07")
    assert ra07["target_asset"] == "H-01"
    assert ra07["verified"] is True


def test_invalid_proposed_action_rejected():
    model = load_model()

    # RA-05 is a disallowed action (bypass lockout without breaker audit)
    verified, detail, meta = verify_proposed_action("RA-05", "S-01", model)
    assert verified is False
    assert "rejected" in detail.lower()
    assert "unsafe sequence" in detail.lower()
    assert meta.get("is_disallowed") is True


def test_unavailable_resource_blocks_action():
    model = load_model()

    # When G-01 is marked unavailable, RA-04 (which requires G-01) must fail verification
    verified, detail, meta = verify_proposed_action(
        "RA-04", "G-01", model, unavailable_resources={"G-01"}
    )
    assert verified is False
    assert "resource unavailable" in detail.lower()
    assert "G-01" in detail


def test_unregistered_target_asset_rejected():
    model = load_model()

    verified, detail, _ = verify_proposed_action("RA-01", "FAKE-999", model)
    assert verified is False
    assert "not registered" in detail.lower()


def test_persistence_of_incident_history(tmp_path: Path):
    test_history_file = tmp_path / "test_history.json"

    # Save first incident
    rec1 = save_incident_history(
        {"root_asset": "S-01", "event_type": "OUTAGE", "status": "ACTIVE"},
        storage_path=test_history_file,
    )
    assert rec1["incident_id"] is not None
    assert rec1["evidence_id"] is not None

    # Save second incident
    rec2 = save_incident_history(
        {"root_asset": "G-01", "event_type": "UNAVAILABLE", "status": "MITIGATING"},
        storage_path=test_history_file,
    )
    assert rec2["evidence_id"] != rec1["evidence_id"]

    # Save third incident (duplicate report)
    rec3 = save_incident_history(
        {"root_asset": "S-01", "event_type": "DUPLICATE_MERGE", "incident_id": rec1["incident_id"]},
        storage_path=test_history_file,
    )

    # Load back and verify history is never silently overwritten
    loaded = load_incident_history(storage_path=test_history_file)
    assert len(loaded) == 3
    assert loaded[0]["root_asset"] == "S-01"
    assert loaded[1]["root_asset"] == "G-01"
    assert loaded[2]["event_type"] == "DUPLICATE_MERGE"
