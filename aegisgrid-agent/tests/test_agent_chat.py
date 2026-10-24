"""
Unit and integration tests for AegisGrid uAgent ACP chat interactions.
"""

from pathlib import Path
import pytest
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
)

from agent import (
    AegisAgentState,
    check_network_diagnostics,
    create_agent,
    make_chat_response,
    process_chat_command,
)


@pytest.fixture
def agent_state(tmp_path: Path):
    history_file = tmp_path / "test_agent_history.json"
    return AegisAgentState(history_path=history_file)


def test_command_analyze_s01(agent_state):
    reply = process_chat_command("Analyze outage at S-01", agent_state)

    assert "[SIMULATION]" in reply
    assert "S-01" in reply
    assert "W-02" in reply
    assert "T-04" in reply
    assert "H-01" in reply
    assert "RA-01" in reply
    assert agent_state.active_failed_asset == "S-01"


def test_command_show_affected_assets(agent_state):
    # First trigger analysis
    process_chat_command("Analyze outage at S-01", agent_state)

    # Then request affected assets
    reply = process_chat_command("Show affected assets", agent_state)

    assert "[SIMULATION]" in reply
    assert "W-02" in reply
    assert "T-04" in reply
    assert "H-01" in reply
    assert "Loss of primary electrical supply" in reply


def test_command_plan_recovery(agent_state):
    process_chat_command("Analyze outage at S-01", agent_state)
    reply = process_chat_command("Plan recovery", agent_state)

    assert "[SIMULATION]" in reply
    assert "VERIFIED RECOVERY PLAN" in reply
    assert "RA-01" in reply
    assert "RA-04" in reply
    assert "RA-02" in reply
    assert "RA-03" in reply
    assert "Prerequisites:" in reply


def test_command_g01_unavailable(agent_state):
    reply = process_chat_command("G-01 is unavailable", agent_state)

    assert "[SIMULATION]" in reply
    assert "G-01" in reply
    assert "UNAVAILABLE" in reply
    assert "H-01" in reply
    # Should trigger RA-07 mobile generator contingency
    assert "RA-07" in reply
    assert "G-01" in agent_state.unavailable_resources


def test_command_unknown_asset_quarantine(agent_state):
    reply = process_chat_command("Analyze outage at UNKNOWN-999", agent_state)

    assert "[SIMULATION]" in reply
    assert "QUARANTINE" in reply
    assert "UNKNOWN-999" in reply
    assert "RA-06" in reply
    assert "protected" in reply.lower()


def test_command_verify_invalid_action(agent_state):
    reply = process_chat_command("Verify RA-05", agent_state)

    assert "[SIMULATION]" in reply
    assert "REJECTED" in reply
    assert "RA-05" in reply
    assert "unsafe sequence" in reply.lower() or "breaker" in reply.lower()


def test_duplicate_incident_handling(agent_state):
    # Trigger first incident
    process_chat_command("Analyze outage at S-01", agent_state)
    assert agent_state.active_incident_id is not None

    # Trigger duplicate report
    reply = process_chat_command("Duplicate incident report for S-01", agent_state)

    assert "[SIMULATION]" in reply
    assert "DUPLICATE INCIDENT DETECTED" in reply
    assert "merged into active incident chain" in reply.lower()


def test_malformed_input_does_not_crash(agent_state):
    malformed_inputs = [
        "",
        "   ",
        "???!!!",
        "asdf qwer zxcv 12345",
        "what is the weather today?",
        "DROP TABLE assets;--",
        "None",
        "!@#$%^&*()_+",
    ]
    for inp in malformed_inputs:
        reply = process_chat_command(inp, agent_state)
        assert isinstance(reply, str)
        assert len(reply) > 0
        assert "[SIMULATION]" in reply
        # No unhandled python tracebacks
        assert "traceback" not in reply.lower()


def test_acp_message_and_acknowledgement_types():
    msg = ChatMessage(content=[TextContent(type="text", text="Analyze outage at S-01")])
    assert msg.text() == "Analyze outage at S-01"
    assert msg.msg_id is not None

    ack = ChatAcknowledgement(
        timestamp=msg.timestamp,
        acknowledged_msg_id=msg.msg_id,
    )
    assert ack.acknowledged_msg_id == msg.msg_id


def test_agent_creation_with_chat_protocol(tmp_path: Path):
    hist = tmp_path / "test_create_history.json"
    agent, proto, state = create_agent(
        name="test_resilience_agent",
        seed="test seed for aegisgrid test suite",
        port=8099,
        history_path=hist,
    )

    assert agent.name == "test_resilience_agent"
    assert agent.address.startswith("agent1")
    # Verify protocol was registered and manifest can be published
    assert proto.canonical_name == "AgentChatProtocol:0.3.0"
    assert len(proto.models) > 0
    assert proto in agent.protocols.values()


def test_agent_creation_mailbox_mode(tmp_path: Path):
    hist = tmp_path / "test_mb_history.json"
    agent, proto, state = create_agent(
        name="test_mb_agent",
        seed="test seed for mailbox agent test",
        mailbox=True,
        history_path=hist,
    )
    assert agent.name == "test_mb_agent"
    assert agent._use_mailbox is True
    assert any("mailbox" in ep.url for ep in agent._endpoints)


def test_hosted_agent_flow():
    import hosted_agent
    state = hosted_agent.HostedAgentState()
    
    # S-01 Analysis
    res1 = hosted_agent.process_chat_command("Analyze outage at S-01", state)
    assert "[SIMULATION]" in res1
    assert "S-01" in res1
    assert "W-02" in res1

    # G-01 Unavailable
    res2 = hosted_agent.process_chat_command("G-01 is unavailable", state)
    assert "UNAVAILABLE" in res2
    assert "RA-07" in res2

    # Unknown asset quarantine
    res3 = hosted_agent.process_chat_command("Analyze outage at UNKNOWN-999", state)
    assert "QUARANTINE" in res3
    assert "RA-06" in res3

    # Disallowed action
    res4 = hosted_agent.process_chat_command("Verify RA-05", state)
    assert "REJECTED" in res4


def test_network_diagnostics_preflight():
    results = check_network_diagnostics(timeout=0.5)
    assert isinstance(results, dict)
    assert "agentverse" in results
    assert "almanac_rpc" in results
    assert isinstance(results["agentverse"], bool)
    assert isinstance(results["almanac_rpc"], bool)


def test_create_agent_validation_empty_identity():
    with pytest.raises(ValueError, match="AGENT_NAME must not be empty"):
        create_agent(name="   ")

    with pytest.raises(ValueError, match="AGENT_SEED must not be empty"):
        create_agent(seed="   ")


def test_local_mode_loopback_skips_endpoints(tmp_path: Path):
    hist = tmp_path / "test_local_loopback_hist.json"
    agent, proto, state = create_agent(
        name="test_local_agent",
        seed="test seed for local loopback test",
        port=8080,
        endpoint="http://127.0.0.1:8080/submit",
        mailbox=False,
        history_path=hist,
    )
    # Loopback endpoint must be omitted from agent._endpoints so remote Almanac
    # registration is skipped and initialization does not stall on blockchain queries.
    assert agent._endpoints == []
    assert agent._use_mailbox is False
    assert agent._port == 8080


def test_public_endpoint_preserved_for_external_mode(tmp_path: Path):
    hist = tmp_path / "test_public_ep_hist.json"
    agent, proto, state = create_agent(
        name="test_ext_agent",
        seed="test seed for external agent test",
        endpoint="https://aegisgrid.onrender.com/submit",
        mailbox=False,
        history_path=hist,
    )
    assert len(agent._endpoints) == 1
    assert agent._endpoints[0].url == "https://aegisgrid.onrender.com/submit"
    assert agent._use_mailbox is False


def test_acp_session_content_helpers():
    # Ordinary response
    msg_normal = make_chat_response("Hello AegisGrid", end_session=False)
    assert len(msg_normal.content) == 1
    assert isinstance(msg_normal.content[0], TextContent)
    assert msg_normal.content[0].text == "Hello AegisGrid"

    # End session response
    msg_end = make_chat_response("Goodbye", end_session=True)
    assert len(msg_end.content) == 2
    assert isinstance(msg_end.content[0], TextContent)
    assert isinstance(msg_end.content[1], EndSessionContent)


def test_incident_history_append_only(tmp_path: Path):
    hist_file = tmp_path / "ledger_audit.json"
    state = AegisAgentState(history_path=hist_file)

    # Trigger outage at S-01
    process_chat_command("Analyze outage at S-01", state)
    # Trigger G-01 unavailable
    process_chat_command("G-01 is unavailable", state)
    # Quarantine unknown asset
    process_chat_command("Analyze outage at UNKNOWN-999", state)

    assert hist_file.exists()
    import json
    data = json.loads(hist_file.read_text(encoding="utf-8"))
    assert len(data) >= 3
    event_types = [entry.get("event_type") for entry in data]
    assert "OUTAGE_CASCADE_ANALYSIS" in event_types
    assert "RESOURCE_UNAVAILABLE" in event_types
    assert "UNKNOWN_ASSET_QUARANTINED" in event_types


