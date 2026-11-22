import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart' as sp;
import '../task_service.dart';
import 'serverpod_client_provider.dart';

class ServerpodTaskService implements TaskService {
  final sp.Client _client;

  ServerpodTaskService({sp.Client? client})
      : _client = client ?? ServerpodClientProvider.getClient();

  @override
  Future<TaskSubmissionResult> submitTask({required int roomId, required String query}) async {
    final sp.SharedTask task = await _client.task.submitTask(roomId, query);
    return TaskSubmissionResult(
      id: task.id ?? 0,
      roomId: task.roomId,
      query: task.query,
      status: task.status,
      finalAnswer: task.finalAnswer,
      error: task.error,
    );
  }

  @override
  Future<TaskSubmissionResult?> getTask(int taskId) async {
    final sp.SharedTask? task = await _client.task.getTask(taskId);
    if (task == null) return null;
    return TaskSubmissionResult(
      id: task.id ?? taskId,
      roomId: task.roomId,
      query: task.query,
      status: task.status,
      finalAnswer: task.finalAnswer,
      error: task.error,
    );
  }

  @override
  Future<TaskSubmissionResult?> getActiveTask(int roomId) async {
    final sp.SharedTask? task = await _client.task.getActiveTask(roomId);
    if (task == null) return null;
    return TaskSubmissionResult(
      id: task.id ?? 0,
      roomId: task.roomId,
      query: task.query,
      status: task.status,
      finalAnswer: task.finalAnswer,
      error: task.error,
    );
  }
}
