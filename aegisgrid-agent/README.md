# AegisGrid Autonomous Resilience Agent

> **Fetch-A-Thon 3.0 — ASI:One Agent Challenge**  
> Fictional Infrastructure Resilience Intelligence & Dependency Cascade Recovery

AegisGrid is a deterministic, dependency-aware backend agent built with Fetch.ai's official `uagents` framework and implementing the **Agent Chat Protocol (ACP)** (`AgentChatProtocol:0.3.0`).

The agent models cascading multi-sector infrastructure outages across electrical distribution, municipal water pumping, traffic signaling, and hospital critical care systems without calling non-deterministic external LLMs or vector databases.

---

## ⚠️ Simulation Disclaimer
All actions, topology updates, and recovery workflows executed by AegisGrid are **strictly simulated**. AegisGrid operates on a fictional municipal infrastructure model and never claims that simulated actions have repaired or altered real-world physical infrastructure.

---

## Architecture & Capabilities

```
                  +-----------------------------------+
                  |           ASI:One Chat            |
                  +-----------------------------------+
                                    | (Agent Chat Protocol)
                                    v
                  +-----------------------------------+
                  |     aegisgrid_resilience_agent    |
                  |             (agent.py)            |
                  +-----------------------------------+
                   /                |                \
                  v                 v                 v
        +-------------------+ +-------------+ +--------------------+
        |  Cascade Engine   | |   Planner   | | Verification Engine|
        |   (analysis.py)   | |(recovery.py)| |   (recovery.py)    |
        +-------------------+ +-------------+ +--------------------+
                  |                 |                 |
                  +--------> [scenarios.json] <-------+
                                    |
                                    v
                       [incident_history.json]
                         (Persistent Ledger)
```

1. **Deterministic Cascade Analysis (`analysis.py`)**:
   - Validates asset IDs against the registered operational catalog.
   - Traverses explicit downstream dependencies (never invents relationships at runtime).
   - Models cascading failure paths (e.g. Electrical Substation `S-01` outage propagating to Water Pump `W-02`, Traffic Signals `T-04`, and Hospital `H-01`).
   - Quarantines uncataloged assets (e.g. `UNKNOWN-999` or `X-99`) at ingress to protect the operational topology.

2. **Dependency-Aware Recovery Planner (`recovery.py`)**:
   - Sequences recovery actions using explicit life-safety and grid stability ranking rules.
   - Respects dynamic resource constraints (e.g., if Generator `G-01` is unavailable, switches from `RA-04` to `RA-07` mobile generator dispatch).
   - Rejects disallowed sequences (e.g., Action `RA-05` proposing breaker lockout bypass without verifier clearance).

3. **Audit Ledger & State Persistence (`recovery.py`)**:
   - Persists incident records, evidence IDs, and UTC timestamps to `incident_history.json` without overwriting historical records.
   - Merges duplicate incident reports into active chains to preserve a single authoritative queue.

4. **Official Agent Chat Protocol (`agent.py`)**:
   - Implements `uagents_core.contrib.protocols.chat` with `chat_protocol_spec`.
   - Sends immediate `ChatAcknowledgement` for every incoming message.
   - Handles `TextContent`, `StartSessionContent`, and `EndSessionContent`.
   - Publishes ACP manifest via `agent.include(chat_proto, publish_manifest=True)`.

---

## Fictional Infrastructure Topology

| Asset ID | Name | Sector | Type | Dependencies | Downstream Dependents | Default Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S-01** | Electrical Substation | Sector 1 | Electrical | None | `W-02`, `T-04`, `H-01` | Primary distribution feeder |
| **W-02** | Water Pump Station | Sector 2 | Water | `S-01` | `H-01` | Municipal & chiller water pressure |
| **T-04** | Traffic Signals & Corridor | Sector 4 | Traffic | `S-01` | `H-01` | Emergency vehicle arterial route |
| **H-01** | Hospital Critical Care | Sector 3 | Healthcare | `S-01`, `G-01`, `W-02`| None | Regional emergency trauma center |
| **G-01** | Backup Generator Station | Sector 1 | Backup | None | `H-01` | Dedicated secondary power reserve |

---

## Chat Commands Supported

The agent recognizes natural language chat requests through ASI:One / ACP:

| User Query | Agent Execution |
| :--- | :--- |
| `"Analyze outage at S-01"` | Models S-01 cascade across W-02, T-04, and H-01; generates initial recovery plan; persists incident record. |
| `"Show affected assets"` | Breaks down currently degraded nodes, impact reasons, and upstream feeder links. |
| `"Plan recovery"` | Returns ranked, verified recovery actions with prerequisites and safety audits. |
| `"G-01 is unavailable"` | Marks G-01 offline, detects single-point hospital failure risk, recalculates plan to dispatch mobile fleet `RA-07`. |
| `"Analyze outage at UNKNOWN-999"` | Quarantines unregistered asset at intake gateway; digital twin remains unaffected. |
| `"Verify RA-05"` | Submits unsafe bypass action to verifier; rejects it with policy rationale. |
| `"Duplicate incident report for S-01"` | Merges repeat report into active incident chain; deduplicates action queue. |
| `"Help"` or `"Status"` | Displays registered topology, unavailable resources, and active incident state. |

---

## Local Development & Setup

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13.

### 2. Virtual Environment Setup
```bash
cd aegisgrid-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Automated Test Suite
```bash
pytest tests/ -v
```
All 29 unit and integration tests cover:
- S-01 failure and downstream impact traversal
- G-01 unavailable and contingency plan recalculation
- Unknown asset quarantine (`UNKNOWN-999`)
- Disallowed action rejection (`RA-05`)
- Missing prerequisites and unavailable resource blocking
- Duplicate incident deduplication
- JSON history persistence across multiple events
- Malformed inputs, fuzzing, and error recovery
- Agent ACP protocol initialization and manifest publication
- Mode A (local development) loopback endpoint skipping
- Mode B (Agentverse Mailbox) configuration
- Pre-flight network diagnostics

### 4. Run the Local End-to-End Simulation
To observe a full conversation simulation through all scenarios:
```bash
python simulation.py
```

### 5. Run the Live uAgent Locally (Mode A: Local Development)
```bash
python agent.py
```
Starts a local HTTP server on `http://127.0.0.1:8000/submit` and displays the Agent Inspector link. Pure local development skips remote Almanac on-chain registration to prevent initialization stalls on network lag.

---

## Agentverse & ASI:One Deployment Workflows

There are two primary ways to connect AegisGrid to Agentverse and ASI:One:

### Route 1: Agentverse Cloud Hosted Agent (Zero Local Infrastructure)
*Use this route if you want the agent running 24/7 in the cloud without keeping your laptop on.*

1. Log in to [Agentverse.ai](https://agentverse.ai/).
2. Navigate to **Agents** &rarr; **+ New Agent** &rarr; Select **Blank Agent**.
3. Name your agent `aegisgrid_resilience_agent`.
4. Copy the entire contents of `hosted_agent.py` (which is 100% self-contained with embedded scenarios and in-memory ledger) and paste it into the Agentverse Web Code Editor.
5. *(Optional)* Under the agent's **Secrets** tab, add `AGENT_SEED` if you wish to use a custom private seed.
6. Click **Start** to run the agent in Agentverse's cloud container.
7. Verify that the agent badge turns green (`Running`) and that `AgentChatProtocol` is listed under the Protocols tab.
8. Go to [ASI:One](https://asi1.ai/) chat, search for your agent's address or name, and test: `"Analyze outage at S-01"`.

---

### Route 2: Local Agent via Agentverse Mailbox (Local Execution + Cloud Discovery)
*Use this route to run the multi-file architecture (`agent.py`, `analysis.py`, `recovery.py`, `scenarios.json`) on your machine while receiving messages from ASI:One through Agentverse's outbound polling mailbox.*

1. In `aegisgrid-agent/.env`, set:
   ```env
   AGENT_MAILBOX=true
   ```
2. Start the agent:
   ```bash
   python agent.py
   ```
3. Look at the terminal output for the Agent Inspector URL:
   ```text
   Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address=agent1...
   ```
4. Click the URL in your browser (while logged into Agentverse).
5. On the Inspector page, click **Connect to Mailbox**.
   Agentverse authenticates with your local agent and provisions the mailbox queue for your agent's address.
6. The terminal will log:
   ```text
   INFO: Starting mailbox client for https://agentverse.ai
   ```
   The local agent is now actively listening for incoming ASI:One messages via outbound long-polling! No public IP, port forwarding, or domain is required.

---

### ⚠️ Note on Agentverse "External Integration"
Agentverse includes an "External Integration" wizard that asks for an **Agent Endpoint URL**.
- **Do NOT enter `http://127.0.0.1:8000/submit` or `localhost`** into this form. Agentverse cloud servers cannot reach your computer's local loopback network.
- The External Integration wizard is only for agents deployed on legitimate public cloud hosting (e.g. Render, Railway, AWS EC2, Fly.io) with a public domain and valid SSL certificate (e.g. `https://my-agent.onrender.com/submit`).
- For running on your local machine, use **Route 2 (Mailbox)** instead.

---

## Discover & Test in ASI:One
1. In ASI:One or DeltaV, search for your agent by its address (`agent1...`) or name (`aegisgrid_resilience_agent`).
2. Open a chat session and test:
   - `"Analyze outage at S-01"`
   - `"Show affected assets"`
   - `"G-01 is unavailable"`
   - `"Plan recovery"`
   - `"Analyze outage at UNKNOWN-999"`
   - `"Verify RA-05"`
3. Confirm that all responses return with the `[SIMULATION]` prefix and that actions are verified against registered safety rules.

---

## Project Structure

```
aegisgrid-agent/
├── .env.example          # Template for agent port, seed, and mailbox configuration
├── .gitignore            # Git exclusion rules (excludes .env, .venv, private keys, audit history)
├── README.md             # Complete documentation and deployment guide
├── requirements.txt      # Pinned dependencies (uagents==0.26.1, uagents-core==0.4.12, pytest==9.1.1)
├── scenarios.json        # Explicit infrastructure catalog, dependencies, and actions
├── analysis.py           # Deterministic cascade analysis & dependency graph traversal
├── recovery.py           # Dependency-aware recovery planner & safety verification engine
├── agent.py              # Main uAgent entrypoint (supports Local HTTP and Mailbox modes)
├── hosted_agent.py       # Self-contained single-file agent for Agentverse Cloud Web Editor
├── simulation.py         # Local end-to-end multi-turn simulation runner
└── tests/                # Complete Pytest test suite (29 tests)
    ├── __init__.py
    ├── test_analysis.py  # Outage cascade and asset validation tests
    ├── test_recovery.py  # Action verification, plan recalculation, and persistence tests
    └── test_agent_chat.py# Natural-language ACP chat handling, fuzzing, and protocol tests
```
# AEGISGRID
