# AegisGrid — Agentic Infrastructure Resilience System

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

> **Fetch-A-Thon 3.0 — ASI:One Agent Challenge**  
> Autonomous, deterministic, dependency-aware infrastructure resilience intelligence and cascading recovery planning built on Fetch.ai's `uagents` framework and the Agent Chat Protocol (ACP).

---

## ⚠️ Simulation Disclaimer
**All infrastructure assets, failure cascades, telemetry signals, and recovery actions modeled by AegisGrid are strictly simulated.** AegisGrid operates against a fictional municipal infrastructure topology to evaluate deterministic agentic resilience algorithms. The system never connects to, monitors, controls, or alters real-world physical infrastructure, supervisory control and data acquisition (SCADA) systems, or industrial hardware.

---

## Table of Contents
- [Project Overview](#project-overview)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Fictional Infrastructure Topology](#fictional-infrastructure-topology)
- [Recovery Action Catalog](#recovery-action-catalog)
- [Example Scenarios & Chat Commands](#example-scenarios--chat-commands)
- [Technology Stack](#technology-stack)
- [Local Setup & Installation](#local-setup--installation)
  - [Prerequisites](#prerequisites)
  - [Frontend Setup (React + Vite)](#frontend-setup-react--vite)
  - [Backend Agent Setup (Python uAgent)](#backend-agent-setup-python-uagent)
  - [Environment Configuration & Security Warnings](#environment-configuration--security-warnings)
- [Testing & Validation](#testing--validation)
- [Agentverse & ASI:One Integration](#agentverse--asione-integration)
  - [Mode A: Local Development (Default)](#mode-a-local-development-default)
  - [Mode B: Agentverse Outbound Mailbox](#mode-b-agentverse-outbound-mailbox)
  - [Route 1: Hosted Agent on Agentverse Cloud](#route-1-hosted-agent-on-agentverse-cloud)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

---

## Project Overview

**AegisGrid** is an agentic resilience system designed to maintain stability across interdependent critical infrastructure during complex multi-sector outage cascades. Combining a deterministic **Fetch.ai autonomous agent** (`uagents`) with a high-fidelity **React + TypeScript + Vite digital twin control center**, AegisGrid enables operators to simulate disruptions, trace downstream impact chains, evaluate dependency-aware restoration workflows, and reject unsafe recovery sequences before action can be taken.

The agent communicates natively via the **Agent Chat Protocol (ACP)** (`AgentChatProtocol:0.3.0`), making it directly discoverable and interactive through [ASI:One](https://asi1.ai/) and DeltaV chat interfaces.

---

## The Problem

Critical municipal infrastructure sectors—electrical power distribution, municipal water pumping, traffic signaling, and healthcare facilities—are deeply interdependent:
- **Cascading Failures:** A fault in an electrical distribution feeder does not stay isolated to the power grid; it starves water pumping stations of pressure, incapacitates arterial traffic controllers, and forces regional hospitals onto backup power and emergency cooling.
- **LLM Non-Determinism in Mission-Critical Systems:** Generative AI models often hallucinate asset dependencies, generate non-deterministic recovery paths, or suggest dangerous recovery steps (such as energizing a locked-out breaker without verification).
- **Rogue & Unknown Telemetry:** Unregistered devices or spoofed telemetry reporting into central dashboards can corrupt network models if not strictly quarantined at ingress.
- **Dynamic Resource Constraints:** When secondary reserves (such as on-site backup generators) fail or are unavailable, static standard operating procedures (SOPs) break down, failing to recalculate alternative contingency dispatches.

---

## The Solution

AegisGrid solves these challenges through a deterministic, policy-enforced agent architecture:
1. **Deterministic Graph Traversal:** Traverses explicit, cataloged dependency relationships (`scenarios.json`) without relying on probabilistic model inference or external vector lookups.
2. **Safety Verification Engine:** Every proposed recovery step is checked against certified safety interlocks, prerequisite states, target asset validity, and resource availability. Disallowed operations (such as `RA-05` breaker bypass) are rejected with explicit policy rationale.
3. **Ingress Quarantine Gateway:** Unregistered asset identifiers (e.g., `UNKNOWN-999`) are quarantined at the telemetry gateway, isolating the digital twin model from unvalidated inputs.
4. **Dynamic Contingency Planning:** If a primary contingency asset (such as Generator `G-01`) is marked offline, the planner recalculates the recovery order and dispatches secondary alternatives (such as mobile generator fleet `RA-07`).
5. **Immutable Evidence & Audit Ledger:** Maintains an append-only JSON ledger (`incident_history.json`) recording every incident, state change, and verification decision with UTC timestamps and unique evidence IDs.
6. **Dual Interaction Planes:** Provides both a conversational interface via the official Agent Chat Protocol (ACP) for ASI:One and an interactive web dashboard for human operators.

---

## Key Features

- **Cascade Impact Analysis (`analysis.py`):** Deterministically maps failure propagation paths from root asset failures down through municipal water, transit, and healthcare consumers.
- **Dependency-Aware Recovery Planner (`recovery.py`):** Prioritizes life-safety and grid stability using strict ranking rules, prerequisite checks, and resource constraints.
- **Action Verifier (`recovery.py`):** Enforces negative constraints, rejecting hazardous actions (such as breaker lockout bypass without authorization).
- **Unknown Asset Handling:** Detects anomalous telemetry identifiers and triggers quarantine workflows to protect operational integrity.
- **Incident Deduplication:** Merges repeat telemetry or duplicate user reports into existing active incident chains without creating conflicting tasks.
- **Fetch.ai uAgent & ACP Support (`agent.py`):** Implements `uagents_core.contrib.protocols.chat` with `ChatAcknowledgement`, `TextContent`, `StartSessionContent`, and `EndSessionContent`.
- **Pre-Flight Network Diagnostics:** Validates local network connectivity to Fetch.ai Almanac and Agentverse endpoints before startup to isolate connectivity issues from application logic.
- **Self-Contained Cloud Deployment (`hosted_agent.py`):** Single-file agent variant with embedded scenarios and in-memory state designed for immediate execution in the Agentverse Cloud Web Editor.
- **Interactive Control Center Frontend (`src/`):** React 19 dashboard featuring interactive asset topology, live incident feeds, recovery action trackers, and a simulation lab.

---

## System Architecture

```
                       +---------------------------------------+
                       |             ASI:One Chat              |
                       |       (Agent Chat Protocol ACP)       |
                       +---------------------------------------+
                                          |
                                          | ACP Messages (TextContent / Sessions)
                                          v
+---------------------------------------------------------------------------------+
|                         AegisGrid Backend Agent (Python)                        |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                 Agent Core (`agent.py` / `hosted_agent.py`)             |   |
|   |         ACP Handler | Acknowledgement Emitter | Message Parser          |   |
|   +-------------------------------------------------------------------------+   |
|             |                                   |                               |
|             v                                   v                               |
|   +-------------------+               +-------------------------------------+   |
|   |  Cascade Engine   |               | Recovery Planner & Verifier         |   |
|   |   (analysis.py)   |               |            (recovery.py)            |   |
|   |                   |               |                                     |   |
|   | - Dependency Walk |               | - Priority Sorter                   |   |
|   | - Root Isolation  |               | - Prerequisite Validation           |   |
|   | - Quarantine Gate |               | - Disallowed Action Interlock       |   |
|   +-------------------+               +-------------------------------------+   |
|             \                                   /                               |
|              \                                 /                                |
|               v                               v                                 |
|   +-------------------------------------------------------------------------+   |
|   |                         Deterministic Data Store                        |   |
|   |   - Topology Catalog: scenarios.json                                    |   |
|   |   - Audit Ledger: incident_history.json (Append-only state & evidence)  |   |
|   +-------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------+
                                          ^
                                          | Fictional Topology & Incident Data
                                          v
+---------------------------------------------------------------------------------+
|                       AegisGrid Operator Web Dashboard                          |
|                             (React 19 + TypeScript + Vite)                      |
|                                                                                 |
|   - Digital Twin Topology Graph (@xyflow/react)                                 |
|   - Real-time Incident Tracker & Severity Meters                                |
|   - Action Verification & Recovery Execution Panel                              |
|   - Evidence Ledger Viewer & Scenario Simulation Lab                            |
+---------------------------------------------------------------------------------+
```

---

## Fictional Infrastructure Topology

The resilience model defines a deterministic five-node municipal infrastructure graph:

| Asset ID | Asset Name | Sector | Type | Criticality | Dependencies | Downstream Dependents | Default Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S-01** | Electrical Substation | Sector 1 - North District | Electrical | Critical | None | `W-02`, `T-04`, `H-01` | Primary high-voltage feeder bus |
| **W-02** | Water Pump Station | Sector 2 - Central Reservoir | Water | High | `S-01` | `H-01` | Municipal water and hospital chiller loop |
| **T-04** | Traffic Signals & Corridor | Sector 4 - Metro Arterial | Traffic | Moderate | `S-01` | `H-01` | Emergency response vehicle arterial route |
| **H-01** | Hospital Critical Care | Sector 3 - Medical Center | Healthcare | Critical | `S-01`, `G-01`, `W-02` | None | Regional trauma hospital & emergency care |
| **G-01** | Backup Generator Station | Sector 1 - Reserve Facility | Backup | High | None | `H-01` | Dedicated secondary power reserve |

---

## Recovery Action Catalog

All recovery actions are indexed in `scenarios.json` and verified prior to execution:

| Action ID | Target Asset | Priority | Required Resource | Required Prerequisites | Disallowed? | Description / Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RA-01** | `S-01` | 1 | `feeder_reserve_bus` | `breaker_latch_confirmed`, `grid_controller_clearance` | No | Isolate upstream feeder and reroute demand to reserve bus. |
| **RA-02** | `W-02` | 2 | `hydraulic_accumulator` | `operator_clearance`, `pressure_threshold_validated` | No | Shift pump staging to emergency reserve pressure setpoint. |
| **RA-03** | `T-04` | 3 | `arterial_signal_network` | `signal_controller_sync` | No | Reduce cycle times and maintain emergency corridor green wave. |
| **RA-04** | `G-01` | 4 | `G-01` | `gas_lube_checked`, `starter_electrical_verified` | No | Validate backup generator startup sequence and transfer switch. |
| **RA-05** | `S-01` | 1 | `none` | None | **YES (Disallowed)** | Bypass lockout and restore full load without breaker audit. **Always rejected by safety verifier.** |
| **RA-06** | `UNKNOWN-999` | 1 | `ingress_firewall` | `security_controller_auth` | No | Quarantine payload and audit telemetry ingress gateway. |
| **RA-07** | `H-01` | 1 | `mobile_generator_fleet` | `emergency_fleet_clearance` | No | Dispatch mobile emergency power unit to hospital when `G-01` is unavailable. |

---

## Example Scenarios & Chat Commands

When communicating with AegisGrid over ACP or during simulation, the agent supports natural-language commands:

| Natural Language Command | Agent Action & Output |
| :--- | :--- |
| `"Analyze outage at S-01"` | Initiates incident `INC-S01-CASCADE`; models cascade to `W-02`, `T-04`, and `H-01`; generates prioritized recovery plan; logs audit entry. |
| `"Show affected assets"` | Lists all currently degraded or compromised assets, upstream feeds, and operational statuses. |
| `"Plan recovery"` | Returns ranked, verified recovery actions (`RA-01`, `RA-04`, `RA-02`, `RA-03`) with safety audits and prerequisite statuses. |
| `"G-01 is unavailable"` | Marks backup generator offline; detects single-point hospital failure risk; dynamically substitutes `RA-04` with mobile fleet dispatch `RA-07`. |
| `"Analyze outage at UNKNOWN-999"` | Flags unrecognized asset; triggers `RA-06` ingress firewall quarantine; preserves digital twin integrity. |
| `"Verify RA-05"` | Submits unsafe bypass action to verification engine; returns explicit policy rejection (`REJECTED: Action RA-05 proposes an unsafe sequence`). |
| `"Duplicate incident report for S-01"` | Recognizes existing active incident chain; links report to original incident without creating duplicate recovery queues. |
| `"Status"` or `"Help"` | Displays current model state, unavailable resources, registered assets, and active incident queue. |

---

## Technology Stack

### Backend Agent
- **Language:** Python 3.10+ (tested on Python 3.13)
- **Agent Framework:** Fetch.ai `uagents` (v0.26.1) & `uagents-core` (v0.4.12)
- **Messaging Protocol:** Agent Chat Protocol (`AgentChatProtocol:0.3.0` via `uagents_core.contrib.protocols.chat`)
- **Asynchronous Runtime:** `anyio` (v4.15+)
- **Testing:** `pytest` (v9.1.1)

### Frontend Dashboard
- **Framework:** React 19 (`react`, `react-dom`)
- **Build Tool:** Vite 8 (`vite`, `@vitejs/plugin-react`)
- **Language:** TypeScript (~6.0)
- **Styling:** Tailwind CSS v4 (`tailwindcss`, `@tailwindcss/vite`)
- **Graph & Topology Visualization:** `@xyflow/react` (React Flow)
- **Icons & Visuals:** `lucide-react`
- **Charts:** `recharts`
- **Animation:** `framer-motion`
- **Linter:** `oxlint`

---

## Local Setup & Installation

### Prerequisites
- **Node.js:** v18.0.0 or later (v20+ recommended)
- **npm:** v9.0.0 or later
- **Python:** v3.10, v3.11, v3.12, or v3.13

---

### Frontend Setup (React + Vite)

From the repository root:

```bash
# 1. Install frontend dependencies
npm install

# 2. Run the Vite development server
npm run dev

# 3. Build for production preview
npm run build

# 4. Run Oxlint code analysis
npm run lint
```

The frontend dashboard will be available at `http://localhost:5173/`.

---

### Backend Agent Setup (Python uAgent)

From the repository root:

```bash
# 1. Navigate to the agent directory
cd aegisgrid-agent

# 2. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install pinned Python dependencies
pip install -r requirements.txt
```

---

### Environment Configuration & Security Warnings

The backend agent configuration is managed via `.env`. A complete template is provided at [`aegisgrid-agent/.env.example`](file:///Users/princemahto/AEGISGRID/aegisgrid-agent/.env.example).

To configure your environment:
```bash
cd aegisgrid-agent
cp .env.example .env
```

Review the settings in `.env`:
- `AGENT_NAME`: Name registered with protocols (default: `aegisgrid_resilience_agent`).
- `AGENT_SEED`: Secret seed phrase used to derive the agent's keypair. Replace this with your own private seed phrase.
- `AGENT_NETWORK`: `mainnet` (default) or `testnet`.
- `AGENT_MAILBOX`: Set `false` for local development (Mode A) or `true` for Agentverse Mailbox (Mode B).
- `AGENT_PORT`: Local server port (default: `8000`).

> [!CAUTION]
> **CRITICAL SECURITY WARNING: NEVER COMMIT SENSITIVE DATA**
> - **Never commit `.env` files** containing real seeds, credentials, or API keys.
> - **Never commit private seeds or keys**, including `private_keys.json`.
> - **Never commit runtime state files**, such as `.venv/`, `.pytest_cache/`, or runtime audit logs like `incident_history.json`.
> - Always verify your `.gitignore` rules before pushing to any remote repository.

---

## Testing & Validation

### Backend Automated Test Suite
AegisGrid includes a comprehensive test suite covering deterministic cascade analysis, action verification, unknown asset quarantine, incident persistence, and ACP protocol compliance.

To run the tests, execute from the `aegisgrid-agent` directory with the virtual environment activated:

```bash
cd aegisgrid-agent
source .venv/bin/activate
pytest tests/ -v
```

*(Alternatively, run directly via `.venv/bin/pytest tests/ -v` from `aegisgrid-agent`).*

> [!NOTE]
> **Test Suite Status:** The existing test suite contains **29 unit and integration tests** across `test_analysis.py`, `test_recovery.py`, and `test_agent_chat.py`. Running `pytest tests/ -v` in the configured virtual environment confirms that all **29 tests pass successfully** (`29 passed, 1 warning in ~10.7s`).

The test suite validates:
1. `S-01` primary feeder outage and downstream impact traversal (`W-02`, `T-04`, `H-01`).
2. Single-point failure detection when `G-01` is unavailable.
3. Double-contingency cascading (`S-01` + `G-01`).
4. Unknown asset validation and rejection (`UNKNOWN-999`).
5. Action catalog lookups and priority ordering.
6. Dynamic contingency plan recalculation (switching to `RA-07`).
7. Unsafe action rejection (`RA-05` lockout bypass).
8. Missing prerequisite and unavailable resource enforcement.
9. Append-only persistence and idempotency of `incident_history.json`.
10. Duplicate incident report merging and deduplication.
11. Malformed chat input handling and fuzzing resilience.
12. Official ACP message types (`ChatMessage`, `ChatAcknowledgement`, `TextContent`, session events).
13. uAgent creation in Local HTTP mode and Mailbox mode.
14. Cloud hosted agent self-containment (`hosted_agent.py`).
15. Pre-flight network diagnostics for Fetch.ai endpoints.

---

### Local End-to-End Simulation Runner
To execute a simulated multi-turn natural-language conversation running through all scenarios in sequence:

```bash
cd aegisgrid-agent
source .venv/bin/activate
python simulation.py
```

This script steps through an automated multi-turn dialogue, printing both user queries and agent ACP responses, followed by a summary of the resulting audit trail in `incident_history.json`.

---

## Agentverse & ASI:One Integration

AegisGrid supports multiple execution workflows to accommodate local development and live cloud discovery.

### Mode A: Local Development (Default)
In Mode A, the agent runs as a local HTTP server without requiring cloud credentials or public IP addresses:

1. Ensure `AGENT_MAILBOX=false` in `aegisgrid-agent/.env`.
2. Start the agent:
   ```bash
   cd aegisgrid-agent
   source .venv/bin/activate
   python agent.py
   ```
3. The terminal displays the local HTTP endpoint (`http://127.0.0.1:8000/submit`) and an **Agent Inspector URL**. Local mode skips on-chain Almanac registration to prevent network timeouts during offline development.

---

### Mode B: Agentverse Outbound Mailbox
*Recommended for connecting your local agent to ASI:One without opening ports or configuring reverse proxies.*

1. In `aegisgrid-agent/.env`, set:
   ```env
   AGENT_MAILBOX=true
   ```
2. Start the agent:
   ```bash
   cd aegisgrid-agent
   source .venv/bin/activate
   python agent.py
   ```
3. Locate the Agent Inspector URL printed in your terminal:
   ```text
   Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address=agent1...
   ```
4. Open the link in your browser while logged into [Agentverse](https://agentverse.ai/).
5. Click **Connect to Mailbox**. Agentverse provisions a long-polling queue for your agent address.
6. The agent terminal will confirm:
   ```text
   INFO: Starting mailbox client for https://agentverse.ai
   ```
   The local agent is now listening for incoming ASI:One messages via outbound polling.

> [!WARNING]
> **Do not use Agentverse "External Integration" for localhost.**
> The Agentverse External Integration form requires a publicly reachable HTTPS endpoint with a valid SSL certificate (e.g., hosted on AWS, Render, or Railway). It cannot reach `127.0.0.1` or `localhost`. Use **Mode B (Mailbox)** for local machine development.

---

### Route 1: Hosted Agent on Agentverse Cloud
*Zero local infrastructure: Runs 24/7 inside the Agentverse cloud container.*

1. Log in to [Agentverse](https://agentverse.ai/).
2. Navigate to **Agents** &rarr; **+ New Agent** &rarr; select **Blank Agent**.
3. Name the agent `aegisgrid_resilience_agent`.
4. Copy the entire contents of [`aegisgrid-agent/hosted_agent.py`](file:///Users/princemahto/AEGISGRID/aegisgrid-agent/hosted_agent.py) and paste it into the Agentverse Web Code Editor. (This file is 100% self-contained with embedded scenarios and in-memory ledger).
5. *(Optional)* Add `AGENT_SEED` under the agent's **Secrets** tab.
6. Click **Start** to run the agent.
7. Confirm the agent status shows **Running** and that `AgentChatProtocol` is listed under the Protocols tab.
8. Go to [ASI:One](https://asi1.ai/), search for your agent name or address, and start chatting (e.g., `"Analyze outage at S-01"`).

---

## Project Structure

```
AEGISGRID/
├── README.md                      # Primary project documentation & architecture guide
├── package.json                   # Frontend dependencies, scripts, and build configuration
├── package-lock.json              # Pinned npm dependency lockfile
├── vite.config.ts                 # Vite bundler configuration
├── tsconfig.json                  # Root TypeScript configuration
├── tsconfig.app.json              # Application TypeScript configuration
├── tsconfig.node.json             # Vite/Node TypeScript configuration
├── .oxlintrc.json                 # Oxlint static analysis rules
├── index.html                     # Frontend single-page application entry point
├── public/                        # Static assets (favicons, SVG icons)
├── src/                           # Frontend React application source code
│   ├── App.tsx                    # Main dashboard: Digital Twin, Incidents, Simulation Lab
│   ├── App.css                    # Dashboard custom styles and transitions
│   ├── index.css                  # Global styles and Tailwind CSS imports
│   ├── main.tsx                   # React DOM application mount
│   └── assets/                    # Image assets
└── aegisgrid-agent/               # Autonomous Python uAgent backend
    ├── README.md                  # Agent-specific documentation and command reference
    ├── requirements.txt           # Pinned Python dependencies (uagents, pytest, etc.)
    ├── .env.example               # Configuration template for seeds, ports, and mailbox
    ├── .gitignore                 # Backend gitignore rules (protects .env, .venv, history)
    ├── scenarios.json             # Certified infrastructure catalog, dependencies, & actions
    ├── analysis.py                # Deterministic cascade analysis engine & graph traversal
    ├── recovery.py                # Dependency-aware recovery planner & action verifier
    ├── agent.py                   # Main uAgent entry point (Local HTTP & Mailbox modes)
    ├── hosted_agent.py            # Self-contained single-file agent for Agentverse Cloud
    ├── simulation.py              # Local multi-turn scenario conversation runner
    └── tests/                     # Pytest automated test suite (29 tests)
        ├── __init__.py
        ├── test_analysis.py       # Outage cascade and asset validation tests
        ├── test_recovery.py       # Action verification, plan recalculation, & persistence
        └── test_agent_chat.py     # ACP chat protocol handling, fuzzing, & agent lifecycle
```

---

## Limitations

- **Simulated Topology Scope:** The current implementation models a curated five-node municipal infrastructure graph (`S-01`, `W-02`, `T-04`, `H-01`, `G-01`). It is designed as a resilience intelligence proof-of-concept rather than an exhaustive multi-thousand node utility topology.
- **Synchronous Telemetry Modeling:** Telemetry inputs are processed on-demand through chat commands, automated tests, or the simulation runner rather than real-time live telemetry streaming from physical sensors.
- **File-Based Audit Ledger:** State persistence in local mode utilizes an append-only JSON ledger (`incident_history.json`). Production multi-region deployments would require a distributed database or decentralized ledger.
- **No Direct Physical Actuation:** By design and safety policy, AegisGrid outputs verified recommendation plans and rationale; it does not issue direct actuator control signals to physical machinery.

---

## Future Improvements

- **Multi-Agent Sector Swarm:** Decomposing the system into specialized peer agents for each municipal utility (e.g., an Electrical Sector Agent, Water Authority Agent, and Hospital Facility Agent) negotiating resource allocation through agent-to-agent ACP protocols.
- **Decentralized Ledger Anchoring:** Anchoring incident evidence hashes and action verification decisions onto the Fetch.ai blockchain for tamper-evident regulatory audits.
- **Real-Time WebSocket Gateway:** Implementing a bi-directional WebSocket interface between the Python uAgent runtime and the React digital twin interface for live event streaming.
- **Dynamic Topology Ingestion:** Supporting standard power systems CIM (Common Information Model) or GIS data imports to generate dependency graphs dynamically for larger municipal networks.
