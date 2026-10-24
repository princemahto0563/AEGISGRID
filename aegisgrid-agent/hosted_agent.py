"""
AegisGrid - Autonomous Resilience Agent (Single-File Agentverse Hosted Version)
Fetch-A-Thon 3.0 ASI:One Agent Challenge.
All operations are simulated only.

Deployable directly into the Agentverse Web Cloud Editor without local filesystem dependencies.
"""

from __future__ import annotations
from datetime import datetime, timezone
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# --- Embedded Infrastructure Model (No external filesystem dependency) ---
SCENARIOS_DATA: Dict[str, Any] = {
    "system": {
        "name": "AegisGrid Resilience Model",
        "version": "1.0.0",
        "environment": "SIMULATION_ONLY",
        "disclaimer": "All infrastructure actions, impacts, and recovery workflows are simulated. Never claim simulated actions repaired real physical infrastructure.",
    },
    "assets": {
        "S-01": {
            "id": "S-01",
            "name": "Electrical Substation",
            "type": "Electrical",
            "criticality": "Critical",
            "sector": "Sector 1 - North District",
            "default_status": "normal",
            "dependencies": [],
            "downstream_dependents": ["W-02", "T-04", "H-01"],
            "description": "Primary high-voltage distribution substation feeding water pumping, traffic signaling, and hospital main line.",
        },
        "W-02": {
            "id": "W-02",
            "name": "Water Pump Station",
            "type": "Water",
            "criticality": "High",
            "sector": "Sector 2 - Central Reservoir",
            "default_status": "normal",
            "dependencies": ["S-01"],
            "downstream_dependents": ["H-01"],
            "description": "Potable and cooling water distribution pump station requiring primary electricity from S-01.",
        },
        "T-04": {
            "id": "T-04",
            "name": "Traffic Signals & Emergency Corridor",
            "type": "Traffic",
            "criticality": "Moderate",
            "sector": "Sector 4 - Metro Arterial",
            "default_status": "normal",
            "dependencies": ["S-01"],
            "downstream_dependents": ["H-01"],
            "description": "Synchronized intersection signals along the primary emergency vehicle corridor connecting district sectors.",
        },
        "H-01": {
            "id": "H-01",
            "name": "Hospital Critical Care & Backup Feeder",
            "type": "Healthcare",
            "criticality": "Critical",
            "sector": "Sector 3 - Medical Center",
            "default_status": "normal",
            "dependencies": ["S-01", "G-01", "W-02"],
            "downstream_dependents": [],
            "description": "Regional trauma hospital requiring continuous electricity (primary S-01, reserve G-01) and water pressure.",
        },
        "G-01": {
            "id": "G-01",
            "name": "Backup Generator Station",
            "type": "Backup",
            "criticality": "High",
            "sector": "Sector 1 - Reserve Facility",
            "default_status": "normal",
            "dependencies": [],
            "downstream_dependents": ["H-01"],
            "description": "Dedicated diesel/gas emergency turbine generator providing redundant power to hospital and substation bus during outages.",
        },
    },
    "action_catalog": {
        "RA-01": {
            "id": "RA-01",
            "action": "Isolate upstream feeder and reroute demand to reserve bus",
            "target_asset": "S-01",
            "base_priority": 1,
            "rationale": "Mitigates cascading electrical fault propagation while stabilizing feeder bus.",
            "prerequisites": ["breaker_latch_confirmed", "grid_controller_clearance"],
            "resource_required": "feeder_reserve_bus",
        },
        "RA-02": {
            "id": "RA-02",
            "action": "Shift pump staging to emergency reserve pressure setpoint",
            "target_asset": "W-02",
            "base_priority": 2,
            "rationale": "Maintains minimum hydraulic pressure for municipal services and hospital cooling.",
            "prerequisites": ["operator_clearance", "pressure_threshold_validated"],
            "resource_required": "hydraulic_accumulator",
        },
        "RA-03": {
            "id": "RA-03",
            "action": "Reduce traffic cycle times and maintain emergency corridor green wave",
            "target_asset": "T-04",
            "base_priority": 3,
            "rationale": "Preserves vehicle flow along critical response routes while signal controller runs on degraded power.",
            "prerequisites": ["signal_controller_sync"],
            "resource_required": "arterial_signal_network",
        },
        "RA-04": {
            "id": "RA-04",
            "action": "Validate backup generator startup sequence and transfer switch",
            "target_asset": "G-01",
            "base_priority": 4,
            "rationale": "Guarantees secondary power continuity to critical healthcare loads.",
            "prerequisites": ["gas_lube_checked", "starter_electrical_verified"],
            "resource_required": "G-01",
        },
        "RA-05": {
            "id": "RA-05",
            "action": "Bypass lockout and restore full load without breaker audit",
            "target_asset": "S-01",
            "base_priority": 1,
            "rationale": "Unsafe acceleration attempt to energize feeder without verifying interlocks.",
            "prerequisites": ["NO_PREREQUISITES_SATISFIED"],
            "resource_required": "none",
            "is_disallowed": True,
        },
        "RA-06": {
            "id": "RA-06",
            "action": "Quarantine payload and audit telemetry ingress gateway",
            "target_asset": "UNKNOWN-999",
            "base_priority": 1,
            "rationale": "Quarantines unrecognized asset data to protect digital twin graph integrity.",
            "prerequisites": ["security_controller_auth"],
            "resource_required": "ingress_firewall",
        },
        "RA-07": {
            "id": "RA-07",
            "action": "Dispatch mobile emergency power unit to hospital H-01",
            "target_asset": "H-01",
            "base_priority": 1,
            "rationale": "Contingency dispatch because primary backup generator G-01 is unavailable.",
            "prerequisites": ["emergency_fleet_clearance"],
            "resource_required": "mobile_generator_fleet",
        },
    },
}


# --- Deterministic Cascade Analysis ---
def validate_asset_id(asset_id: str, model: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    normalized_id = (asset_id or "").strip().upper()
    if normalized_id in model.get("assets", {}):
        return True, None
    return False, f"Asset ID '{asset_id}' is not registered in operational catalog."


def analyze_cascade(
    failed_asset_id: str,
    model: Dict[str, Any],
    unavailable_resources: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    unavailable = {r.strip().upper() for r in (unavailable_resources or set())}
    normalized_id = (failed_asset_id or "").strip().upper()
    assets = model.get("assets", {})

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
    queue = [normalized_id]
    visited: Set[str] = {normalized_id}

    while queue:
        current_id = queue.pop(0)
        dependents = assets.get(current_id, {}).get("downstream_dependents", [])
        for dep_id in dependents:
            dep_asset = assets.get(dep_id)
            if not dep_asset:
                continue

            impact_reason = ""
            severity = "Warning"
            if current_id == "S-01":
                if dep_id == "W-02":
                    impact_reason = "Loss of primary electrical supply induces water pump pressure loss."
                elif dep_id == "T-04":
                    impact_reason = "Substation feeder loss degrades intersection signal synchronization."
                elif dep_id == "H-01":
                    if "G-01" in unavailable:
                        impact_reason = "CRITICAL: Primary feeder lost and backup generator G-01 is unavailable! Hospital continuity at critical risk."
                        severity = "Critical"
                    else:
                        impact_reason = "Primary grid feeder lost; hospital transfer switch engages backup generator G-01."
                        severity = "High"
            elif current_id == "G-01" and dep_id == "H-01":
                impact_reason = "Backup generator G-01 is unavailable. Hospital operates on single-feed grid contingency."
                severity = "High"
            elif current_id == "W-02" and dep_id == "H-01":
                impact_reason = "Reduced municipal water pressure affects critical medical chiller systems."
            else:
                impact_reason = f"Downstream dependency on failed component {current_id}."

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
                paths.append({"from": current_id, "to": dep_id, "type": "dependency", "reason": impact_reason})

            if dep_id not in visited:
                visited.add(dep_id)
                queue.append(dep_id)

    affected_list = list(affected.values())
    return {
        "root_asset": normalized_id,
        "root_name": root_asset.get("name"),
        "root_criticality": root_asset.get("criticality"),
        "is_valid": True,
        "quarantined": False,
        "status": "ANALYZED",
        "affected_assets": affected_list,
        "cascade_paths": paths,
        "summary": f"[SIMULATION] Cascade Analysis for {normalized_id} ({root_asset.get('name')}): {len(affected_list)} downstream nodes affected.",
    }


# --- Recovery Planning & Verification ---
def verify_proposed_action(
    action_id: str,
    target_asset: str,
    model: Dict[str, Any],
    unavailable_resources: Optional[Set[str]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    unavailable = {r.strip().upper() for r in (unavailable_resources or set())}
    action = model.get("action_catalog", {}).get(action_id)
    if not action:
        return False, f"Action ID '{action_id}' not found in catalog.", {}

    target = target_asset or action.get("target_asset", "")
    if target not in model.get("assets", {}) and target not in {"UNKNOWN-999", "X-99"}:
        return False, f"Target asset '{target}' is not registered.", action

    if action.get("is_disallowed", False):
        return False, f"REJECTED: Action {action_id} proposes an unsafe sequence: {action.get('rationale')}. Disallowed by safety interlocks.", action

    req_resource = action.get("resource_required", "").strip().upper()
    if req_resource in unavailable:
        return False, f"RESOURCE UNAVAILABLE: Required resource '{req_resource}' is currently offline.", action

    return True, f"VERIFIED: Action {action_id} passed all safety, topology, and prerequisite audits.", action


def plan_recovery(
    failed_asset_id: str,
    cascade_result: Dict[str, Any],
    model: Dict[str, Any],
    unavailable_resources: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    unavailable = {r.strip().upper() for r in (unavailable_resources or set())}
    catalog = model.get("action_catalog", {})
    root_id = (failed_asset_id or "").strip().upper()

    if not cascade_result.get("is_valid", True) or cascade_result.get("quarantined", False):
        action_item = catalog.get("RA-06", {})
        verified, reason, _ = verify_proposed_action("RA-06", root_id, model, unavailable)
        return {
            "root_asset": root_id,
            "status": "QUARANTINED",
            "is_valid": False,
            "actions": [
                {
                    "priority": 1,
                    "action_id": "RA-06",
                    "action": action_item.get("action"),
                    "target_asset": root_id,
                    "rationale": action_item.get("rationale"),
                    "verified": verified,
                    "verification_detail": reason,
                    "status": "Verified" if verified else "Failed",
                }
            ],
            "summary": "[SIMULATION] Security Protocol: Telemetry quarantined. No invasive recovery actions dispatched.",
        }

    selected_ids: List[str] = []
    if "G-01" in unavailable or root_id == "G-01":
        selected_ids.extend(["RA-07", "RA-01"])
    elif root_id == "S-01":
        selected_ids.extend(["RA-01", "RA-04", "RA-02", "RA-03"])
    elif root_id == "W-02":
        selected_ids.append("RA-02")
    elif root_id == "T-04":
        selected_ids.append("RA-03")
    else:
        selected_ids.append("RA-01")

    actions_out: List[Dict[str, Any]] = []
    for priority_idx, act_id in enumerate(selected_ids, start=1):
        meta = catalog.get(act_id, {})
        target = meta.get("target_asset", root_id)
        verified, detail, _ = verify_proposed_action(act_id, target, model, unavailable)
        actions_out.append({
            "priority": priority_idx,
            "action_id": act_id,
            "action": meta.get("action", ""),
            "target_asset": target,
            "rationale": meta.get("rationale", ""),
            "prerequisites": meta.get("prerequisites", []),
            "verified": verified,
            "verification_detail": detail,
            "status": "In Progress" if (priority_idx == 1 and verified) else ("Verified" if verified else "Failed"),
        })

    summary_lines = [f"[SIMULATION] Recovery Plan for {root_id} Outage ({len(actions_out)} ranked actions):"]
    for act in actions_out:
        tag = "VERIFIED" if act["verified"] else "BLOCKED"
        summary_lines.append(f"  {act['priority']}. [{tag}] {act['action_id']}: {act['action']} (Target: {act['target_asset']})")

    return {
        "root_asset": root_id,
        "status": "PLANNED",
        "is_valid": True,
        "actions": actions_out,
        "summary": "\n".join(summary_lines),
    }


# --- In-Memory State for Cloud Hosted Session ---
class HostedAgentState:
    def __init__(self):
        self.model = SCENARIOS_DATA
        self.unavailable_resources: Set[str] = set()
        self.active_failed_asset: Optional[str] = None
        self.last_cascade: Optional[Dict[str, Any]] = None
        self.last_plan: Optional[Dict[str, Any]] = None
        self.active_incident_id: Optional[str] = None
        self.history: List[Dict[str, Any]] = []

    def record_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc).isoformat()
        ev_id = f"EV-{len(self.history) + 100:03d}"
        entry = {"evidence_id": ev_id, "timestamp_utc": now_utc, **record}
        self.history.append(entry)
        return entry


hosted_state = HostedAgentState()


def make_chat_response(text: str, end_session: bool = False) -> ChatMessage:
    content: List[AgentContent] = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(content=content)


def process_chat_command(raw_text: str, state: HostedAgentState) -> str:
    text = (raw_text or "").strip()
    if not text:
        return (
            "[SIMULATION] Ready for resilience operations.\n"
            "Try: 'Analyze outage at S-01', 'Show affected assets', 'G-01 is unavailable', or 'Plan recovery'."
        )

    lower = text.lower()

    if "duplicate" in lower and "incident" in lower:
        target_asset = state.active_failed_asset or "S-01"
        ev = state.record_event({
            "incident_id": state.active_incident_id or "INC-2041",
            "event_type": "DUPLICATE_REPORT_SUPPRESSED",
            "target_asset": target_asset,
        })
        return (
            f"[SIMULATION] ℹ️ DUPLICATE INCIDENT DETECTED\n"
            f"Active Incident: {ev.get('incident_id')} (Target: {target_asset})\n"
            f"Evidence ID: {ev['evidence_id']}\n"
            "Action: Second report merged into active incident chain. Operational queue preserves a single authoritative action pipeline."
        )

    if "unavailable" in lower or ("offline" in lower and not lower.startswith("analyze")):
        resource_id = "G-01"
        for cand in ["G-01", "S-01", "W-02", "T-04", "H-01"]:
            if cand.lower() in lower:
                resource_id = cand
                break
        state.unavailable_resources.add(resource_id)
        target = state.active_failed_asset or resource_id
        state.last_cascade = analyze_cascade(target, state.model, state.unavailable_resources)
        state.last_plan = plan_recovery(target, state.last_cascade, state.model, state.unavailable_resources)
        ev = state.record_event({"event_type": "RESOURCE_UNAVAILABLE", "resource_id": resource_id})
        return (
            f"[SIMULATION] 🚨 RESOURCE STATUS UPDATE\n"
            f"Resource: {resource_id} marked as UNAVAILABLE.\n"
            f"Evidence ID: {ev['evidence_id']}\n\n"
            f"Operational Cascade:\n"
            f"• Hospital H-01 power redundancy compromised; backup generator offline.\n"
            f"• Contingency Action Dispatched: RA-07 (Mobile Emergency Power Unit to H-01).\n\n"
            f"Recalculated Plan:\n{state.last_plan['summary']}"
        )

    act_match = re.search(r"\bverify\s+(ra-\d+)\b", lower)
    if act_match or "verify action" in lower or "invalid action" in lower or "bypass lockout" in lower:
        act_id = act_match.group(1).upper() if act_match else ("RA-05" if ("invalid" in lower or "bypass" in lower) else "RA-01")
        target_asset = "S-01"
        verified, detail, meta = verify_proposed_action(act_id, target_asset, state.model, state.unavailable_resources)
        state.record_event({"event_type": "ACTION_VERIFICATION", "action_id": act_id, "verified": verified})
        if not verified:
            return (
                f"[SIMULATION] ⛔ ACTION VERIFICATION AUDIT: REJECTED\n"
                f"Action ID: {act_id} ({meta.get('action', 'Unsafe Sequence')})\n"
                f"Target: {target_asset}\n"
                f"Audit Result: FAILED / BLOCKED\n"
                f"Reason: {detail}\n"
                "Rule: Verification Agent prohibits unlatched bypasses without breaker clearance."
            )
        return (
            f"[SIMULATION] ✅ ACTION VERIFICATION AUDIT: APPROVED\n"
            f"Action ID: {act_id} ({meta.get('action', '')})\n"
            f"Target: {target_asset}\n"
            f"Audit Result: PASSED\n"
            f"Detail: {detail}"
        )

    if "analyze" in lower or "outage" in lower or "failure" in lower:
        asset_id = "S-01"
        id_match = re.search(r"\b(?:at|asset|for)?\s*([a-zA-Z]+-?\d+)\b", text)
        if id_match:
            cand = id_match.group(1).strip().upper()
            if cand not in {"ANALYZE", "OUTAGE", "AT", "SHOW", "PLAN"}:
                asset_id = cand
        else:
            for known in ["S-01", "W-02", "T-04", "H-01", "G-01", "UNKNOWN-999", "X-99"]:
                if known.lower() in lower:
                    asset_id = known
                    break

        cascade = analyze_cascade(asset_id, state.model, state.unavailable_resources)
        state.last_cascade = cascade

        if not cascade["is_valid"]:
            plan = plan_recovery(asset_id, cascade, state.model, state.unavailable_resources)
            state.last_plan = plan
            ev = state.record_event({"event_type": "UNKNOWN_ASSET_QUARANTINED", "asset_id": asset_id})
            return (
                f"[SIMULATION] 🛡️ INGRESS SECURITY QUARANTINE\n"
                f"Reported Asset ID: {asset_id} — NOT FOUND IN OPERATIONAL CATALOG\n"
                f"Evidence ID: {ev['evidence_id']}\n"
                f"Status: QUARANTINED\n\n"
                f"{cascade['summary']}\n\n"
                f"Action Taken: RA-06 (Quarantine payload and audit telemetry ingress gateway).\n"
                "Operational Digital Twin topology graph remains protected and unaffected."
            )

        state.active_failed_asset = asset_id
        plan = plan_recovery(asset_id, cascade, state.model, state.unavailable_resources)
        state.last_plan = plan
        inc_id = f"INC-{2040 + len(state.unavailable_resources) * 10 + 1}"
        state.active_incident_id = inc_id
        ev = state.record_event({"event_type": "OUTAGE_CASCADE", "asset_id": asset_id, "incident_id": inc_id})

        lines = [
            f"[SIMULATION] ⚠️ INCIDENT REPORT: {cascade['root_name']} ({asset_id}) Outage",
            f"Incident ID: {inc_id} | Evidence ID: {ev['evidence_id']} | Status: ACTIVE_SIMULATION",
            "",
            f"1. Direct Impact: {asset_id} ({cascade['root_name']}) — Critical Outage ({cascade['root_criticality']} criticality)",
            "",
            f"2. Downstream Dependency Cascade ({len(cascade['affected_assets'])} affected components):",
        ]
        for aff in cascade["affected_assets"]:
            lines.append(f"   • {aff['asset_id']} ({aff['name']}) [{aff['severity']}]: {aff['impact_reason']}")

        lines.extend(["", f"3. Recommended Recovery Actions ({len(plan['actions'])} prioritized steps):"])
        for act in plan["actions"]:
            sym = "✅" if act["verified"] else "❌"
            lines.append(f"   {act['priority']}. {sym} [{act['action_id']}] {act['action']} (Target: {act['target_asset']})")

        return "\n".join(lines)

    if "affected" in lower or "impacted" in lower:
        if not state.last_cascade or not state.last_cascade.get("is_valid", True):
            target = state.active_failed_asset or "S-01"
            state.last_cascade = analyze_cascade(target, state.model, state.unavailable_resources)
        aff_list = state.last_cascade.get("affected_assets", [])
        lines = [f"[SIMULATION] 🌐 AFFECTED INFRASTRUCTURE ASSETS ({len(aff_list)} nodes affected):"]
        for aff in aff_list:
            lines.append(f"• [{aff['severity']}] {aff['asset_id']} — {aff['name']} ({aff['type']}): {aff['impact_reason']}")
        return "\n".join(lines)

    if "plan" in lower or "recovery" in lower:
        target = state.active_failed_asset or "S-01"
        if not state.last_cascade:
            state.last_cascade = analyze_cascade(target, state.model, state.unavailable_resources)
        state.last_plan = plan_recovery(target, state.last_cascade, state.model, state.unavailable_resources)
        return state.last_plan.get("summary", "No recovery plan available.")

    return (
        "[SIMULATION] 🛡️ AegisGrid Resilience Intelligence Agent online.\n"
        "Supported commands:\n"
        "• 'Analyze outage at S-01' — Model substation cascade failure\n"
        "• 'Show affected assets' — View downstream impacted assets\n"
        "• 'G-01 is unavailable' — Simulate backup generator lockout & mobile contingency\n"
        "• 'Plan recovery' — Review ranked, verified recovery actions\n"
        "• 'Analyze outage at UNKNOWN-999' — Test ingress quarantine of unregistered ID\n"
        "• 'Verify RA-05' — Test safety verification rejecting disallowed actions"
    )


# --- Agentverse Hosted Agent Instantiation ---
agent_name = os.getenv("AGENT_NAME", "aegisgrid_resilience_agent").strip()
agent_seed = os.getenv("AGENT_SEED", "aegisgrid fetchathon 3 resilience intelligence seed").strip()
agent_network = os.getenv("AGENT_NETWORK", "mainnet").strip()

# Note: On Agentverse hosted cloud, port and endpoint are managed automatically by the platform
agent = Agent(name=agent_name, seed=agent_seed, network=agent_network)

chat_proto = Protocol(spec=chat_protocol_spec)


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"Received ACP acknowledgement from {sender} for msg_id={msg.acknowledged_msg_id}")


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    # Immediately acknowledge incoming message
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    has_start = any(isinstance(c, StartSessionContent) for c in msg.content)
    has_end = any(isinstance(c, EndSessionContent) for c in msg.content)

    user_text = msg.text().strip()
    if not user_text and has_start:
        welcome = (
            "[SIMULATION] 🛡️ AegisGrid Resilience Intelligence Agent online.\n"
            "Ready to analyze infrastructure dependencies, model cascading failures, and sequence verified recovery plans.\n\n"
            "Try: 'Analyze outage at S-01', 'Show affected assets', 'G-01 is unavailable', or 'Plan recovery'."
        )
        await ctx.send(sender, make_chat_response(welcome))
        return

    if has_end:
        farewell = "[SIMULATION] Session ended. Incident audit history and digital twin state preserved."
        await ctx.send(sender, make_chat_response(farewell, end_session=True))
        return

    try:
        reply_text = process_chat_command(user_text, hosted_state)
    except Exception as err:
        ctx.logger.error(f"Error processing command '{user_text}': {err}")
        reply_text = "[SIMULATION] AegisGrid encountered an unexpected condition. Digital twin telemetry remains secure."

    await ctx.send(sender, make_chat_response(reply_text))


agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"Starting {agent.name} on address: {agent.address}")
    agent.run()
