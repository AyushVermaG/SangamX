import 'dart:async';
import 'dart:convert';
import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart' as sp;
import '../../models/agent.dart';
import '../agent_service.dart';
import 'serverpod_client_provider.dart';

class ServerpodAgentService implements AgentService {
  final sp.Client _client;
  final Map<int, String> _finalAnswersByRoom = {};

  ServerpodAgentService({sp.Client? client})
      : _client = client ?? ServerpodClientProvider.getClient();

  @override
  List<AgentInfo> getInitialAgents() {
    return const [
      AgentInfo(
        id: 'agent_planner',
        name: 'Planner Agent',
        roleDescription: 'Decomposes problem into structured objectives & dependency graphs.',
        avatarIcon: 'architecture',
        state: AgentState.waiting,
        currentActivity: 'Waiting for task dispatch',
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
  Stream<List<AgentInfo>> watchAgents({
    required int roomId,
    String? problemStatement,
    int? taskId,
  }) async* {
    List<AgentInfo> agents = getInitialAgents();

    // 1. Subscribe to live stream FIRST to prevent race condition during snapshot fetch
    final stream = _client.task.watchTask(roomId);

    // 2. Fetch snapshot of active or known task to recover current state
    try {
      final sp.SharedTask? snapshot = taskId != null
          ? await _client.task.getTask(taskId)
          : await _client.task.getActiveTask(roomId);

      if (snapshot != null) {
        if (snapshot.finalAnswer != null && snapshot.finalAnswer!.isNotEmpty) {
          _finalAnswersByRoom[roomId] = snapshot.finalAnswer!;
        }

        if (snapshot.status == 'completed') {
          // All agents completed
          agents = agents.map((a) => a.copyWith(
            state: AgentState.completed,
            currentActivity: 'Workflow concluded',
            progress: 1.0,
          )).toList();
        } else if (snapshot.status == 'failed') {
          agents = agents.map((a) => a.copyWith(
            state: AgentState.failed,
            currentActivity: snapshot.error ?? 'Task failed',
          )).toList();
        } else if (snapshot.status == 'running' || snapshot.status == 'queued') {
          // Honest reconnected state: intermediate events cannot be replayed from DB
          agents = [
            agents[0].copyWith(
              state: AgentState.working,
              currentActivity: 'Connected to active room task...',
              progress: 0.2,
            ),
            ...agents.sublist(1),
          ];
        }
      }
    } catch (_) {
      // Reconnection or network hiccup; continue listening to live stream
    }

    yield List.unmodifiable(agents);

    // 3. Process incoming real-time Serverpod events
    await for (final sp.TaskUpdate update in stream) {
      if (update.roomId != roomId) continue;

      if (update.finalAnswer != null && update.finalAnswer!.isNotEmpty) {
        _finalAnswersByRoom[roomId] = update.finalAnswer!;
      }

      final event = update.event;
      final agentName = update.agent;
      Map<String, dynamic> data = {};
      if (update.data != null && update.data!.isNotEmpty) {
        try {
          data = jsonDecode(update.data!) as Map<String, dynamic>;
        } catch (_) {}
      }

      // Map backend agent identifier to UI agent ID
      final targetAgentId = _mapAgentId(agentName);

      if (event == 'agent_start' && targetAgentId != null) {
        agents = agents.map((a) {
          if (a.id == targetAgentId) {
            final msg = data['message'] as String? ?? 'Executing analysis...';
            return a.copyWith(
              state: AgentState.working,
              currentActivity: msg,
              progress: 0.5,
            );
          }
          return a;
        }).toList();
      } else if (event == 'agent_done' && targetAgentId != null) {
        agents = agents.map((a) {
          if (a.id == targetAgentId) {
            final summary = data['preview'] as String? ??
                data['approach'] as String? ??
                data['reason'] as String? ??
                data['message'] as String? ??
                'Analysis completed';
            return a.copyWith(
              state: AgentState.completed,
              currentActivity: 'Completed successfully',
              outputSummary: summary,
              progress: 1.0,
            );
          }
          return a;
        }).toList();
      } else if (event == 'disagreement') {
        // System-level event from Critic
        final reason = data['reason'] as String? ?? 'Disagreement flagged during audit';
        agents = agents.map((a) {
          if (a.id == 'agent_critic') {
            return a.copyWith(
              state: AgentState.working,
              currentActivity: 'Disagreement: $reason',
              outputSummary: 'Revision requested: $reason',
            );
          }
          return a;
        }).toList();
      } else if (event == 'revision_start') {
        final reason = data['reason'] as String? ?? 'Revising solution proposal';
        agents = agents.map((a) {
          if (a.id == 'agent_planner' || a.id == 'agent_synthesizer') {
            return a.copyWith(
              state: AgentState.working,
              currentActivity: 'Revision cycle: $reason',
            );
          }
          return a;
        }).toList();
      } else if (event == 'final_answer') {
        final answer = update.finalAnswer ?? data['content'] as String? ?? data['preview'] as String?;
        if (answer != null) {
          _finalAnswersByRoom[roomId] = answer;
        }
        agents = agents.map((a) {
          if (a.id == 'agent_synthesizer') {
            return a.copyWith(
              state: AgentState.completed,
              currentActivity: 'Final architectural synthesis ready',
              progress: 1.0,
            );
          }
          return a;
        }).toList();
      } else if (event == 'workflow_completed') {
        final answer = update.finalAnswer ?? data['final_answer'] as String?;
        if (answer != null) {
          _finalAnswersByRoom[roomId] = answer;
        }
        // Mark all agents completed
        agents = agents.map((a) {
          return a.copyWith(
            state: AgentState.completed,
            progress: 1.0,
          );
        }).toList();
      } else if (event == 'workflow_failed' || update.status == 'failed') {
        final err = update.error ?? 'Task workflow failed';
        agents = agents.map((a) {
          if (a.state == AgentState.working) {
            return a.copyWith(
              state: AgentState.failed,
              currentActivity: err,
            );
          }
          return a;
        }).toList();
      } else if (event == 'cancelled' || update.status == 'cancelled') {
        agents = agents.map((a) {
          if (a.state == AgentState.working) {
            return a.copyWith(
              state: AgentState.failed,
              currentActivity: 'Workflow was cancelled by user',
            );
          }
          return a;
        }).toList();
      }

      yield List.unmodifiable(agents);
    }
  }

  @override
  Future<String?> getFinalAnswer({required int roomId, int? taskId}) async {
    if (_finalAnswersByRoom.containsKey(roomId)) {
      return _finalAnswersByRoom[roomId];
    }

    try {
      final sp.SharedTask? task = taskId != null
          ? await _client.task.getTask(taskId)
          : await _client.task.getActiveTask(roomId);
      if (task?.finalAnswer != null && task!.finalAnswer!.isNotEmpty) {
        _finalAnswersByRoom[roomId] = task.finalAnswer!;
        return task.finalAnswer;
      }
    } catch (_) {}

    return null;
  }

  String? _mapAgentId(String? rawAgent) {
    if (rawAgent == null) return null;
    switch (rawAgent.toLowerCase().trim()) {
      case 'planner':
        return 'agent_planner';
      case 'researcher':
        return 'agent_researcher';
      case 'analyst':
        return 'agent_technical_analyst';
      case 'critic':
        return 'agent_critic';
      case 'synthesizer':
        return 'agent_synthesizer';
      default:
        return null;
    }
  }
}
