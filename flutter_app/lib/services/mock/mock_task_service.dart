import 'dart:math';
import '../task_service.dart';

class MockTaskService implements TaskService {
  static final MockTaskService _instance = MockTaskService._internal();
  factory MockTaskService() => _instance;
  MockTaskService._internal();

  final Map<int, TaskSubmissionResult> _tasks = {};

  @override
  Future<TaskSubmissionResult> submitTask({required int roomId, required String query}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final id = Random().nextInt(9000) + 1000;
    final task = TaskSubmissionResult(
      id: id,
      roomId: roomId,
      query: query,
      status: 'queued',
    );
    _tasks[id] = task;
    return task;
  }

  @override
  Future<TaskSubmissionResult?> getTask(int taskId) async {
    await Future.delayed(const Duration(milliseconds: 200));
    return _tasks[taskId];
  }

  @override
  Future<TaskSubmissionResult?> getActiveTask(int roomId) async {
    await Future.delayed(const Duration(milliseconds: 200));
    return _tasks.values.firstWhere(
      (t) => t.roomId == roomId && (t.status == 'queued' || t.status == 'running'),
      orElse: () => TaskSubmissionResult(
        id: 1,
        roomId: roomId,
        query: 'Sample Active Task',
        status: 'running',
      ),
    );
  }
}
