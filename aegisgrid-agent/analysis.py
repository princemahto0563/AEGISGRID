"""
AegisGrid - Deterministic Infrastructure Cascade Analysis
Fictional infrastructure dependency model for Fetch-A-Thon 3.0 ASI:One Agent Challenge.
All operations are simulated only.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


DEFAULT_SCENARIOS_PATH = Path(__file__).parent / "scenarios.json"


def load_model(path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load the explicit infrastructure registry and dependency model."""
    target_path = Path(path) if path else DEFAULT_SCENARIOS_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Infrastructure configuration not found at {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_asset_id(asset_id: str, model: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate asset ID against registered infrastructure catalog."""
    normalized_id = (asset_id or "").strip().upper()
    registered_assets = model.get("assets", {})
    if normalized_id in registered_assets:
        return True, None
    return False, f"Asset ID '{asset_id}' is not registered in operational catalog."


def get_asset_info(asset_id: str, model: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get metadata for a registered asset."""
    normalized_id = (asset_id or "").strip().upper()
    return model.get("assets", {}).get(normalized_id)


def analyze_cascade(
    failed_asset_id: str,
    model: Dict[str, Any],
    unavailable_resources: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Deterministic cascade analysis traversing explicitly defined dependency relationships.
    Never invents dependencies at runtime.
    """
    unavailable = {r.strip().upper() for r in (unavailable_resources or set())}
    normalized_id = (failed_asset_id or "").strip().upper()
    assets = model.get("assets", {})

    # 1. Validation check
    is_valid, error = validate_asset_id(normalized_id, model)
    if not is_valid:
        return {
            "root_asset": normalized_id or "UNKNOWN",
            "is_valid": False,
            "quarantined": True,
            "status": "QUARANTINED",
            "error": error,
            "affected_assets": [],
            "cascade_paths": [],
            "summary": (
                f"[SIMULATION] Ingress Quarantine: Asset '{normalized_id}' was not found in the "
                "registered infrastructure catalog. Telemetry report quarantined to prevent "
                "unverified impact injection into the digital twin topology."
            ),
        }

    root_asset = assets[normalized_id]
    affected: Dict[str, Dict[str, Any]] = {}
    paths: List[Dict[str, Any]] = []

    # Queue for deterministic breadth-first dependency traversal
    queue = [normalized_id]
    visited: Set[str] = {normalized_id}

    while queue:
        current_id = queue.pop(0)
        current_asset = assets.get(current_id, {})
        dependents = current_asset.get("downstream_dependents", [])

        for dep_id in dependents:
            dep_asset = assets.get(dep_id)
            if not dep_asset:
                continue

            # Determine cascade effect based on explicit asset relationships
            impact_reason = ""
            severity = "Warning"

            if current_id == "S-01":
                if dep_id == "W-02":
                    impact_reason = "Loss of primary electrical supply induces water pump pressure loss."
                    severity = "Warning"
                elif dep_id == "T-04":
                    impact_reason = "Substation feeder loss degrades intersection signal synchronization."
                    severity = "Warning"
                elif dep_id == "H-01":
                    # Check if backup generator is available
                    if "G-01" in unavailable:
                        impact_reason = (
                            "CRITICAL: Primary feeder lost and backup generator G-01 is unavailable! "
                            "Hospital healthcare continuity at critical risk."
                        )
                        severity = "Critical"
                    else:
                        impact_reason = (
                            "Primary grid feeder lost; hospital transfer switch engages backup generator G-01."
                        )
                        severity = "High"

            elif current_id == "G-01":
                if dep_id == "H-01":
                    impact_reason = (
                        "Backup generator G-01 is unavailable. Hospital loses reserve redundancy, "
                        "operating on single-feed grid contingency."
                    )
                    severity = "High"

            elif current_id == "W-02":
                if dep_id == "H-01":
                    impact_reason = "Reduced municipal water pressure affects critical medical chiller systems."
                    severity = "Warning"

            else:
                impact_reason = f"Downstream dependency on failed component {current_id}."
                severity = "Warning"

            if dep_id not in affected:
                affected[dep_id] = {
                    "asset_id": dep_id,
                    "name": dep_asset.get("name"),
                    "type": dep_asset.get("type"),
                    "criticality": dep_asset.get("criticality"),
                    "severity": severity,
                    "impact_reason": impact_reason,
                    "upstream_cause": current_id,
                }
                paths.append({
                    "from": current_id,
                    "to": dep_id,
                    "type": "dependency",
                    "reason": impact_reason,
                })

            if dep_id not in visited:
                visited.add(dep_id)
                queue.append(dep_id)

    # Format human-readable summary
    affected_list = list(affected.values())
    if not affected_list:
        summary = (
            f"[SIMULATION] Analysis of {normalized_id} ({root_asset.get('name')}): "
            "Isolated event. No downstream dependency failures detected."
        )
    else:
        dep_names = ", ".join(f"{a['asset_id']} ({a['name']})" for a in affected_list)
        summary = (
            f"[SIMULATION] Cascade Analysis for {normalized_id} ({root_asset.get('name')}):\n"
            f"- Direct status: Offline / Degraded ({root_asset.get('criticality')} criticality)\n"
            f"- Downstream affected nodes ({len(affected_list)}): {dep_names}\n"
            f"- Impact paths modeled: {len(paths)} dependency edges traversed."
        )

    return {
        "root_asset": normalized_id,
        "root_name": root_asset.get("name"),
        "root_criticality": root_asset.get("criticality"),
        "is_valid": True,
        "quarantined": False,
        "status": "ANALYZED",
        "affected_assets": affected_list,
        "cascade_paths": paths,
        "summary": summary,
    }
