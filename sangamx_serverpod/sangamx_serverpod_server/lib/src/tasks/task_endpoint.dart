import 'dart:async';
import 'package:serverpod/serverpod.dart';
import '../generated/protocol.dart';
import 'fastapi_bridge_service.dart';

class TaskEndpoint extends Endpoint {
  static FastApiBridgeService? mockBridgeService;

  FastApiBridgeService get bridgeService =>
      mockBridgeService ?? _bridgeService;
  final FastApiBridgeService _bridgeService;

  TaskEndpoint({FastApiBridgeService? bridgeService})
      : _bridgeService = bridgeService ?? FastApiBridgeService();

  /// Submit a query to be processed by the 5-agent LangGraph workflow.
  /// Enforces single active task per room to prevent duplicate execution.
  Future<SharedTask> submitTask(
    Session session,
    int roomId,
    String query,
  ) async {
    // 1. Verify room exists and is active
    final room = await Room.db.findById(session, roomId);
    if (room == null || !room.isActive) {
      throw FormatException('Room not found or inactive: $roomId');
    }

    final trimmedQuery = query.trim();
    if (trimmedQuery.isEmpty) {
      throw FormatException('Query cannot be empty');
    }

    // 2. Prevent duplicate / concurrent workflow execution within a database transaction
    final task = await session.db.transaction<SharedTask>((transaction) async {
      final existingActive = await SharedTask.db.findFirstRow(
        session,
        where: (t) =>
            t.roomId.equals(roomId) &
            (t.status.equals('queued') | t.status.equals('running')),
        transaction: transaction,
      );
      if (existingActive != null) {
        throw FormatException(
          'A task is already running in room $roomId (Task #${existingActive.id}).',
        );
      }

      // 3. Persist new task in queued status
      final now = DateTime.now().toUtc();
      return await SharedTask.db.insertRow(
        session,
        SharedTask(
          roomId: roomId,
          query: trimmedQuery,
          status: 'queued',
          createdAt: now,
        ),
        transaction: transaction,
      );
    });

    // 4. Trigger FastAPI workflow exactly once in background
    unawaited(
      bridgeService.execute(
        serverpod: session.serverpod,
        sharedTaskId: task.id!,
        roomId: roomId,
        query: trimmedQuery,
      ),
    );

    return task;
  }

  /// Get details and final answer for a specific task.
  Future<SharedTask?> getTask(Session session, int taskId) async {
    return await SharedTask.db.findById(session, taskId);
  }

  /// Get currently active (queued/running) task for a room.
  Future<SharedTask?> getActiveTask(Session session, int roomId) async {
    return await SharedTask.db.findFirstRow(
      session,
      where: (t) =>
          t.roomId.equals(roomId) &
          (t.status.equals('queued') | t.status.equals('running')),
    );
  }

  /// Real-time stream of task updates (agent progress, final answer, status).
  Stream<TaskUpdate> watchTask(Session session, int roomId) async* {
    final room = await Room.db.findById(session, roomId);
    if (room == null || !room.isActive) {
      throw FormatException('Room not found or inactive: $roomId');
    }
    yield* session.messages.createStream<TaskUpdate>('task_$roomId');
  }
}
