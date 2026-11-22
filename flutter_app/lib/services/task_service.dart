class TaskSubmissionResult {
  final int id;
  final int roomId;
  final String query;
  final String status;
  final String? finalAnswer;
  final String? error;

  const TaskSubmissionResult({
    required this.id,
    required this.roomId,
    required this.query,
    required this.status,
    this.finalAnswer,
    this.error,
  });
}

abstract class TaskService {
  /// Submits a new shared task for [roomId] with research [query].
  Future<TaskSubmissionResult> submitTask({required int roomId, required String query});

  /// Retrieves task details by [taskId].
  Future<TaskSubmissionResult?> getTask(int taskId);

  /// Retrieves active task for [roomId] if queued or running.
  Future<TaskSubmissionResult?> getActiveTask(int roomId);
}
