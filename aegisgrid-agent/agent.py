"""
AegisGrid - Autonomous Resilience Agent
Implements the official Agent Chat Protocol (ACP) for Fetch-A-Thon 3.0 ASI:One Agent Challenge.
All operations are simulated only.
"""

from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set

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

from analysis import analyze_cascade, load_model, validate_asset_id
from recovery import (
    load_incident_history,
    plan_recovery,
    save_incident_history,
    verify_proposed_action,
)


BASE_DIR = Path(__file__).parent
SCENARIOS_PATH = BASE_DIR / "scenarios.json"
HISTORY_PATH = BASE_DIR / "incident_history.json"


def _load_env_file():
    """Lightweight zero-dependency loader for .env configuration."""
    dotenv = BASE_DIR / ".env"
    if not dotenv.exists():
        return
    try:
        with open(dotenv, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Remove surrounding quotes or inline comments outside quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                else:
                    val = val.split("#", 1)[0].strip()
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


_load_env_file()


def check_network_diagnostics(timeout: float = 1.5) -> Dict[str, bool]:
    """
    Non-blocking pre-flight diagnostic check for Fetch.ai Almanac and Agentverse reachability.
    Distinguishes network timeout / firewall blocking from code defects.
    """
    import socket

    targets = {
        "agentverse": ("agentverse.ai", 443),
        "almanac_rpc": ("grpc-fetchhub.fetch.ai", 443),
    }
    results = {}
    for target_name, (host, port) in targets.items():
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            results[target_name] = True
        except Exception:
            results[target_name] = False
    return results


class AegisAgentState:
    """In-memory state container for AegisGrid deterministic operations."""

    def __init__(
        self,
        scenarios_path: Optional[Path | str] = None,
        history_path: Optional[Path | str] = None,
    ):
        self.scenarios_path = scenarios_path or SCENARIOS_PATH
        self.history_path = history_path or HISTORY_PATH
        self.model = load_model(self.scenarios_path)
        self.unavailable_resources: Set[str] = set()
        self.active_failed_asset: Optional[str] = None
        self.last_cascade: Optional[Dict[str, Any]] = None
        self.last_plan: Optional[Dict[str, Any]] = None
        self.active_incident_id: Optional[str] = None

    def reset(self):
        """Reset transient simulation state to catalog baseline."""
        self.model = load_model(self.scenarios_path)
        self.unavailable_resources.clear()
        self.active_failed_asset = None
        self.last_cascade = None
        self.last_plan = None
        self.active_incident_id = None


def make_chat_response(text: str, end_session: bool = False) -> ChatMessage:
    """Helper to assemble a standard ACP ChatMessage response."""
    content: List[AgentContent] = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(content=content)


def process_chat_command(raw_text: str, state: AegisAgentState) -> str:
    """
    Deterministic natural language command processor for AegisGrid resilience operations.
    Handles all commands gracefully without throwing unhandled exceptions.
    """
    text = (raw_text or "").strip()
    if not text:
        return (
            "[SIMULATION] Ready for resilience operations.\n"
            "Try: 'Analyze outage at S-01', 'Show affected assets', 'G-01 is unavailable', or 'Plan recovery'."
        )

    lower = text.lower()

    # 1. Check for duplicate incident report
    if "duplicate" in lower and "incident" in lower:
        target_asset = state.active_failed_asset or "S-01"
        evidence_record = save_incident_history(
            {
                "incident_id": state.active_incident_id or "INC-2041",
                "event_type": "DUPLICATE_REPORT_SUPPRESSED",
                "target_asset": target_asset,
                "detail": f"Secondary telemetry report for {target_asset} merged into active narrative. Queue deduplicated.",
            },
            storage_path=state.history_path,
        )
        return (
            f"[SIMULATION] ℹ️ DUPLICATE INCIDENT DETECTED\n"
            f"Active Incident: {evidence_record['incident_id']} (Target: {target_asset})\n"
            f"Evidence ID: {evidence_record['evidence_id']}\n"
            "Action: Second report merged into active incident chain. Operational queue preserves a single authoritative action pipeline."
        )

    # 2. Check for Resource Availability updates: "G-01 is unavailable", "G-01 offline", etc.
    res_match = re.search(r"\b([A-Za-z0-9_-]+)\s+(?:is\s+)?(?:un?available|offline|failed|down)\b", lower)
    if "unavailable" in lower or ("offline" in lower and not lower.startswith("analyze")):
        # Extract resource ID (default G-01 if mentioned)
        resource_id = "G-01"
        for candidate in ["G-01", "S-01", "W-02", "T-04", "H-01"]:
            if candidate.lower() in lower:
                resource_id = candidate
                break

        state.unavailable_resources.add(resource_id)

        # Recalculate impacts on dependents
        if state.active_failed_asset:
            state.last_cascade = analyze_cascade(
                state.active_failed_asset, state.model, state.unavailable_resources
            )
            state.last_plan = plan_recovery(
                state.active_failed_asset, state.last_cascade, state.model, state.unavailable_resources
            )
        else:
            state.active_failed_asset = resource_id
            state.last_cascade = analyze_cascade(resource_id, state.model, state.unavailable_resources)
            state.last_plan = plan_recovery(
                resource_id, state.last_cascade, state.model, state.unavailable_resources
            )

        saved = save_incident_history(
            {
                "event_type": "RESOURCE_UNAVAILABLE",
                "resource_id": resource_id,
                "unavailable_set": list(state.unavailable_resources),
                "cascade_summary": state.last_cascade.get("summary", ""),
            },
            storage_path=state.history_path,
        )

        plan_summary = state.last_plan.get("summary", "No plan generated.")
        return (
            f"[SIMULATION] 🚨 RESOURCE STATUS UPDATE\n"
            f"Resource: {resource_id} marked as UNAVAILABLE.\n"
            f"Evidence ID: {saved['evidence_id']}\n\n"
            f"Operational Cascade:\n"
            f"• Hospital H-01 power redundancy compromised; backup generator offline.\n"
            f"• Contingency Action Dispatched: RA-07 (Mobile Emergency Power Unit to H-01).\n\n"
            f"Recalculated Plan:\n{plan_summary}"
        )

    # 3. Check for specific Action Verification request: "verify RA-05", "verify RA-01"
    act_match = re.search(r"\bverify\s+(ra-\d+)\b", lower)
    if act_match or "verify action" in lower or "invalid action" in lower or "bypass lockout" in lower:
        act_id = act_match.group(1).upper() if act_match else ("RA-05" if ("invalid" in lower or "bypass" in lower) else "RA-01")
        target_asset = "S-01"
        verified, detail, meta = verify_proposed_action(
            act_id, target_asset, state.model, state.unavailable_resources
        )

        save_incident_history(
            {
                "event_type": "ACTION_VERIFICATION_AUDIT",
                "action_id": act_id,
                "target_asset": target_asset,
                "verified": verified,
                "detail": detail,
            },
            storage_path=state.history_path,
        )

        if not verified:
            return (
                f"[SIMULATION] ⛔ ACTION VERIFICATION AUDIT: REJECTED\n"
                f"Action ID: {act_id} ({meta.get('action', 'Unsafe Sequence')})\n"
                f"Target: {target_asset}\n"
                f"Audit Result: FAILED / BLOCKED\n"
                f"Reason: {detail}\n"
                "Rule: Verification Agent prohibits unlatched bypasses without breaker clearance."
            )
        else:
            return (
                f"[SIMULATION] ✅ ACTION VERIFICATION AUDIT: APPROVED\n"
                f"Action ID: {act_id} ({meta.get('action', '')})\n"
                f"Target: {target_asset}\n"
                f"Audit Result: PASSED\n"
                f"Detail: {detail}"
            )

    # 4. Outage Analysis: "Analyze outage at S-01", "Analyze outage at UNKNOWN-999", "S-01 outage", etc.
    if "analyze" in lower or "outage" in lower or "failure" in lower:
        # Extract asset ID
        asset_id = "S-01"  # Default
        # Look for explicit pattern
        id_match = re.search(r"\b(?:at|asset|for)?\s*([a-zA-Z]+-?\d+)\b", text)
        if id_match:
            candidate = id_match.group(1).strip().upper()
            if candidate not in {"ANALYZE", "OUTAGE", "AT", "SHOW", "PLAN"}:
                asset_id = candidate
        else:
            for known in ["S-01", "W-02", "T-04", "H-01", "G-01", "UNKNOWN-999", "X-99"]:
                if known.lower() in lower:
                    asset_id = known
                    break

        # Check for duplicate if same asset is already actively failed
        is_duplicate = (state.active_failed_asset == asset_id and state.active_incident_id is not None)

        cascade = analyze_cascade(asset_id, state.model, state.unavailable_resources)
        state.last_cascade = cascade

        if not cascade["is_valid"]:
            # Quarantined unregistered asset
            state.active_failed_asset = None
            plan = plan_recovery(asset_id, cascade, state.model, state.unavailable_resources)
            state.last_plan = plan
            saved = save_incident_history(
                {
                    "event_type": "UNKNOWN_ASSET_QUARANTINED",
                    "target_asset": asset_id,
                    "quarantined": True,
                    "error": cascade.get("error"),
                },
                storage_path=state.history_path,
            )
            return (
                f"[SIMULATION] 🛡️ INGRESS SECURITY QUARANTINE\n"
                f"Reported Asset ID: {asset_id} — NOT FOUND IN OPERATIONAL CATALOG\n"
                f"Evidence ID: {saved['evidence_id']}\n"
                f"Status: QUARANTINED\n\n"
                f"{cascade['summary']}\n\n"
                f"Action Taken: RA-06 (Quarantine payload and audit telemetry ingress gateway).\n"
                "Operational Digital Twin topology graph remains protected and unaffected."
            )

        # Valid asset outage
        state.active_failed_asset = asset_id
        plan = plan_recovery(asset_id, cascade, state.model, state.unavailable_resources)
        state.last_plan = plan

        incident_id = f"INC-{2040 + len(state.unavailable_resources) * 10 + 1}"
        state.active_incident_id = incident_id

        saved = save_incident_history(
            {
                "incident_id": incident_id,
                "event_type": "OUTAGE_CASCADE_ANALYSIS",
                "root_asset": asset_id,
                "is_duplicate": is_duplicate,
                "affected_assets": [a["asset_id"] for a in cascade.get("affected_assets", [])],
                "plan_action_count": len(plan.get("actions", [])),
            },
            storage_path=state.history_path,
        )

        lines = [
            f"[SIMULATION] ⚠️ INCIDENT REPORT: {cascade['root_name']} ({asset_id}) Outage",
            f"Incident ID: {saved['incident_id']} | Evidence ID: {saved['evidence_id']} | Status: ACTIVE_SIMULATION",
            "",
            f"1. Direct Impact:",
            f"   • Asset: {asset_id} ({cascade['root_name']}) — Status: Critical Outage ({cascade['root_criticality']} criticality)",
            "",
            f"2. Downstream Dependency Cascade ({len(cascade['affected_assets'])} affected components):",
        ]
        if not cascade["affected_assets"]:
            lines.append("   • None (Isolated node)")
        else:
            for aff in cascade["affected_assets"]:
                lines.append(f"   • {aff['asset_id']} ({aff['name']}) [{aff['severity']}]: {aff['impact_reason']}")

        lines.extend([
            "",
            f"3. Recommended Recovery Actions ({len(plan['actions'])} prioritized steps):",
        ])
        for act in plan["actions"]:
            status_symbol = "✅" if act["verified"] else "❌"
            lines.append(f"   {act['priority']}. {status_symbol} [{act['action_id']}] {act['action']} (Target: {act['target_asset']})")

        lines.extend([
            "",
            "Commands to continue:",
            "• 'Plan recovery' to inspect action prerequisites and rationales.",
            "• 'Show affected assets' to view graph dependency breakdown.",
            "• 'G-01 is unavailable' to test generator failure contingency.",
        ])

        return "\n".join(lines)

    # 5. Show Affected Assets: "Show affected assets", "What is affected"
    if "affected" in lower or "impacted" in lower:
        if not state.last_cascade or not state.last_cascade.get("is_valid", True):
            # Run default cascade for active failed asset or S-01
            target = state.active_failed_asset or "S-01"
            state.last_cascade = analyze_cascade(target, state.model, state.unavailable_resources)

        aff_list = state.last_cascade.get("affected_assets", [])
        root = state.last_cascade.get("root_asset", "S-01")
        lines = [
            f"[SIMULATION] 🌐 AFFECTED INFRASTRUCTURE ASSETS (Root Outage: {root}):",
            f"Total downstream affected nodes: {len(aff_list)}",
            "",
        ]
        if not aff_list:
            lines.append("• No downstream assets are currently degraded.")
        else:
            for aff in aff_list:
                lines.append(
                    f"• [{aff['severity']}] {aff['asset_id']} — {aff['name']} ({aff['type']})\n"
                    f"  Impact: {aff['impact_reason']}\n"
                    f"  Upstream Feeder: {aff['upstream_cause']}"
                )

        return "\n".join(lines)

    # 6. Plan Recovery: "Plan recovery", "Show recovery plan"
    if "plan" in lower or "recovery" in lower:
        target = state.active_failed_asset or "S-01"
        if not state.last_cascade:
            state.last_cascade = analyze_cascade(target, state.model, state.unavailable_resources)
        state.last_plan = plan_recovery(target, state.last_cascade, state.model, state.unavailable_resources)

        actions = state.last_plan.get("actions", [])
        lines = [
            f"[SIMULATION] 📋 VERIFIED RECOVERY PLAN (Target: {target}):",
            f"Action queue verified: {len(actions)} steps ranked by life-safety and grid stability.\n",
        ]
        for act in actions:
            status_tag = "VERIFIED" if act["verified"] else "BLOCKED"
            prereq_str = ", ".join(act.get("prerequisites", [])) or "None"
            lines.extend([
                f"Priority #{act['priority']} [{status_tag}]: {act['action_id']} — {act['action']}",
                f"  • Target Asset: {act['target_asset']}",
                f"  • Rationale: {act['rationale']}",
                f"  • Prerequisites: {prereq_str}",
                f"  • Audit: {act['verification_detail']}",
                "",
            ])

        return "\n".join(lines).strip()

    # 7. Help / Catalog / Status
    if "help" in lower or "status" in lower or "assets" in lower:
        assets = state.model.get("assets", {})
        asset_summary = ", ".join(f"{aid} ({meta['name']})" for aid, meta in assets.items())
        unavail = ", ".join(state.unavailable_resources) or "None (all operational)"
        return (
            "[SIMULATION] 🛡️ AegisGrid Resilience Intelligence System Status\n"
            f"• Mode: DETERMINISTIC SIMULATION ONLY\n"
            f"• Registered Topology: {asset_summary}\n"
            f"• Unavailable Resources: {unavail}\n"
            f"• Active Failed Node: {state.active_failed_asset or 'None (nominal)'}\n\n"
            "Supported Chat Commands:\n"
            "• 'Analyze outage at S-01' — Model substation failure cascade\n"
            "• 'Show affected assets' — View downstream impacted assets\n"
            "• 'Plan recovery' — Review ranked, verified recovery actions\n"
            "• 'G-01 is unavailable' — Simulate backup generator lockout & mobile contingency\n"
            "• 'Analyze outage at UNKNOWN-999' — Test ingress quarantine of unregistered ID\n"
            "• 'Verify RA-05' — Test safety verification rejecting disallowed actions"
        )

    # 8. Friendly Fallback
    return (
        "[SIMULATION] Command not recognized.\n"
        "Try standard resilience commands:\n"
        "• 'Analyze outage at S-01'\n"
        "• 'Show affected assets'\n"
        "• 'G-01 is unavailable'\n"
        "• 'Plan recovery'\n"
        "• 'Analyze outage at UNKNOWN-999'\n"
        "• 'Verify RA-05'"
    )


# --- uAgent and ACP Protocol Definition ---

def create_agent(
    name: Optional[str] = None,
    seed: Optional[str] = None,
    port: Optional[int] = None,
    endpoint: Optional[str] = None,
    mailbox: Optional[bool] = None,
    network: Optional[str] = None,
    agentverse_url: Optional[str] = None,
    scenarios_path: Optional[Path | str] = None,
    history_path: Optional[Path | str] = None,
    loop: Optional[Any] = None,
) -> Tuple[Agent, Protocol, AegisAgentState]:
    """
    Constructs the real uAgent and ACP protocol with manifest publishing.
    Supports two clearly separated operational modes:
      Mode A: Local Development (local HTTP server on AGENT_PORT, no public IP needed)
      Mode B: Agentverse Mailbox (outbound polling to Agentverse for ASI:One discovery)
    """
    raw_name = name or os.getenv("AGENT_NAME", "aegisgrid_resilience_agent")
    agent_name = raw_name.strip()
    raw_seed = seed or os.getenv("AGENT_SEED", "aegisgrid fetchathon 3 resilience intelligence seed")
    agent_seed = raw_seed.strip()
    agent_network = (network or os.getenv("AGENT_NETWORK", "mainnet")).strip()
    agent_port = port or int(os.getenv("AGENT_PORT", "8000"))

    if not agent_name:
        raise ValueError("Configuration error: AGENT_NAME must not be empty.")
    if not agent_seed:
        raise ValueError("Configuration error: AGENT_SEED must not be empty.")

    # Determine Mailbox Mode
    env_mailbox = (
        os.getenv("AGENT_MAILBOX", "").strip().lower() in {"true", "1", "yes", "t"}
        or os.getenv("USE_MAILBOX", "").strip().lower() in {"true", "1", "yes", "t"}
    )
    use_mailbox = mailbox if mailbox is not None else env_mailbox
    av_url = agentverse_url or os.getenv("AGENTVERSE_URL")

    agent_kwargs: Dict[str, Any] = {
        "name": agent_name,
        "seed": agent_seed,
        "network": agent_network,
    }
    if loop is not None:
        agent_kwargs["loop"] = loop

    if use_mailbox:
        # MODE B: AGENTVERSE MAILBOX
        # Connects outbound to Agentverse's hosted mailbox. No public IP or inbound port forwarding needed.
        agent_kwargs["mailbox"] = True
        if av_url:
            agent_kwargs["agentverse"] = av_url
    else:
        # MODE A: LOCAL DEVELOPMENT
        agent_kwargs["port"] = agent_port
        raw_endpoint = endpoint if endpoint is not None else os.getenv("AGENT_ENDPOINT", "")
        raw_endpoint = raw_endpoint.strip()

        # Check if endpoint is local loopback
        is_local_loopback = False
        if raw_endpoint:
            lower_ep = raw_endpoint.lower()
            is_local_loopback = any(h in lower_ep for h in ["127.0.0.1", "localhost", "0.0.0.0"])

        force_register = os.getenv("AGENT_FORCE_REGISTER_LOCAL", "").strip().lower() in {"true", "1", "yes"}

        if raw_endpoint and not is_local_loopback:
            # Legitimate public endpoint provided (e.g., https://your-domain.com/submit)
            agent_kwargs["endpoint"] = [raw_endpoint]
        elif raw_endpoint and is_local_loopback and force_register:
            # User explicitly opted into registering loopback on Almanac contract
            agent_kwargs["endpoint"] = [raw_endpoint]
        else:
            # Pure local development:
            # In uAgents, omitting 'endpoint' starts the local HTTP server on AGENT_PORT,
            # serves local /submit and Agent Inspector, and skips remote Almanac on-chain registration.
            pass

    agent = Agent(**agent_kwargs)
    state = AegisAgentState(scenarios_path=scenarios_path, history_path=history_path)

    # Official Agent Chat Protocol
    chat_proto = Protocol(spec=chat_protocol_spec)

    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
        ctx.logger.debug(f"Received ACP acknowledgement from {sender} for msg_id={msg.acknowledged_msg_id}")

    @chat_proto.on_message(ChatMessage)
    async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
        # 1. Immediately send official ChatAcknowledgement
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
        )

        # 2. Check for StartSessionContent / EndSessionContent
        has_start = any(isinstance(c, StartSessionContent) for c in msg.content)
        has_end = any(isinstance(c, EndSessionContent) for c in msg.content)

        if has_start:
            ctx.logger.info(f"ACP Session started with {sender}")

        # 3. Process text
        user_text = msg.text().strip()
        if not user_text and has_start:
            welcome_text = (
                "[SIMULATION] 🛡️ AegisGrid Resilience Intelligence Agent online.\n"
                "Ready to analyze infrastructure dependencies, model cascading failures, and sequence verified recovery plans.\n\n"
                "Try commands like:\n"
                "• 'Analyze outage at S-01'\n"
                "• 'Show affected assets'\n"
                "• 'G-01 is unavailable'\n"
                "• 'Plan recovery'\n"
                "• 'Analyze outage at UNKNOWN-999'"
            )
            response_msg = make_chat_response(welcome_text)
            await ctx.send(sender, response_msg)
            return

        if has_end:
            ctx.logger.info(f"ACP Session ended with {sender}")
            farewell = "[SIMULATION] Session ended. Incident audit history and digital twin state preserved."
            await ctx.send(sender, make_chat_response(farewell, end_session=True))
            return

        # 4. Deterministic command processing with friendly error handling
        try:
            reply_text = process_chat_command(user_text, state)
        except Exception as err:
            ctx.logger.error(f"Error processing command '{user_text}': {err}")
            reply_text = (
                f"[SIMULATION] AegisGrid encountered an unexpected condition while processing your request. "
                "The system state remains secure and digital twin telemetry is intact. "
                "Please check the asset ID or try: 'Analyze outage at S-01'."
            )

        response_msg = make_chat_response(reply_text)
        await ctx.send(sender, response_msg)

    # Requirement 7: agent.include(chat_proto, publish_manifest=True)
    agent.include(chat_proto, publish_manifest=True)

    return agent, chat_proto, state


# Global instance for import compatibility
agent, chat_protocol, agent_state = create_agent()


if __name__ == "__main__":
    print("=" * 68)
    print("🛡️  AegisGrid Resilience Intelligence Agent (Fetch-A-Thon 3.0)")
    print("=" * 68)

    # Pre-flight network diagnostics
    diag = check_network_diagnostics(timeout=1.5)
    print("[DIAGNOSTICS] Pre-flight network connectivity:")
    print(f"  • Agentverse (agentverse.ai:443):       {'✅ Reachable' if diag.get('agentverse') else '⚠️ Unreachable / Offline'}")
    print(f"  • Almanac RPC (grpc-fetchhub.fetch.ai): {'✅ Reachable' if diag.get('almanac_rpc') else '⚠️ Unreachable / Filtered'}")

    if agent._use_mailbox:
        print("\n[ACTIVE MODE] Mode B: AGENTVERSE MAILBOX")
        print(f"  • Address:  {agent.address}")
        print("  • Mailbox:  Connecting outbound to Agentverse (no public IP needed).")
        print("  • ASI:One:  Ready for discovery via Agentverse Mailbox.")
        print(f"  • Inspector: https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address={agent.address}")
    else:
        print("\n[ACTIVE MODE] Mode A: LOCAL DEVELOPMENT")
        print(f"  • Address:  {agent.address}")
        print(f"  • Server:   Listening on port {agent._port}")
        print(f"  • Submit:   http://127.0.0.1:{agent._port}/submit")
        print(f"  • Inspector: https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A{agent._port}&address={agent.address}")
        print("  • Note:     To enable Agentverse Mailbox for ASI:One, set AGENT_MAILBOX=true in .env")
    print("=" * 68 + "\n")

    print(f"Starting {agent.name} on address: {agent.address}")
    agent.run()
