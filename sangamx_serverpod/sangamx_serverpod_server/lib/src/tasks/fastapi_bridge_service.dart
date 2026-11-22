import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:serverpod/serverpod.dart';
import '../generated/protocol.dart';

class FastApiBridgeService {
  final http.Client _client;
  final String _baseUrl;

  FastApiBridgeService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = (baseUrl ??
                Platform.environment['FASTAPI_BASE_URL'] ??
                'http://127.0.0.1:8000')
            .replaceAll(RegExp(r'/+$'), '');

  /// Execute workflow bridge in background:
  /// 1. Submits query to FastAPI POST /api/v1/engine/run
  /// 2. Consumes FastAPI SSE stream GET /api/v1/engine/stream/{task_id}
  /// 3. Broadcasts intermediate agent progress and terminal events via Message Central
  /// 4. Updates SharedTask in PostgreSQL
  Future<void> execute({
    required Serverpod serverpod,
    required int sharedTaskId,
    required int roomId,
    required String query,
  }) async {
    final session = await serverpod.createSession();

    try {
      // 1. Submit query to FastAPI with mapped session_id
      final runUri = Uri.parse('$_baseUrl/api/v1/engine/run');
      final runResponse = await _client
          .post(
            runUri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'query': query,
              'session_id': 'room_$roomId',
            }),
          )
          .timeout(const Duration(seconds: 15));

      if (runResponse.statusCode != 200) {
        throw FormatException(
          'FastAPI engine rejected task (${runResponse.statusCode}): ${runResponse.body}',
        );
      }

      final runJson = jsonDecode(runResponse.body) as Map<String, dynamic>;
      final fastapiTaskId = runJson['task_id'] as String;

      // 2. Update task with fastapiTaskId and status 'running'
      final task = await SharedTask.db.findById(session, sharedTaskId);
      if (task == null) return;

      task.fastapiTaskId = fastapiTaskId;
      task.status = 'running';
      await SharedTask.db.updateRow(session, task);

      await session.messages.postMessage(
        'task_$roomId',
        TaskUpdate(
          taskId: sharedTaskId,
          roomId: roomId,
          status: 'running',
          event: 'task_started',
          timestamp: DateTime.now().toUtc(),
        ),
        scope: MessageScope.auto,
      );

      // 3. Connect to FastAPI SSE stream
      final streamUri =
          Uri.parse('$_baseUrl/api/v1/engine/stream/$fastapiTaskId');
      final request = http.Request('GET', streamUri)
        ..headers['Accept'] = 'text/event-stream';

      final response =
          await _client.send(request).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw FormatException(
          'Failed to open SSE stream (${response.statusCode})',
        );
      }

      // 4. Stream consumption
      final lineStream = response.stream
          .transform(utf8.decoder)
          .transform(const LineSplitter());

      await for (final line in lineStream) {
        if (!line.startsWith('data: ')) continue;
        final rawData = line.substring(6).trim();
        if (rawData.isEmpty) continue;

        Map<String, dynamic> eventPayload;
        try {
          eventPayload = jsonDecode(rawData) as Map<String, dynamic>;
        } catch (_) {
          continue;
        }

        final eventName = eventPayload['event'] as String? ?? 'message';
        final agent = eventPayload['agent'] as String?;
        final dataMap = eventPayload['data'] as Map<String, dynamic>? ?? {};
        final now = DateTime.now().toUtc();

        if (eventName == 'workflow_completed') {
          final answer = dataMap['final_answer']?.toString() ?? '';
          final current = await SharedTask.db.findById(session, sharedTaskId);
          if (current != null) {
            current.status = 'completed';
            current.finalAnswer = answer;
            current.completedAt = now;
            await SharedTask.db.updateRow(session, current);
          }

          await session.messages.postMessage(
            'task_$roomId',
            TaskUpdate(
              taskId: sharedTaskId,
              roomId: roomId,
              status: 'completed',
              event: eventName,
              agent: agent,
              data: jsonEncode(dataMap),
              finalAnswer: answer,
              timestamp: now,
            ),
            scope: MessageScope.auto,
          );
          break;
        } else if (eventName == 'workflow_failed') {
          final errStr = dataMap['error']?.toString() ?? 'Workflow failed';
          final current = await SharedTask.db.findById(session, sharedTaskId);
          if (current != null) {
            current.status = 'failed';
            current.error = errStr;
            current.completedAt = now;
            await SharedTask.db.updateRow(session, current);
          }

          await session.messages.postMessage(
            'task_$roomId',
            TaskUpdate(
              taskId: sharedTaskId,
              roomId: roomId,
              status: 'failed',
              event: eventName,
              agent: agent,
              data: jsonEncode(dataMap),
              error: errStr,
              timestamp: now,
            ),
            scope: MessageScope.auto,
          );
          break;
        } else if (eventName == 'cancelled') {
          final current = await SharedTask.db.findById(session, sharedTaskId);
          if (current != null) {
            current.status = 'cancelled';
            current.completedAt = now;
            await SharedTask.db.updateRow(session, current);
          }

          await session.messages.postMessage(
            'task_$roomId',
            TaskUpdate(
              taskId: sharedTaskId,
              roomId: roomId,
              status: 'cancelled',
              event: eventName,
              agent: agent,
              timestamp: now,
            ),
            scope: MessageScope.auto,
          );
          break;
        } else {
          // Progress event: agent_start, agent_done, disagreement, final_answer, etc.
          await session.messages.postMessage(
            'task_$roomId',
            TaskUpdate(
              taskId: sharedTaskId,
              roomId: roomId,
              status: 'running',
              event: eventName,
              agent: agent,
              data: jsonEncode(dataMap),
              finalAnswer: eventName == 'final_answer'
                  ? dataMap['content']?.toString()
                  : null,
              timestamp: now,
            ),
            scope: MessageScope.auto,
          );
        }
      }

      // Verify task reached a terminal state; if stream disconnected prematurely, mark as failed
      final finalCheck = await SharedTask.db.findById(session, sharedTaskId);
      if (finalCheck != null &&
          finalCheck.status != 'completed' &&
          finalCheck.status != 'failed' &&
          finalCheck.status != 'cancelled') {
        final now = DateTime.now().toUtc();
        finalCheck.status = 'failed';
        finalCheck.error =
            'FastAPI SSE stream closed unexpectedly before workflow conclusion.';
        finalCheck.completedAt = now;
        await SharedTask.db.updateRow(session, finalCheck);

        await session.messages.postMessage(
          'task_$roomId',
          TaskUpdate(
            taskId: sharedTaskId,
            roomId: roomId,
            status: 'failed',
            event: 'workflow_failed',
            error: finalCheck.error,
            timestamp: now,
          ),
          scope: MessageScope.auto,
        );
      }
    } catch (err) {
      session.log('FastApiBridgeService error: $err', level: LogLevel.error);
      var task = await SharedTask.db.findById(session, sharedTaskId);
      if (task != null && task.status != 'completed') {
        final now = DateTime.now().toUtc();
        task.status = 'failed';
        task.error = err.toString();
        task.completedAt = now;
        await SharedTask.db.updateRow(session, task);

        await session.messages.postMessage(
          'task_$roomId',
          TaskUpdate(
            taskId: sharedTaskId,
            roomId: roomId,
            status: 'failed',
            event: 'workflow_failed',
            error: err.toString(),
            timestamp: now,
          ),
          scope: MessageScope.auto,
        );
      }
    } finally {
      await session.close();
    }
  }
}
