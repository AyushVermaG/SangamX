import '../models/agent.dart';

abstract class AgentService {
  /// Returns the initial set of 5 agents (Planner, Researcher, Analyst, Critic, Synthesizer).
  List<AgentInfo> getInitialAgents();

  /// Subscribes to real-time agent updates for [roomId].
  /// In Serverpod mode, listens to `client.task.watchTask(roomId)`.
  /// In mock mode, runs the sequential state simulation.
  Stream<List<AgentInfo>> watchAgents({
    required int roomId,
    String? problemStatement,
    int? taskId,
  });

  /// Returns final synthesis / answer if available.
  Future<String?> getFinalAnswer({required int roomId, int? taskId});
}
