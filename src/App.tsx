import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Bell,
  ChevronRight,
  Database,
  Download,
  Gauge,
  Menu,
  Network,
  Play,
  Repeat,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Sun,
  TrendingUp,
  Moon,
} from 'lucide-react'
import './App.css'

type PageKey =
  | 'overview'
  | 'incidents'
  | 'digital-twin'
  | 'agent-network'
  | 'recovery-plans'
  | 'evidence-ledger'
  | 'simulation-lab'
  | 'settings'

type AssetStatus = 'critical' | 'warning' | 'normal' | 'unavailable'
type AgentState = 'Ready' | 'Processing' | 'Needs Review'
type Severity = 'Critical' | 'High' | 'Medium' | 'Low'
type RecoveryStatus = 'Pending' | 'In Progress' | 'Verified' | 'Rejected'
type VerificationState = 'Verified' | 'Pending' | 'Failed'
type ScenarioId =
  | 'substation-failure'
  | 'backup-generator'
  | 'unknown-asset'
  | 'duplicate-incident'
  | 'invalid-action'
type Theme = 'dark' | 'light'

interface Asset {
  id: string
  name: string
  type: 'Electrical' | 'Water' | 'Traffic' | 'Healthcare' | 'Backup'
  status: AssetStatus
  criticality: 'Critical' | 'High' | 'Moderate'
  dependencies: string[]
  lastEvent: string
  x: number
  y: number
}

interface Incident {
  id: string
  title: string
  severity: Severity
  affectedAssets: string[]
  status: string
  lastUpdate: string
  description: string
}

interface Agent {
  id: string
  name: string
  role: string
  state: AgentState
  lastTask: string
  tasks: number
}

interface RecoveryAction {
  id: string
  priority: number
  action: string
  targetAsset: string
  rationale: string
  prerequisites: string
  status: RecoveryStatus
  verification: VerificationState
}

interface EvidenceItem {
  id: string
  timestamp: string
  source: string
  type: string
  message: string
  detail: string
  incidentId?: string
  actionId?: string
}

interface NotificationItem {
  id: string
  title: string
  detail: string
  time: string
  kind: 'info' | 'warning' | 'success'
}

interface DemoState {
  assets: Asset[]
  incidents: Incident[]
  agents: Agent[]
  recoveryActions: RecoveryAction[]
  evidence: EvidenceItem[]
  notifications: NotificationItem[]
  activeScenario: ScenarioId
}

const LS_KEY = 'aegisgrid-demo-state-v1'
const THEME_KEY = 'aegisgrid-theme'
const navItems: Array<{ id: PageKey; label: string; icon: any }> = [
  { id: 'overview', label: 'Overview', icon: Gauge },
  { id: 'incidents', label: 'Live Incidents', icon: AlertTriangle },
  { id: 'digital-twin', label: 'Digital Twin', icon: Network },
  { id: 'agent-network', label: 'Agent Network', icon: Sparkles },
  { id: 'recovery-plans', label: 'Recovery Plans', icon: ShieldCheck },
  { id: 'evidence-ledger', label: 'Evidence Ledger', icon: Database },
  { id: 'simulation-lab', label: 'Simulation Lab', icon: Play },
  { id: 'settings', label: 'Settings', icon: Settings },
]

const baseAssets: Asset[] = [
  {
    id: 'S-01',
    name: 'Electrical Substation',
    type: 'Electrical',
    status: 'normal',
    criticality: 'Moderate',
    dependencies: ['G-01', 'H-01'],
    lastEvent: '12:00 UTC',
    x: 200,
    y: 150,
  },
  {
    id: 'W-02',
    name: 'Water Pump',
    type: 'Water',
    status: 'normal',
    criticality: 'Moderate',
    dependencies: ['S-01'],
    lastEvent: '12:00 UTC',
    x: 430,
    y: 210,
  },
  {
    id: 'T-04',
    name: 'Traffic Signals',
    type: 'Traffic',
    status: 'normal',
    criticality: 'Moderate',
    dependencies: ['S-01'],
    lastEvent: '12:00 UTC',
    x: 520,
    y: 96,
  },
  {
    id: 'H-01',
    name: 'Hospital Backup Supply',
    type: 'Healthcare',
    status: 'normal',
    criticality: 'Moderate',
    dependencies: ['S-01', 'G-01'],
    lastEvent: '12:00 UTC',
    x: 620,
    y: 250,
  },
  {
    id: 'G-01',
    name: 'Backup Generator',
    type: 'Backup',
    status: 'normal',
    criticality: 'Moderate',
    dependencies: ['S-01'],
    lastEvent: '12:00 UTC',
    x: 92,
    y: 290,
  },
]

const baseEvidence: EvidenceItem[] = [
  {
    id: 'EV-010',
    timestamp: '12:01 UTC',
    source: 'SCADA',
    type: 'Incident received',
    message: 'Feeder anomaly reported at substation S-01.',
    detail: 'Voltage sag and breaker trip sequence recorded before downstream impacts were visible.',
    incidentId: 'INC-2041',
  },
  {
    id: 'EV-011',
    timestamp: '12:03 UTC',
    source: 'Dependency map',
    type: 'Asset dependencies traversed',
    message: 'Downstream impact path identified to W-02 and T-04.',
    detail: 'Critical path traced through S-01 to the water and traffic infrastructure nodes.',
    incidentId: 'INC-2041',
  },
  {
    id: 'EV-012',
    timestamp: '12:04 UTC',
    source: 'Power Specialist',
    type: 'Assessment generated',
    message: 'Substation load is 3.2x above stable operating band.',
    detail: 'Risk to backup power continuity remains elevated but generator reserve remains available.',
    incidentId: 'INC-2041',
  },
  {
    id: 'EV-013',
    timestamp: '12:05 UTC',
    source: 'Recovery Planner',
    type: 'Recovery plan assembled',
    message: 'Action queue ranked to isolate feeder and hold pump pressure.',
    detail: 'Recovery plan prioritized by impact to patient-care and emergency mobility services.',
    actionId: 'RA-01',
  },
  {
    id: 'EV-014',
    timestamp: '12:08 UTC',
    source: 'Verification Agent',
    type: 'Verification performed',
    message: 'Prerequisites validated for generator startup sequence.',
    detail: 'Maintained service continuity and reduced chance of backup power failure during the recovery window.',
    actionId: 'RA-04',
  },
  {
    id: 'EV-015',
    timestamp: '12:09 UTC',
    source: 'Command Agent',
    type: 'Plan updated',
    message: 'Recovery plan adjusted after pressure loss review.',
    detail: 'Action sequencing updated to keep hospital backup supply online while mitigating traffic flow issues.',
    incidentId: 'INC-2041',
  },
]

function createScenarioState(scenarioId: ScenarioId): DemoState {
  switch (scenarioId) {
    case 'substation-failure':
      return {
        activeScenario: 'substation-failure',
        assets: [
          { ...baseAssets[0], status: 'critical', criticality: 'Critical', lastEvent: '12:12 UTC' },
          { ...baseAssets[1], status: 'warning', criticality: 'High', lastEvent: '12:08 UTC' },
          { ...baseAssets[2], status: 'warning', criticality: 'High', lastEvent: '12:09 UTC' },
          { ...baseAssets[3], status: 'normal', criticality: 'Moderate', lastEvent: '12:06 UTC' },
          { ...baseAssets[4], status: 'normal', criticality: 'Moderate', lastEvent: '12:05 UTC' },
        ],
        incidents: [
          {
            id: 'INC-2041',
            title: 'Substation S-01 fault cascade',
            severity: 'Critical',
            affectedAssets: ['S-01', 'W-02', 'T-04', 'H-01'],
            status: 'Monitoring',
            lastUpdate: '12:12 UTC',
            description: 'Electrical disturbance propagated through the substation feeder and elevated downstream service risk.',
          },
          {
            id: 'INC-2042',
            title: 'Pressure loss at water pump cluster',
            severity: 'High',
            affectedAssets: ['W-02'],
            status: 'Mitigating',
            lastUpdate: '12:05 UTC',
            description: 'Water pressure dropped below resilience threshold after upstream load-shedding changes.',
          },
          {
            id: 'INC-2043',
            title: 'Signal timing degraded near corridor',
            severity: 'Medium',
            affectedAssets: ['T-04'],
            status: 'Assessing',
            lastUpdate: '11:58 UTC',
            description: 'Traffic signal timing drifted after degraded transmission stability from the primary station.',
          },
        ],
        agents: [
          { id: 'cmd', name: 'Command Agent', role: 'Scenario orchestration', state: 'Processing', lastTask: 'Coordinating substation cascade response', tasks: 5 },
          { id: 'power', name: 'Power Specialist', role: 'Grid health', state: 'Ready', lastTask: 'Breaker status review', tasks: 3 },
          { id: 'water', name: 'Water Specialist', role: 'Pressure resilience', state: 'Processing', lastTask: 'Pump load balancing', tasks: 4 },
          { id: 'traffic', name: 'Traffic Specialist', role: 'Intersection timing', state: 'Needs Review', lastTask: 'Signal adaptation check', tasks: 3 },
          { id: 'recovery', name: 'Recovery Planner', role: 'Plan sequencing', state: 'Ready', lastTask: 'Ranking recovery actions', tasks: 6 },
          { id: 'verify', name: 'Verification Agent', role: 'Evidence validation', state: 'Processing', lastTask: 'Verifying plan prerequisites', tasks: 4 },
        ],
        recoveryActions: [
          {
            id: 'RA-01',
            priority: 1,
            action: 'Isolate the upstream feeder and reroute demand to reserve bus',
            targetAsset: 'S-01',
            rationale: 'Reduces cascading fault propagation while preserving hospital backup service.',
            prerequisites: 'Breaker status verification and latch confirmation',
            status: 'In Progress',
            verification: 'Pending',
          },
          {
            id: 'RA-02',
            priority: 2,
            action: 'Shift pump staging to emergency reserve pressure setpoint',
            targetAsset: 'W-02',
            rationale: 'Maintains critical water pressure during substation outage recovery.',
            prerequisites: 'Operator clearance and pressure threshold checks',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-03',
            priority: 3,
            action: 'Reduce traffic cycle times at junction T-04',
            targetAsset: 'T-04',
            rationale: 'Improves emergency corridor throughput while load remains unstable.',
            prerequisites: 'Signal controller validation',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-04',
            priority: 4,
            action: 'Validate backup generator startup sequence',
            targetAsset: 'G-01',
            rationale: 'Provides resilient power to critical healthcare loads if the utility feeder remains unstable.',
            prerequisites: 'Gas and lube checks',
            status: 'Verified',
            verification: 'Verified',
          },
        ],
        evidence: [
          {
            id: 'EV-016',
            timestamp: '12:12 UTC',
            source: 'Command Agent',
            type: 'Scenario executed',
            message: 'Substation failure scenario applied to the shared demo state.',
            detail: 'System state refreshed with cascading infrastructure impacts and recovery sequencing.',
            incidentId: 'INC-2041',
            actionId: 'RA-01',
          },
          ...baseEvidence,
        ],
        notifications: [
          { id: 'n-s-1', title: 'Fault cascade confirmed', detail: 'S-01 surge propagated to W-02 and T-04', time: '12:12 UTC', kind: 'warning' },
          { id: 'n-s-2', title: 'Recovery queue updated', detail: 'Action RA-01 is active', time: '12:12 UTC', kind: 'info' },
          { id: 'n1', title: 'Scenario loaded', detail: 'Substation fault cascade is active', time: '12:09 UTC', kind: 'warning' },
        ],
      }

    case 'backup-generator':
      return {
        activeScenario: 'backup-generator',
        assets: [
          { ...baseAssets[0], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[1], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[2], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[3], status: 'warning', criticality: 'High', lastEvent: '12:15 UTC' },
          { ...baseAssets[4], status: 'unavailable', criticality: 'High', lastEvent: '12:15 UTC' },
        ],
        incidents: [
          {
            id: 'INC-2042',
            title: 'Backup generator outage risk',
            severity: 'High',
            affectedAssets: ['G-01', 'H-01'],
            status: 'Mitigating',
            lastUpdate: '12:15 UTC',
            description: 'Reserve supply G-01 is offline and healthcare continuity requires manual checks and alternate feeder lock.',
          },
          {
            id: 'INC-2041',
            title: 'Substation S-01 nominal grid operations',
            severity: 'Low',
            affectedAssets: ['S-01'],
            status: 'Normal',
            lastUpdate: '12:10 UTC',
            description: 'Substation power delivery is stable; reserve redundancy is under review.',
          },
          {
            id: 'INC-2043',
            title: 'Signal corridor nominal',
            severity: 'Low',
            affectedAssets: ['T-04'],
            status: 'Resolved',
            lastUpdate: '12:00 UTC',
            description: 'Traffic signal timing operating within standard baseline tolerances.',
          },
        ],
        agents: [
          { id: 'cmd', name: 'Command Agent', role: 'Scenario orchestration', state: 'Processing', lastTask: 'Assessing backup generator contingency', tasks: 6 },
          { id: 'power', name: 'Power Specialist', role: 'Grid health', state: 'Processing', lastTask: 'Investigating G-01 alternator lockout', tasks: 5 },
          { id: 'water', name: 'Water Specialist', role: 'Pressure resilience', state: 'Ready', lastTask: 'Normal pressure monitoring', tasks: 3 },
          { id: 'traffic', name: 'Traffic Specialist', role: 'Intersection timing', state: 'Ready', lastTask: 'Corridor priority route clear', tasks: 3 },
          { id: 'recovery', name: 'Recovery Planner', role: 'Plan sequencing', state: 'Processing', lastTask: 'Prioritizing mobile generation deployment', tasks: 7 },
          { id: 'verify', name: 'Verification Agent', role: 'Evidence validation', state: 'Needs Review', lastTask: 'G-01 startup sequence failed verification', tasks: 5 },
        ],
        recoveryActions: [
          {
            id: 'RA-04',
            priority: 1,
            action: 'Validate backup generator startup sequence',
            targetAsset: 'G-01',
            rationale: 'G-01 reserve capacity failed startup verification; dispatch mobile emergency power unit to hospital.',
            prerequisites: 'Gas, lube, and starter electrical verification',
            status: 'Pending',
            verification: 'Failed',
          },
          {
            id: 'RA-01',
            priority: 2,
            action: 'Lock primary feeder to prevent scheduled maintenance switching',
            targetAsset: 'S-01',
            rationale: 'Prevents grid interruption while G-01 backup generator is unavailable.',
            prerequisites: 'Grid controller clearance',
            status: 'Verified',
            verification: 'Verified',
          },
          {
            id: 'RA-02',
            priority: 3,
            action: 'Shift pump staging to emergency reserve pressure setpoint',
            targetAsset: 'W-02',
            rationale: 'Maintains critical water pressure during substation outage recovery.',
            prerequisites: 'Operator clearance and pressure threshold checks',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-03',
            priority: 4,
            action: 'Maintain emergency vehicle corridor signal priority',
            targetAsset: 'T-04',
            rationale: 'Guarantees unhindered route for mobile emergency power transport.',
            prerequisites: 'Signal controller sync',
            status: 'Pending',
            verification: 'Pending',
          },
        ],
        evidence: [
          {
            id: 'EV-017',
            timestamp: '12:15 UTC',
            source: 'Generator monitor',
            type: 'Generator unavailable',
            message: 'G-01 reserve output dropped below safe threshold.',
            detail: 'Healthcare continuity is protected through emergency feeder lock and manual dispatch checks.',
            incidentId: 'INC-2042',
            actionId: 'RA-04',
          },
          ...baseEvidence,
        ],
        notifications: [
          { id: 'n-g-1', title: 'Generator unavailable', detail: 'Reserve supply G-01 is offline; hospital on single feed', time: '12:15 UTC', kind: 'warning' },
          { id: 'n-g-2', title: 'Verification alert', detail: 'RA-04 failed verification; mobile generator requested', time: '12:15 UTC', kind: 'warning' },
        ],
      }

    case 'unknown-asset':
      return {
        activeScenario: 'unknown-asset',
        assets: [
          { ...baseAssets[0], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[1], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[2], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[3], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
          { ...baseAssets[4], status: 'normal', criticality: 'Moderate', lastEvent: '12:10 UTC' },
        ],
        incidents: [
          {
            id: 'INC-9000',
            title: 'Unknown asset incident reported',
            severity: 'Low',
            affectedAssets: ['X-99'],
            status: 'Escalated',
            lastUpdate: '12:18 UTC',
            description: 'A system message referenced unregistered asset X-99. The intake pipeline quarantined the report and prevented unsafe impact propagation.',
          },
          {
            id: 'INC-2041',
            title: 'Substation S-01 nominal grid operations',
            severity: 'Low',
            affectedAssets: ['S-01'],
            status: 'Normal',
            lastUpdate: '12:10 UTC',
            description: 'Substation power delivery is stable; topology registry verified authentic.',
          },
          {
            id: 'INC-2042',
            title: 'Water pump cluster nominal',
            severity: 'Low',
            affectedAssets: ['W-02'],
            status: 'Normal',
            lastUpdate: '12:05 UTC',
            description: 'Pump pressure verified in safe operating band.',
          },
          {
            id: 'INC-2043',
            title: 'Signal corridor nominal',
            severity: 'Low',
            affectedAssets: ['T-04'],
            status: 'Normal',
            lastUpdate: '12:00 UTC',
            description: 'Corridor traffic timing aligned with normal schedule.',
          },
        ],
        agents: [
          { id: 'cmd', name: 'Command Agent', role: 'Scenario orchestration', state: 'Processing', lastTask: 'Quarantining uncataloged asset report', tasks: 6 },
          { id: 'power', name: 'Power Specialist', role: 'Grid health', state: 'Ready', lastTask: 'Grid telemetry verified authentic', tasks: 4 },
          { id: 'water', name: 'Water Specialist', role: 'Pressure resilience', state: 'Ready', lastTask: 'Pump telemetry verified authentic', tasks: 3 },
          { id: 'traffic', name: 'Traffic Specialist', role: 'Intersection timing', state: 'Ready', lastTask: 'Signal telemetry verified authentic', tasks: 3 },
          { id: 'recovery', name: 'Recovery Planner', role: 'Plan sequencing', state: 'Ready', lastTask: 'Quarantine protocol active', tasks: 5 },
          { id: 'verify', name: 'Verification Agent', role: 'Evidence validation', state: 'Processing', lastTask: 'Rejecting unregistered asset X-99', tasks: 6 },
        ],
        recoveryActions: [
          {
            id: 'RA-06',
            priority: 1,
            action: 'Quarantine payload and audit telemetry ingress gateway',
            targetAsset: 'X-99',
            rationale: 'Blocks unrecognized asset ID from injecting synthetic state into digital twin.',
            prerequisites: 'Security controller authorization',
            status: 'Verified',
            verification: 'Verified',
          },
          {
            id: 'RA-01',
            priority: 2,
            action: 'Verify substation telemetry feed integrity',
            targetAsset: 'S-01',
            rationale: 'Confirms SCADA packet signatures match registered asset catalog.',
            prerequisites: 'PKI signature audit',
            status: 'Verified',
            verification: 'Verified',
          },
          {
            id: 'RA-02',
            priority: 3,
            action: 'Shift pump staging to emergency reserve pressure setpoint',
            targetAsset: 'W-02',
            rationale: 'Maintains critical water pressure during substation outage recovery.',
            prerequisites: 'Operator clearance and pressure threshold checks',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-04',
            priority: 4,
            action: 'Validate backup generator startup sequence',
            targetAsset: 'G-01',
            rationale: 'Provides resilient power to critical healthcare loads if the utility feeder remains unstable.',
            prerequisites: 'Gas and lube checks',
            status: 'Verified',
            verification: 'Verified',
          },
        ],
        evidence: [
          {
            id: 'EV-018',
            timestamp: '12:18 UTC',
            source: 'Incident intake',
            type: 'Unknown asset',
            message: 'Asset X-99 was not found in the operational registry.',
            detail: 'The intake pipeline quarantined the report and prevented unsafe impact propagation into the dependency graph.',
            incidentId: 'INC-9000',
            actionId: 'RA-06',
          },
          ...baseEvidence,
        ],
        notifications: [
          { id: 'n-x-1', title: 'Unknown asset blocked', detail: 'X-99 was quarantined by intake gateway', time: '12:18 UTC', kind: 'info' },
          { id: 'n-x-2', title: 'Graph integrity confirmed', detail: 'Operational topology protected against unverified node', time: '12:18 UTC', kind: 'success' },
        ],
      }

    case 'duplicate-incident':
      return {
        activeScenario: 'duplicate-incident',
        assets: [
          { ...baseAssets[0], status: 'critical', criticality: 'Critical', lastEvent: '12:20 UTC' },
          { ...baseAssets[1], status: 'warning', criticality: 'High', lastEvent: '12:08 UTC' },
          { ...baseAssets[2], status: 'warning', criticality: 'High', lastEvent: '12:09 UTC' },
          { ...baseAssets[3], status: 'normal', criticality: 'Moderate', lastEvent: '12:06 UTC' },
          { ...baseAssets[4], status: 'normal', criticality: 'Moderate', lastEvent: '12:05 UTC' },
        ],
        incidents: [
          {
            id: 'INC-2041-DUP',
            title: 'Duplicate report for S-01 fault cascade',
            severity: 'Medium',
            affectedAssets: ['S-01'],
            status: 'Merged',
            lastUpdate: '12:20 UTC',
            description: 'Secondary report merged into the active incident narrative to avoid duplicate action attempts.',
          },
          {
            id: 'INC-2041',
            title: 'Substation S-01 fault cascade',
            severity: 'Critical',
            affectedAssets: ['S-01', 'W-02', 'T-04', 'H-01'],
            status: 'Monitoring',
            lastUpdate: '12:12 UTC',
            description: 'Electrical disturbance propagated through the substation feeder.',
          },
          {
            id: 'INC-2042',
            title: 'Pressure loss at water pump cluster',
            severity: 'High',
            affectedAssets: ['W-02'],
            status: 'Mitigating',
            lastUpdate: '12:05 UTC',
            description: 'Water pressure dropped below resilience threshold.',
          },
          {
            id: 'INC-2043',
            title: 'Signal timing degraded near corridor',
            severity: 'Medium',
            affectedAssets: ['T-04'],
            status: 'Assessing',
            lastUpdate: '11:58 UTC',
            description: 'Traffic signal timing drifted.',
          },
        ],
        agents: [
          { id: 'cmd', name: 'Command Agent', role: 'Scenario orchestration', state: 'Processing', lastTask: 'Deduplicating incoming queue reports', tasks: 6 },
          { id: 'power', name: 'Power Specialist', role: 'Grid health', state: 'Ready', lastTask: 'Breaker status review', tasks: 3 },
          { id: 'water', name: 'Water Specialist', role: 'Pressure resilience', state: 'Processing', lastTask: 'Pump load balancing', tasks: 4 },
          { id: 'traffic', name: 'Traffic Specialist', role: 'Intersection timing', state: 'Needs Review', lastTask: 'Signal adaptation check', tasks: 3 },
          { id: 'recovery', name: 'Recovery Planner', role: 'Plan sequencing', state: 'Ready', lastTask: 'Maintaining single action pipeline', tasks: 6 },
          { id: 'verify', name: 'Verification Agent', role: 'Evidence validation', state: 'Ready', lastTask: 'Verified suppression of duplicate incident', tasks: 5 },
        ],
        recoveryActions: [
          {
            id: 'RA-01',
            priority: 1,
            action: 'Isolate the upstream feeder and reroute demand to reserve bus',
            targetAsset: 'S-01',
            rationale: 'Reduces cascading fault propagation while preserving hospital backup service.',
            prerequisites: 'Breaker status verification and latch confirmation',
            status: 'In Progress',
            verification: 'Pending',
          },
          {
            id: 'RA-02',
            priority: 2,
            action: 'Shift pump staging to emergency reserve pressure setpoint',
            targetAsset: 'W-02',
            rationale: 'Maintains critical water pressure during substation outage recovery.',
            prerequisites: 'Operator clearance and pressure threshold checks',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-03',
            priority: 3,
            action: 'Reduce traffic cycle times at junction T-04',
            targetAsset: 'T-04',
            rationale: 'Improves emergency corridor throughput while load remains unstable.',
            prerequisites: 'Signal controller validation',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-04',
            priority: 4,
            action: 'Validate backup generator startup sequence',
            targetAsset: 'G-01',
            rationale: 'Provides resilient power to critical healthcare loads if the utility feeder remains unstable.',
            prerequisites: 'Gas and lube checks',
            status: 'Verified',
            verification: 'Verified',
          },
        ],
        evidence: [
          {
            id: 'EV-019',
            timestamp: '12:20 UTC',
            source: 'Demultiplexer',
            type: 'Duplicate incident suppressed',
            message: 'Second report merged into active incident chain.',
            detail: 'The queue only keeps one active incident record for the same failing asset cluster.',
            incidentId: 'INC-2041',
          },
          ...baseEvidence,
        ],
        notifications: [
          { id: 'n-d-1', title: 'Duplicate filtered', detail: 'Secondary incident merged into active queue', time: '12:20 UTC', kind: 'success' },
        ],
      }

    case 'invalid-action':
      return {
        activeScenario: 'invalid-action',
        assets: [
          { ...baseAssets[0], status: 'critical', criticality: 'Critical', lastEvent: '12:22 UTC' },
          { ...baseAssets[1], status: 'warning', criticality: 'High', lastEvent: '12:08 UTC' },
          { ...baseAssets[2], status: 'warning', criticality: 'High', lastEvent: '12:09 UTC' },
          { ...baseAssets[3], status: 'normal', criticality: 'Moderate', lastEvent: '12:06 UTC' },
          { ...baseAssets[4], status: 'normal', criticality: 'Moderate', lastEvent: '12:05 UTC' },
        ],
        incidents: [
          {
            id: 'INC-2041',
            title: 'Substation S-01 fault cascade',
            severity: 'Critical',
            affectedAssets: ['S-01', 'W-02', 'T-04', 'H-01'],
            status: 'Monitoring',
            lastUpdate: '12:22 UTC',
            description: 'Electrical disturbance propagated through the substation feeder. Recovery plan submitted for verifier audit.',
          },
          {
            id: 'INC-2042',
            title: 'Pressure loss at water pump cluster',
            severity: 'High',
            affectedAssets: ['W-02'],
            status: 'Mitigating',
            lastUpdate: '12:05 UTC',
            description: 'Water pressure dropped below resilience threshold.',
          },
          {
            id: 'INC-2043',
            title: 'Signal timing degraded near corridor',
            severity: 'Medium',
            affectedAssets: ['T-04'],
            status: 'Assessing',
            lastUpdate: '11:58 UTC',
            description: 'Traffic signal timing drifted.',
          },
        ],
        agents: [
          { id: 'cmd', name: 'Command Agent', role: 'Scenario orchestration', state: 'Processing', lastTask: 'Coordinating recovery plan audit', tasks: 6 },
          { id: 'power', name: 'Power Specialist', role: 'Grid health', state: 'Ready', lastTask: 'Breaker status review', tasks: 3 },
          { id: 'water', name: 'Water Specialist', role: 'Pressure resilience', state: 'Processing', lastTask: 'Pump load balancing', tasks: 4 },
          { id: 'traffic', name: 'Traffic Specialist', role: 'Intersection timing', state: 'Needs Review', lastTask: 'Signal adaptation check', tasks: 3 },
          { id: 'recovery', name: 'Recovery Planner', role: 'Plan sequencing', state: 'Needs Review', lastTask: 'Recovery plan revising after rejection', tasks: 7 },
          { id: 'verify', name: 'Verification Agent', role: 'Evidence validation', state: 'Needs Review', lastTask: 'Rejected unsafe action RA-05', tasks: 6 },
        ],
        recoveryActions: [
          {
            id: 'RA-05',
            priority: 1,
            action: 'Bypass lockout and restore full load to S-01 without waiting for breaker audit',
            targetAsset: 'S-01',
            rationale: 'Attempted to accelerate restoration without verifying breaker interlocks.',
            prerequisites: 'No prerequisites satisfied',
            status: 'Rejected',
            verification: 'Failed',
          },
          {
            id: 'RA-01',
            priority: 2,
            action: 'Isolate the upstream feeder and reroute demand to reserve bus',
            targetAsset: 'S-01',
            rationale: 'Reduces cascading fault propagation while preserving hospital backup service.',
            prerequisites: 'Breaker status verification and latch confirmation',
            status: 'In Progress',
            verification: 'Pending',
          },
          {
            id: 'RA-02',
            priority: 3,
            action: 'Shift pump staging to emergency reserve pressure setpoint',
            targetAsset: 'W-02',
            rationale: 'Maintains critical water pressure during substation outage recovery.',
            prerequisites: 'Operator clearance and pressure threshold checks',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-03',
            priority: 4,
            action: 'Reduce traffic cycle times at junction T-04',
            targetAsset: 'T-04',
            rationale: 'Improves emergency corridor throughput while load remains unstable.',
            prerequisites: 'Signal controller validation',
            status: 'Pending',
            verification: 'Pending',
          },
          {
            id: 'RA-04',
            priority: 5,
            action: 'Validate backup generator startup sequence',
            targetAsset: 'G-01',
            rationale: 'Provides resilient power to critical healthcare loads if the utility feeder remains unstable.',
            prerequisites: 'Gas and lube checks',
            status: 'Verified',
            verification: 'Verified',
          },
        ],
        evidence: [
          {
            id: 'EV-020',
            timestamp: '12:22 UTC',
            source: 'Verification Agent',
            type: 'Action rejected',
            message: 'Proposed action RA-05 failed verification checks.',
            detail: 'Lockout and breaker audit were incomplete; action rejected before execution.',
            actionId: 'RA-05',
          },
          ...baseEvidence,
        ],
        notifications: [
          { id: 'n-v-1', title: 'Action rejected', detail: 'Unsafe proposal blocked by verifier', time: '12:22 UTC', kind: 'warning' },
        ],
      }
  }
}

function getScenarioDefaults(scenarioId: ScenarioId): {
  incidentId: string
  assetId: string
  actionId: string
} {
  switch (scenarioId) {
    case 'substation-failure':
      return { incidentId: 'INC-2041', assetId: 'S-01', actionId: 'RA-01' }
    case 'backup-generator':
      return { incidentId: 'INC-2042', assetId: 'G-01', actionId: 'RA-04' }
    case 'unknown-asset':
      return { incidentId: 'INC-9000', assetId: 'S-01', actionId: 'RA-06' }
    case 'duplicate-incident':
      return { incidentId: 'INC-2041-DUP', assetId: 'S-01', actionId: 'RA-01' }
    case 'invalid-action':
      return { incidentId: 'INC-2041', assetId: 'S-01', actionId: 'RA-05' }
  }
}

const initialDemoState: DemoState = createScenarioState('substation-failure')

const scenarioCatalog: Array<{ id: ScenarioId; name: string; description: string; kind: string }> = [
  { id: 'substation-failure', name: 'Substation S-01 failure', description: 'Primary electrical outage cascades through water and traffic services.', kind: 'Critical' },
  { id: 'backup-generator', name: 'Backup generator G-01 unavailable', description: 'Reserve supply is offline and healthcare continuity requires manual checks.', kind: 'High' },
  { id: 'unknown-asset', name: 'Unknown asset incident', description: 'An unrecognized asset ID is reported and should fail safely.', kind: 'Warning' },
  { id: 'duplicate-incident', name: 'Duplicate incident report', description: 'A repeated incident is detected and deduplicated in the queue.', kind: 'Medium' },
  { id: 'invalid-action', name: 'Invalid proposed action rejected', description: 'Recovery planner proposes a disallowed sequence and verifier rejects it.', kind: 'Medium' },
]

const severityColor: Record<Severity, string> = {
  Critical: 'critical',
  High: 'high',
  Medium: 'medium',
  Low: 'low',
}

const stateColor: Record<AssetStatus, string> = {
  critical: 'critical',
  warning: 'warning',
  normal: 'normal',
  unavailable: 'unavailable',
}

const statusTone: Record<RecoveryStatus | VerificationState, string> = {
  Pending: 'pending',
  'In Progress': 'progress',
  Verified: 'verified',
  Rejected: 'rejected',
  Failed: 'rejected',
}

const pageTitles: Record<PageKey, string> = {
  overview: 'Command Center',
  incidents: 'Live Incidents',
  'digital-twin': 'Digital Twin',
  'agent-network': 'Agent Network',
  'recovery-plans': 'Recovery Plans',
  'evidence-ledger': 'Evidence Ledger',
  'simulation-lab': 'Simulation Lab',
  settings: 'Settings',
}

function App() {
  const [page, setPage] = useState<PageKey>('overview')
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'dark'
    return window.localStorage.getItem(THEME_KEY) === 'light' ? 'light' : 'dark'
  })
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [demo, setDemo] = useState<DemoState>(() => {
    if (typeof window === 'undefined') return initialDemoState
    const saved = window.localStorage.getItem(LS_KEY)
    if (!saved) return initialDemoState
    try {
      const parsed = JSON.parse(saved) as DemoState
      if (parsed && parsed.activeScenario && Array.isArray(parsed.assets) && Array.isArray(parsed.incidents)) {
        return parsed
      }
      return initialDemoState
    } catch {
      return initialDemoState
    }
  })
  const [selectedScenarioId, setSelectedScenarioId] = useState<ScenarioId>(() => demo.activeScenario ?? 'substation-failure')
  const [selectedIncidentId, setSelectedIncidentId] = useState(() => {
    const defaults = getScenarioDefaults(demo.activeScenario ?? 'substation-failure')
    return demo.incidents.some((i) => i.id === defaults.incidentId) ? defaults.incidentId : (demo.incidents[0]?.id ?? 'INC-2041')
  })
  const [selectedAssetId, setSelectedAssetId] = useState(() => {
    const defaults = getScenarioDefaults(demo.activeScenario ?? 'substation-failure')
    return demo.assets.some((a) => a.id === defaults.assetId) ? defaults.assetId : (demo.assets[0]?.id ?? 'S-01')
  })
  const [selectedActionId, setSelectedActionId] = useState(() => {
    const defaults = getScenarioDefaults(demo.activeScenario ?? 'substation-failure')
    return demo.recoveryActions.some((a) => a.id === defaults.actionId) ? defaults.actionId : (demo.recoveryActions[0]?.id ?? 'RA-01')
  })
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [commandInput, setCommandInput] = useState('')
  const [commandHistory, setCommandHistory] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([
    { role: 'assistant', text: 'Ready for local demo commands.' },
  ])
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    try {
      window.localStorage.setItem(LS_KEY, JSON.stringify(demo))
    } catch {
      // Ignore storage errors in restricted contexts
    }
  }, [demo])

  useEffect(() => {
    try {
      window.localStorage.setItem(THEME_KEY, theme)
    } catch {
      // Ignore storage errors in restricted contexts
    }
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme)
      document.documentElement.style.colorScheme = theme
    }
  }, [theme])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 1800)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const selectedIncident = demo.incidents.find((incident) => incident.id === selectedIncidentId) ?? demo.incidents[0]
  const selectedAsset = demo.assets.find((asset) => asset.id === selectedAssetId) ?? demo.assets[0]
  const selectedAction = demo.recoveryActions.find((action) => action.id === selectedActionId) ?? demo.recoveryActions[0]

  const filteredIncidents = useMemo(() => {
    const q = search.toLowerCase()
    return demo.incidents.filter((incident) => {
      const haystack = `${incident.id} ${incident.title} ${incident.description} ${incident.affectedAssets.join(' ')}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [demo.incidents, search])

  const filteredEvidence = useMemo(() => {
    const q = search.toLowerCase()
    return demo.evidence.filter((event) => {
      const haystack = `${event.id} ${event.source} ${event.type} ${event.message} ${event.detail}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [demo.evidence, search])

  const filteredActions = useMemo(() => {
    const q = search.toLowerCase()
    return demo.recoveryActions.filter((action) => {
      const haystack = `${action.id} ${action.action} ${action.targetAsset} ${action.rationale}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [demo.recoveryActions, search])

  const overviewIncidentCount = demo.incidents.length
  const affectedAssetCount = demo.assets.filter((asset) => asset.status !== 'normal').length
  const criticalDependencyCount = demo.assets.filter((asset) => asset.criticality === 'Critical' || asset.status === 'critical').length
  const verifiedActionCount = demo.recoveryActions.filter((action) => action.verification === 'Verified').length

  const affectedBySelection = useMemo(() => {
    if (!selectedIncident) return new Set<string>()

    const dependencies = new Set<string>()
    const queue = [...selectedIncident.affectedAssets]
    while (queue.length) {
      const next = queue.shift()
      if (!next) continue
      if (dependencies.has(next)) continue
      dependencies.add(next)
      const asset = demo.assets.find((item) => item.id === next)
      if (asset) {
        for (const dep of asset.dependencies) {
          if (!dependencies.has(dep)) queue.push(dep)
        }
      }
    }
    return dependencies
  }, [demo.assets, selectedIncident])

  function updateScenario(scenarioId: ScenarioId) {
    const nextState = createScenarioState(scenarioId)
    const defaults = getScenarioDefaults(scenarioId)
    setDemo(nextState)
    setSelectedScenarioId(scenarioId)
    setSelectedIncidentId(defaults.incidentId)
    setSelectedAssetId(defaults.assetId)
    setSelectedActionId(defaults.actionId)
  }

  const runCommand = () => {
    const trimmed = commandInput.trim()
    const lower = trimmed.toLowerCase()

    if (!trimmed) {
      const activeScenarioItem = scenarioCatalog.find((s) => s.id === selectedScenarioId) ?? scenarioCatalog[0]
      updateScenario(activeScenarioItem.id)
      setCommandHistory((prev) => [
        ...prev,
        { role: 'user', text: `Run Demo Scenario: ${activeScenarioItem.name}` },
        {
          role: 'assistant',
          text: `Executing scenario: ${activeScenarioItem.name}. Digital Twin, incident queue, recovery plans, and agent activity updated.`,
        },
      ])
      setToast(`Scenario executed: ${activeScenarioItem.name}`)
      return
    }

    let response = 'Unsupported request. Try commands like “Substation S-01 failed”, “G-01 unavailable”, “Unknown asset incident”, or “Show critical incidents”.'
    let scenario: ScenarioId | undefined

    if (
      lower.includes('s-01') ||
      lower.includes('s01') ||
      lower.includes('substation')
    ) {
      response = 'Scenario queued: Substation S-01 failure. Downstream electrical impacts are being modeled across water and traffic infrastructure.'
      scenario = 'substation-failure'
    } else if (
      lower.includes('g-01') ||
      lower.includes('g01') ||
      lower.includes('generator')
    ) {
      response = 'Scenario queued: Backup generator G-01 unavailable. Healthcare continuity and reserve capacity are under review.'
      scenario = 'backup-generator'
    } else if (
      lower.includes('unknown') ||
      lower.includes('x-99') ||
      lower.includes('x99') ||
      lower.includes('quarantine') ||
      lower.includes('unregistered')
    ) {
      response = 'Scenario queued: Unknown asset incident reported. Ingress pipeline quarantined asset X-99 to protect operational model.'
      scenario = 'unknown-asset'
    } else if (lower.includes('duplicate')) {
      response = 'Scenario queued: Duplicate incident report detected. Secondary report merged into active incident chain.'
      scenario = 'duplicate-incident'
    } else if (
      lower.includes('invalid') ||
      lower.includes('bypass') ||
      lower.includes('rejected') ||
      lower.includes('disallowed')
    ) {
      response = 'Scenario queued: Invalid proposed action submitted. Verification agent rejected unsafe sequence.'
      scenario = 'invalid-action'
    } else if (lower.includes('water')) {
      const waterAsset = demo.assets.find((item) => item.id === 'W-02')
      response = waterAsset
        ? `Water asset: ${waterAsset.id} (${waterAsset.name}) is currently in ${waterAsset.status} status and is downstream of S-01.`
        : 'Affected water assets: W-02 (Water Pump) is downstream of S-01.'
    } else if (lower.includes('incident')) {
      response = `Active incidents: ${demo.incidents.map((i) => `${i.id} (${i.severity})`).join(', ')}.`
    }

    if (scenario) {
      updateScenario(scenario)
      setToast(`Scenario executed: ${scenarioCatalog.find((s) => s.id === scenario)?.name ?? scenario}`)
      setPage('overview')
    }

    setCommandHistory((prev) => [...prev, { role: 'user', text: trimmed }, { role: 'assistant', text: response }])
    setCommandInput('')
  }

  const handleSearch = (value: string) => {
    setSearch(value)
    if (value && demo.incidents.length > 0) {
      const incidentMatch = demo.incidents.find((incident) =>
        `${incident.id} ${incident.title}`.toLowerCase().includes(value.toLowerCase()),
      )
      if (incidentMatch) setSelectedIncidentId(incidentMatch.id)
    }
  }

  const exportEvidence = () => {
    const payload = filteredEvidence.map((item) => ({
      id: item.id,
      timestamp: item.timestamp,
      source: item.source,
      type: item.type,
      message: item.message,
      detail: item.detail,
      incidentId: item.incidentId ?? null,
      actionId: item.actionId ?? null,
    }))

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'aegisgrid-demo-evidence.json'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    setToast('Demo evidence exported')
  }

  const copyEvidenceId = async (value: string) => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(value)
      } else {
        const textarea = document.createElement('textarea')
        textarea.value = value
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      }
      setToast('Evidence ID copied')
    } catch {
      setToast('Copy action unavailable in this browser')
    }
  }

  const renderPage = () => {
    switch (page) {
      case 'incidents':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">Simulated operations</p>
                <h2>Live incident queue</h2>
              </div>
              <div className="pill-group">
                <span className="status-badge danger">Critical view</span>
                <span className="status-badge info">{filteredIncidents.length} visible</span>
              </div>
            </div>

            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Incident ID</th>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>Affected assets</th>
                    <th>Status</th>
                    <th>Last update</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIncidents.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                        No incidents match your filter.
                      </td>
                    </tr>
                  ) : (
                    filteredIncidents.map((incident) => (
                      <tr
                        key={incident.id}
                        className={selectedIncidentId === incident.id ? 'selected-row' : ''}
                        onClick={() => setSelectedIncidentId(incident.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td>{incident.id}</td>
                        <td>{incident.title}</td>
                        <td><StatusBadge kind="severity" value={incident.severity} /></td>
                        <td>{incident.affectedAssets.join(', ')}</td>
                        <td>{incident.status}</td>
                        <td>{incident.lastUpdate}</td>
                        <td>
                          <button
                            type="button"
                            className="link-button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedIncidentId(incident.id)
                            }}
                          >
                            View detail
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="detail-panel">
              <h3>Selected incident: {selectedIncident.id}</h3>
              <div className="detail-grid">
                <div>
                  <p className="small-label">Title</p>
                  <p>{selectedIncident.title}</p>
                </div>
                <div>
                  <p className="small-label">Severity</p>
                  <StatusBadge kind="severity" value={selectedIncident.severity} />
                </div>
                <div>
                  <p className="small-label">Status</p>
                  <p>{selectedIncident.status}</p>
                </div>
                <div>
                  <p className="small-label">Affected assets</p>
                  <p>{selectedIncident.affectedAssets.join(', ')}</p>
                </div>
              </div>
              <p className="muted-text">{selectedIncident.description}</p>
            </div>
          </div>
        )
      case 'digital-twin':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">Live dependency model</p>
                <h2>Digital twin</h2>
              </div>
              <div className="action-row compact">
                <select value={selectedScenarioId} onChange={(event) => setSelectedScenarioId(event.target.value as ScenarioId)}>
                  {scenarioCatalog.map((scenario) => (
                    <option key={scenario.id} value={scenario.id}>{scenario.name}</option>
                  ))}
                </select>
                <button type="button" className="primary-button" onClick={() => { updateScenario(selectedScenarioId); setToast('Scenario applied'); }}>
                  Run Scenario
                </button>
              </div>
            </div>

            <div className="digital-twin-shell">
              <div className="graph-panel">
                <DependencyGraph assets={demo.assets} selectedAsset={selectedAssetId} onSelect={setSelectedAssetId} affectedAssetIds={[...affectedBySelection]} />
              </div>
              <div className="asset-inspector">
                <h3>Asset inspector</h3>
                <div className="inspector-card">
                  <div className="asset-title-row">
                    <span className={`status-dot ${stateColor[selectedAsset.status]}`}></span>
                    <div>
                      <div className="asset-id">{selectedAsset.id}</div>
                      <h4>{selectedAsset.name}</h4>
                    </div>
                  </div>
                  <div className="meta-grid">
                    <div><span>Type</span><strong>{selectedAsset.type}</strong></div>
                    <div><span>Status</span><strong>{selectedAsset.status}</strong></div>
                    <div><span>Criticality</span><strong>{selectedAsset.criticality}</strong></div>
                    <div><span>Last event</span><strong>{selectedAsset.lastEvent}</strong></div>
                  </div>
                  <p className="muted-text">Dependency relationships: {selectedAsset.dependencies.join(', ') || 'None'}</p>
                </div>
                <div className="legend">
                  <span><i className="legend-swatch critical"></i>Critical</span>
                  <span><i className="legend-swatch warning"></i>Warning</span>
                  <span><i className="legend-swatch normal"></i>Normal</span>
                  <span><i className="legend-swatch unavailable"></i>Unavailable</span>
                </div>
              </div>
            </div>
          </div>
        )
      case 'agent-network':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">SIMULATED AGENT ACTIVITY</p>
                <h2>Specialist network</h2>
              </div>
              <span className="status-badge info">Local demo only</span>
            </div>
            <div className="agent-grid">
              {demo.agents.map((agent) => (
                <div key={agent.id} className="agent-card">
                  <div className="agent-head">
                    <div>
                      <p className="small-label">Role</p>
                      <h3>{agent.name}</h3>
                    </div>
                    <StatusBadge kind="state" value={agent.state} />
                  </div>
                  <p className="muted-text">{agent.role}</p>
                  <div className="agent-meta"><span>Last task</span><strong>{agent.lastTask}</strong></div>
                  <div className="agent-meta"><span>Tasks</span><strong>{agent.tasks}</strong></div>
                </div>
              ))}
            </div>
            <div className="timeline-panel">
              <h3>Collaboration timeline</h3>
              <div className="timeline">
                {demo.evidence.slice(0, 4).map((event) => (
                  <div key={event.id} className="timeline-item">
                    <span className="timeline-dot"></span>
                    <div>
                      <strong>{event.timestamp}</strong>
                      <p>{event.source}: {event.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      case 'recovery-plans':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">Recovery coordination</p>
                <h2>Recovery plans</h2>
              </div>
              <button type="button" className="primary-button" onClick={() => {
                setDemo((current) => ({
                  ...current,
                  recoveryActions: current.recoveryActions.map((action, index) => ({
                    ...action,
                    priority: index + 1,
                    status: index === 0 ? 'In Progress' : 'Pending',
                    verification: index === 3 ? 'Verified' : 'Pending',
                  })),
                }))
                setToast('Demo plan recalculated')
              }}>
                Recalculate Demo Plan
              </button>
            </div>

            <div className="filter-grid">
              <span className="status-badge info">Priority filter</span>
              <span className="status-badge info">Status filter</span>
            </div>

            <div className="plan-list">
              {filteredActions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  No recovery actions match your filter.
                </div>
              ) : (
                filteredActions.map((action) => (
                  <button
                    key={action.id}
                    type="button"
                    className={`plan-item ${selectedActionId === action.id ? 'active' : ''}`}
                    onClick={() => setSelectedActionId(action.id)}
                  >
                    <div className="plan-topline">
                      <span>#{action.priority}</span>
                      <span className="status-badge info">{action.targetAsset}</span>
                    </div>
                    <h4>{action.action}</h4>
                    <p>{action.rationale}</p>
                    <div className="plan-meta">
                      <span>Prereqs: {action.prerequisites}</span>
                      <StatusBadge kind="recovery" value={action.status} />
                      <StatusBadge kind="verification" value={action.verification} />
                    </div>
                  </button>
                ))
              )}
            </div>

            <div className="detail-panel">
              <h3>Action detail: {selectedAction?.id ?? 'None selected'}</h3>
              {selectedAction && (
                <div className="detail-grid two-col">
                  <div>
                    <p className="small-label">Target asset</p>
                    <p>{selectedAction.targetAsset}</p>
                  </div>
                  <div>
                    <p className="small-label">Priority</p>
                    <p>#{selectedAction.priority}</p>
                  </div>
                  <div>
                    <p className="small-label">Status</p>
                    <StatusBadge kind="recovery" value={selectedAction.status} />
                  </div>
                  <div>
                    <p className="small-label">Verification</p>
                    <StatusBadge kind="verification" value={selectedAction.verification} />
                  </div>
                </div>
              )}
              <p className="muted-text">{selectedAction?.rationale}</p>
            </div>
          </div>
        )
      case 'evidence-ledger':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">DEMO GENERATED</p>
                <h2>Evidence ledger</h2>
              </div>
              <button type="button" className="secondary-button" onClick={exportEvidence}>
                <Download size={16} /> Export JSON
              </button>
            </div>

            <div className="table-shell">
              <table className="data-table compact-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Type</th>
                    <th>Source</th>
                    <th>Message</th>
                    <th>Incident</th>
                    <th>Action</th>
                    <th>ID</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvidence.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                        No evidence entries match your filter.
                      </td>
                    </tr>
                  ) : (
                    filteredEvidence.map((event) => (
                      <tr key={event.id}>
                        <td>{event.timestamp}</td>
                        <td>{event.type}</td>
                        <td>{event.source}</td>
                        <td>{event.message}</td>
                        <td>{event.incidentId ?? '—'}</td>
                        <td>{event.actionId ?? '—'}</td>
                        <td>
                          <button type="button" className="tiny-button" onClick={() => copyEvidenceId(event.id)}>
                            {event.id}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )
      case 'simulation-lab':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">Deterministic scenarios</p>
                <h2>Simulation lab</h2>
              </div>
              <button type="button" className="secondary-button" onClick={() => {
                setDemo(createScenarioState('substation-failure'))
                setSelectedScenarioId('substation-failure')
                setSelectedIncidentId('INC-2041')
                setSelectedAssetId('S-01')
                setSelectedActionId('RA-01')
                setToast('Demo state reset')
              }}>
                <Repeat size={16} /> Reset demo
              </button>
            </div>

            <div className="scenario-grid">
              {scenarioCatalog.map((scenario) => (
                <button key={scenario.id} type="button" className={`scenario-card ${selectedScenarioId === scenario.id ? 'active' : ''}`} onClick={() => setSelectedScenarioId(scenario.id)}>
                  <div className="scenario-topline">
                    <span className="status-badge danger">{scenario.kind}</span>
                    <span>{scenario.name}</span>
                  </div>
                  <p>{scenario.description}</p>
                </button>
              ))}
            </div>

            <div className="launch-panel">
              <div className="launch-header">
                <h3>{scenarioCatalog.find((item) => item.id === selectedScenarioId)?.name}</h3>
                <button type="button" className="primary-button" onClick={() => {
                  updateScenario(selectedScenarioId)
                  setToast('Scenario executed')
                }}>
                  Run Scenario
                </button>
              </div>
              <div className="timeline">
                <div className="timeline-item">
                  <span className="timeline-dot"></span>
                  <div>
                    <strong>Scenario launch</strong>
                    <p>Intake module accepted the selected deterministic incident sequence.</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <span className="timeline-dot"></span>
                  <div>
                    <strong>Impact propagation</strong>
                    <p>Shared state updated across the asset graph, incidents, agents, and action queue.</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <span className="timeline-dot"></span>
                  <div>
                    <strong>Outcome summary</strong>
                    <p>Action status and evidence trail reflect the scenario outcome without a live backend.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      case 'settings':
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">Prototype configuration</p>
                <h2>Settings</h2>
              </div>
              <span className="status-badge info">Frontend v0.1.0</span>
            </div>

            <div className="settings-grid">
              <div className="detail-panel">
                <h3>Demo environment</h3>
                <ul className="settings-list">
                  <li><span>Mode</span><strong>DEMO / SIMULATED</strong></li>
                  <li><span>Persistence</span><strong>Local demo state</strong></li>
                  <li><span>Search</span><strong>Local operation filters</strong></li>
                  <li><span>Motion</span><strong>Reduced motion aware</strong></li>
                </ul>
              </div>
              <div className="detail-panel">
                <h3>Future integration</h3>
                <ul className="settings-list">
                  <li><span>ASI</span><strong>NOT CONNECTED YET</strong></li>
                  <li><span>Agentverse</span><strong>NOT CONNECTED YET</strong></li>
                  <li><span>ACP</span><strong>NOT CONNECTED YET</strong></li>
                  <li><span>Backend</span><strong>NOT CONNECTED YET</strong></li>
                </ul>
              </div>
            </div>
          </div>
        )
      default:
        return (
          <div className="page-stack">
            <div className="section-header align-between">
              <div>
                <p className="eyebrow">Understand cascading risk · coordinate recovery</p>
                <h2>{pageTitles.overview}</h2>
              </div>
            </div>
            <div className="overview-grid">
              <MetricCard value={overviewIncidentCount.toString()} label="Active Incidents" detail="Across electrical, water and traffic services" onClick={() => setPage('incidents')} />
              <MetricCard value={affectedAssetCount.toString()} label="Affected Assets" detail="Currently in warning or critical states" onClick={() => setPage('digital-twin')} />
              <MetricCard value={criticalDependencyCount.toString()} label="Critical Dependencies" detail="Assets linked to the outage chain" onClick={() => setPage('digital-twin')} />
              <MetricCard value={verifiedActionCount.toString()} label="Verified Actions" detail="Validated against demo evidence" onClick={() => setPage('recovery-plans')} />
            </div>

            <div className="overview-main">
              <div className="dual-panel">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">Digital twin</p>
                    <h3>Infrastructure dependency map</h3>
                  </div>
                  <div className="scenario-box">{demo.activeScenario}</div>
                </div>
                <div className="graph-preview-box">
                  <DependencyGraph assets={demo.assets} selectedAsset={selectedAssetId} onSelect={setSelectedAssetId} affectedAssetIds={[...affectedBySelection]} compact />
                </div>
              </div>

              <div className="command-panel">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">Incident command · simulated</p>
                    <h3>Command console</h3>
                  </div>
                </div>
                <div className="command-suggestions">
                  <button type="button" onClick={() => setCommandInput('Substation S-01 failed')}>Substation S-01 failed</button>
                  <button type="button" onClick={() => setCommandInput('G-01 is unavailable')}>G-01 is unavailable</button>
                  <button type="button" onClick={() => setCommandInput('Unknown asset incident')}>Unknown asset incident</button>
                  <button type="button" onClick={() => setCommandInput('Show affected water assets')}>Show affected water assets</button>
                  <button type="button" onClick={() => setCommandInput('Show critical incidents')}>Show critical incidents</button>
                </div>
                <div className="command-input-wrap">
                  <Search size={16} />
                  <input value={commandInput} onChange={(event) => setCommandInput(event.target.value)} placeholder="Enter demo command" onKeyDown={(event) => { if (event.key === 'Enter') runCommand() }} />
                </div>
                <button type="button" className="primary-button full" onClick={runCommand}>Run Demo Scenario</button>
                <div className="transcript-box">
                  {commandHistory.slice(-4).map((item, index) => (
                    <div key={`${item.role}-${index}`} className={`transcript-line ${item.role}`}>
                      {item.text}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="overview-grid bottom-grid">
              <div className="panel-block">
                <div className="panel-header">
                  <p className="eyebrow">Incident queue</p>
                  <h3>Latest incidents</h3>
                </div>
                <table className="mini-table">
                  <tbody>
                    {demo.incidents.map((incident) => (
                      <tr key={incident.id} onClick={() => setSelectedIncidentId(incident.id)}>
                        <td>{incident.id}</td>
                        <td>{incident.title}</td>
                        <td><StatusBadge kind="severity" value={incident.severity} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="panel-block">
                <div className="panel-header">
                  <p className="eyebrow">Recovery preview</p>
                  <h3>Priority actions</h3>
                </div>
                <div className="stack-list">
                  {demo.recoveryActions.slice(0, 3).map((action) => (
                    <div key={action.id} className="stack-item">
                      <strong>#{action.priority} {action.targetAsset}</strong>
                      <span>{action.action}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel-block">
                <div className="panel-header">
                  <p className="eyebrow">Evidence trail</p>
                  <h3>Recent events</h3>
                </div>
                <div className="stack-list">
                  {demo.evidence.slice(0, 3).map((event) => (
                    <div key={event.id} className="stack-item">
                      <strong>{event.timestamp}</strong>
                      <span>{event.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className={`sidebar ${mobileNavOpen ? 'mobile-open' : ''}`}>
        <div className="brand-block">
          <div className="brand-mark" aria-label="AegisGrid logo">
            <span className="shield-shape" />
            <span className="node node-a" />
            <span className="node node-b" />
            <span className="node node-c" />
          </div>
          <div>
            <div className="brand-name">AegisGrid</div>
            <div className="brand-tag">RESILIENCE INTELLIGENCE</div>
          </div>
        </div>

        <nav className="nav-stack" aria-label="Sidebar navigation">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" className={`nav-item ${page === id ? 'active' : ''}`} onClick={() => { setPage(id); setMobileNavOpen(false) }}>
              <Icon size={16} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="icon-button mobile-only"
              aria-label={mobileNavOpen ? 'Close navigation' : 'Open navigation'}
              aria-expanded={mobileNavOpen}
              onClick={() => setMobileNavOpen((open) => !open)}
            >
              <Menu size={18} />
            </button>
            <div>
              <div className="topbar-kicker">{pageTitles[page]}</div>
              <div className="breadcrumbs">Overview <ChevronRight size={14} /> {pageTitles[page]}</div>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="demo-chip">DEMO · LOCAL</div>
            <div className="search-box">
              <Search size={16} />
              <input value={search} onChange={(event) => handleSearch(event.target.value)} placeholder="Search demo data" />
            </div>
            <div className="notification-wrap">
              <button
                type="button"
                className="icon-button"
                aria-label="Notifications"
                aria-expanded={notificationsOpen}
                onClick={() => setNotificationsOpen((value) => !value)}
              >
                <Bell size={18} />
              </button>
              {notificationsOpen && (
                <div className="notification-panel">
                  {demo.notifications.map((notification) => (
                    <div key={notification.id} className="notification-item">
                      <div className={`notification-dot ${notification.kind}`}></div>
                      <div>
                        <strong>{notification.title}</strong>
                        <p>{notification.detail}</p>
                      </div>
                      <span>{notification.time}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button
              type="button"
              className="icon-button theme-toggle"
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              onClick={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')}
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="system-health">
              <Activity size={16} />
              <span>SIMULATED HEALTH</span>
            </div>
            <button type="button" className="primary-button" onClick={() => {
              setSelectedScenarioId('substation-failure')
              updateScenario('substation-failure')
              setToast('Simulation reset to baseline')
            }}>
              NEW SIMULATION
            </button>
          </div>
        </header>

        <div className="page-content">{renderPage()}</div>
      </main>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}

function MetricCard({ value, label, detail, onClick }: { value: string; label: string; detail: string; onClick: () => void }) {
  return (
    <button type="button" className="metric-card" onClick={onClick}>
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        <TrendingUp size={14} />
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-detail">{detail}</div>
    </button>
  )
}

function StatusBadge({ kind, value }: { kind: 'severity' | 'state' | 'recovery' | 'verification'; value: string }) {
  const tone =
    kind === 'severity'
      ? severityColor[value as Severity]
      : kind === 'state'
        ? value === 'Ready'
          ? 'normal'
          : value === 'Processing'
            ? 'warning'
            : 'critical'
        : kind === 'recovery'
          ? statusTone[value as RecoveryStatus]
          : statusTone[value as VerificationState]

  return <span className={`status-badge ${tone}`}>{value}</span>
}

function DependencyGraph({
  assets,
  selectedAsset,
  onSelect,
  affectedAssetIds,
  compact = false,
}: {
  assets: Asset[]
  selectedAsset: string
  onSelect: (value: string) => void
  affectedAssetIds: string[]
  compact?: boolean
}) {
  const svgWidth = compact ? 700 : 760
  const svgHeight = compact ? 360 : 440
  const affected = new Set(affectedAssetIds)

  const edges = [
    { from: 'S-01', to: 'G-01', type: 'support', bend: -18 },
    { from: 'S-01', to: 'W-02', type: 'dependency', bend: 20 },
    { from: 'S-01', to: 'T-04', type: 'dependency', bend: -16 },
    { from: 'S-01', to: 'H-01', type: 'dependency', bend: -116 },
    { from: 'G-01', to: 'H-01', type: 'support', bend: 40 },
    { from: 'W-02', to: 'H-01', type: 'dependency', bend: 20 },
    { from: 'T-04', to: 'H-01', type: 'dependency', bend: -20 },
  ]

  return (
    <svg className="dependency-graph" viewBox={`0 0 ${svgWidth} ${svgHeight}`} role="img" aria-label="Infrastructure dependency graph">
      <defs>
        <marker id={`arrowhead-${compact ? 'overview' : 'twin'}`} markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
          <path d="M0,0 L10,4 L0,8 Z" fill="var(--graph-edge)"></path>
        </marker>
        <marker id={`arrowhead-affected-${compact ? 'overview' : 'twin'}`} markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
          <path d="M0,0 L10,4 L0,8 Z" fill="var(--amber)"></path>
        </marker>
      </defs>

      {edges.map((edge, idx) => {
        const from = assets.find((asset) => asset.id === edge.from)
        const to = assets.find((asset) => asset.id === edge.to)
        if (!from || !to) return null
        const dx = to.x - from.x
        const dy = to.y - from.y
        const length = Math.hypot(dx, dy)
        if (length === 0) return null
        const x1 = from.x + (dx / length) * 35
        const y1 = from.y + (dy / length) * 35
        const x2 = to.x - (dx / length) * 39
        const y2 = to.y - (dy / length) * 39
        const controlX = (x1 + x2) / 2 - (dy / length) * edge.bend
        const controlY = (y1 + y2) / 2 + (dx / length) * edge.bend
        const labelX = (x1 + 2 * controlX + x2) / 4
        const labelY = (y1 + 2 * controlY + y2) / 4 - 7
        const isAffected = affected.has(edge.from) || affected.has(edge.to)
        return (
          <g key={`${edge.from}-${edge.to}-${idx}`}>
            <path
              d={`M ${x1} ${y1} Q ${controlX} ${controlY} ${x2} ${y2}`}
              className={isAffected ? 'edge affected' : 'edge'}
              markerEnd={`url(#arrowhead-${isAffected ? 'affected-' : ''}${compact ? 'overview' : 'twin'})`}
            />
            <text x={labelX} y={labelY} className="edge-label">{edge.type}</text>
          </g>
        )
      })}

      {assets.map((asset) => (
        <g
          key={asset.id}
          className={`asset-node ${selectedAsset === asset.id ? 'selected' : ''}`}
          transform={`translate(${asset.x}, ${asset.y})`}
          onClick={() => onSelect(asset.id)}
          tabIndex={0}
          role="button"
          aria-label={`Select ${asset.id}, ${asset.name}, ${asset.status}`}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault()
              onSelect(asset.id)
            }
          }}
        >
          <circle r={affected.has(asset.id) ? 38 : 31} className={`node-body ${stateColor[asset.status]}`} />
          <text y={4} className="node-text">{asset.id}</text>
          <text y={52} className="node-label">{asset.name}</text>
          <title>{`${asset.name}: ${asset.status}`}</title>
        </g>
      ))}
    </svg>
  )
}

export default App
