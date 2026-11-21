import 'dart:async';
import '../../models/agent.dart';
import '../agent_service.dart';

class MockAgentService implements AgentService {
  static final MockAgentService _instance = MockAgentService._internal();
  factory MockAgentService() => _instance;
  MockAgentService._internal();

  @override
  List<AgentInfo> getInitialAgents() {
    return const [
      AgentInfo(
        id: 'agent_planner',
        name: 'Planner Agent',
        roleDescription: 'Decomposes problem into structured objectives & dependency graphs.',
        avatarIcon: 'architecture',
        state: AgentState.waiting,
        currentActivity: 'Waiting in dispatch queue',
        progress: 0.0,
      ),
      AgentInfo(
        id: 'agent_researcher',
        name: 'Researcher Agent',
        roleDescription: 'Retrieves relevant domain literature, RFCs, and industry benchmarks.',
        avatarIcon: 'search',
        state: AgentState.waiting,
        currentActivity: 'Awaiting plan dependencies',
        progress: 0.0,
      ),
      AgentInfo(
        id: 'agent_technical_analyst',
        name: 'Technical Analyst',
        roleDescription: 'Analyzes algorithmic feasibility, time complexity, and scalability tradeoffs.',
        avatarIcon: 'memory',
        state: AgentState.waiting,
        currentActivity: 'Standby for technical profiling',
        progress: 0.0,
      ),
      AgentInfo(
        id: 'agent_critic',
        name: 'Critic Agent',
        roleDescription: 'Evaluates edge cases, failure scenarios, and architectural bottlenecks.',
        avatarIcon: 'security',
        state: AgentState.waiting,
        currentActivity: 'Standby for adversarial stress-testing',
        progress: 0.0,
      ),
      AgentInfo(
        id: 'agent_synthesizer',
        name: 'Synthesizer Agent',
        roleDescription: 'Harmonizes agent inputs into a comprehensive, verified solution blueprint.',
        avatarIcon: 'auto_fix_high',
        state: AgentState.waiting,
        currentActivity: 'Standby for multi-agent consensus',
        progress: 0.0,
      ),
    ];
  }

  @override
  Stream<List<AgentInfo>> runAnalysisSimulation(String problem) async* {
    List<AgentInfo> current = List.from(getInitialAgents());

    // Step 1: Planner begins working
    current = [
      current[0].copyWith(
        state: AgentState.working,
        currentActivity: 'Decomposing problem statement into 4 work packages...',
        progress: 0.45,
      ),
      current[1],
      current[2],
      current[3],
      current[4],
    ];
    yield List.unmodifiable(current);
    await Future.delayed(const Duration(milliseconds: 900));

    // Step 2: Planner completes, Researcher begins
    current = [
      current[0].copyWith(
        state: AgentState.completed,
        currentActivity: 'Structured taxonomy & requirements tree formulated',
        outputSummary: '4 core architectural requirements mapped with priority tags.',
        progress: 1.0,
      ),
      current[1].copyWith(
        state: AgentState.working,
        currentActivity: 'Synthesizing relevant design patterns & consensus protocols...',
        progress: 0.6,
      ),
      current[2],
      current[3],
      current[4],
    ];
    yield List.unmodifiable(current);
    await Future.delayed(const Duration(milliseconds: 1000));

    // Step 3: Researcher completes, Technical Analyst working
    current = [
      current[0],
      current[1].copyWith(
        state: AgentState.completed,
        currentActivity: 'Retrieved 8 distributed systems patterns & fault topologies',
        outputSummary: 'Benchmarked Raft vs CRDT state-sync approaches.',
        progress: 1.0,
      ),
      current[2].copyWith(
        state: AgentState.working,
        currentActivity: 'Evaluating O(N) message complexity & network partition resilience...',
        progress: 0.7,
      ),
      current[3],
      current[4],
    ];
    yield List.unmodifiable(current);
    await Future.delayed(const Duration(milliseconds: 1000));

    // Step 4: Technical Analyst completes, Critic working
    current = [
      current[0],
      current[1],
      current[2].copyWith(
        state: AgentState.completed,
        currentActivity: 'Complexity bounded to O(log N) through event-driven hash rings',
        outputSummary: 'Sub-second recovery latency confirmed in simulated topology.',
        progress: 1.0,
      ),
      current[3].copyWith(
        state: AgentState.working,
        currentActivity: 'Adversarial audit: checking Byzantine failures and network splits...',
        progress: 0.85,
      ),
      current[4],
    ];
    yield List.unmodifiable(current);
    await Future.delayed(const Duration(milliseconds: 1000));

    // Step 5: Critic completes, Synthesizer working
    current = [
      current[0],
      current[1],
      current[2],
      current[3].copyWith(
        state: AgentState.completed,
        currentActivity: 'Audit verified: added tombstone expiration for split-brain edge case',
        outputSummary: 'No critical deadlock conditions found; 2 safety mitigations applied.',
        progress: 1.0,
      ),
      current[4].copyWith(
        state: AgentState.working,
        currentActivity: 'Compiling multi-agent artifacts into unified architectural consensus...',
        progress: 0.8,
      ),
    ];
    yield List.unmodifiable(current);
    await Future.delayed(const Duration(milliseconds: 1100));

    // Step 6: All Completed
    current = [
      current[0],
      current[1],
      current[2],
      current[3],
      current[4].copyWith(
        state: AgentState.completed,
        currentActivity: 'Production Blueprint synthesized & cross-validated',
        outputSummary: 'Finalized consensus matrix and executive action plan.',
        progress: 1.0,
      ),
    ];
    yield List.unmodifiable(current);
  }

  @override
  String getFinalSynthesis(String problem) {
    return '''# SangamX Multi-Agent Architectural Synthesis
**Problem Statement:** $problem

---

### 1. Executive Summary
The SangamX 5-Agent Swarm (Planner, Researcher, Technical Analyst, Critic, Synthesizer) has successfully decomposed and verified an architectural blueprint tailored to this problem statement.

### 2. Multi-Agent Findings
- **Planner:** Identified 3 primary subsystems: Orchestration Layer, State Synchronization Engine, and Resilient Storage Adapter.
- **Researcher:** Benchmarked against state-of-the-art hybrid gossip protocols and verified zero-dependency edge compatibility.
- **Technical Analyst:** Confirmed sub-50ms node heartbeat reconciliation with bounded memory footprint under O(log N) scaling.
- **Critic:** Hardened against Byzantine network partitions with deterministic vector clock tombstones and idempotency tokens.
- **Synthesizer:** Unified all constraints into an actionable 4-phase deployment blueprint.

### 3. Recommended Implementation Architecture
1. **Transport Layer:** Ephemeral WebRTC / WebSocket channels for low-latency peer coordination.
2. **Consensus Strategy:** Hybrid Optimistic Locking paired with conflict-free replicated data types (CRDTs).
3. **Audit & Safety Boundary:** Strict contract validation on agent inputs with automatic timeout circuit-breakers.

---
*Generated by SangamX Collaborative Intelligence Engine [Demo Sandbox]*''';
  }
}
