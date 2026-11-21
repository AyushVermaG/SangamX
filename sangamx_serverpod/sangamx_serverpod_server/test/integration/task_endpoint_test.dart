import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:serverpod/serverpod.dart';
import 'package:sangamx_serverpod_server/src/generated/protocol.dart';
import 'package:sangamx_serverpod_server/src/tasks/fastapi_bridge_service.dart';
import 'package:sangamx_serverpod_server/src/tasks/task_endpoint.dart';
import 'package:test/test.dart';
import 'test_tools/serverpod_test_tools.dart';

void main() {
  withServerpod(
    'Given Task Endpoint',
    rollbackDatabase: RollbackDatabase.disabled,
    (sessionBuilder, endpoints) {
      late MockClient mockClient;

      setUp(() {
        mockClient = MockClient.streaming((request, bodyStream) async {
          if (request.method == 'POST' &&
              request.url.path.endsWith('/api/v1/engine/run')) {
            return http.StreamedResponse(
              Stream.value(
                utf8.encode(jsonEncode({'task_id': 'mock-fastapi-uuid-777'})),
              ),
              200,
              headers: {'content-type': 'application/json'},
            );
          }
          if (request.method == 'GET' &&
              request.url.path.contains('/api/v1/engine/stream/')) {
            final sseData = [
              'data: {"event": "agent_start", "agent": "PlannerAgent", "data": {}, "timestamp": "2026-11-22T00:00:00Z"}\n\n',
              'data: {"event": "final_answer", "agent": "SynthesisAgent", "data": {"content": "LangGraph offers cyclic graph control."}, "timestamp": "2026-11-22T00:00:01Z"}\n\n',
              'data: {"event": "workflow_completed", "agent": "SynthesisAgent", "data": {"final_answer": "LangGraph offers cyclic graph control."}, "timestamp": "2026-11-22T00:00:02Z"}\n\n',
            ].join();
            return http.StreamedResponse(
              Stream.value(utf8.encode(sseData)),
              200,
              headers: {'content-type': 'text/event-stream'},
            );
          }
          return http.StreamedResponse(Stream.value([]), 404);
        });

        TaskEndpoint.mockBridgeService = FastApiBridgeService(
          client: mockClient,
          baseUrl: 'http://127.0.0.1:8000',
        );
      });

      tearDown(() {
        TaskEndpoint.mockBridgeService = null;
      });

      test('submitTask creates task in queued status and retrieves it', () async {
        final room = await endpoints.room.createRoom(
          sessionBuilder,
          'Quantum Research Room',
        );
        expect(room.id, isNotNull);

        final task = await endpoints.task.submitTask(
          sessionBuilder,
          room.id!,
          'Explain quantum entanglement in simple terms',
        );

        expect(task.id, isNotNull);
        expect(task.roomId, equals(room.id));
        expect(task.query, equals('Explain quantum entanglement in simple terms'));

        // Retrieve task by id
        final retrieved = await endpoints.task.getTask(
          sessionBuilder,
          task.id!,
        );
        expect(retrieved, isNotNull);
        expect(retrieved!.id, equals(task.id));

        // Retrieve active task for room
        final activeTask = await endpoints.task.getActiveTask(
          sessionBuilder,
          room.id!,
        );
        expect(activeTask, isNotNull);
        expect(activeTask!.id, equals(task.id));
      });

      test('submitTask rejects empty query and duplicate active tasks', () async {
        final room = await endpoints.room.createRoom(
          sessionBuilder,
          'Concurrency Control Room',
        );

        // Empty query rejected
        expect(
          () => endpoints.task.submitTask(sessionBuilder, room.id!, '   '),
          throwsA(isA<FormatException>()),
        );

        // First task succeeds
        await endpoints.task.submitTask(
          sessionBuilder,
          room.id!,
          'First active task',
        );

        // Second task in same room rejected
        expect(
          () => endpoints.task.submitTask(
            sessionBuilder,
            room.id!,
            'Second conflicting task',
          ),
          throwsA(
            predicate((e) =>
                e is FormatException && e.message.contains('already running')),
          ),
        );
      });

      test('watchTask receives real-time task updates', () async {
        final room = await endpoints.room.createRoom(
          sessionBuilder,
          'Live Task Stream Room',
        );

        final stream = endpoints.task.watchTask(sessionBuilder, room.id!);

        final expectation = expectLater(
          stream,
          emits(
            predicate((dynamic update) {
              return update is TaskUpdate &&
                  update.status == 'running' &&
                  update.event == 'agent_start' &&
                  update.agent == 'PlannerAgent';
            }),
          ),
        );

        // Allow stream subscription to attach to Message Central
        await Future.delayed(const Duration(milliseconds: 100));

        final session = sessionBuilder.build();
        try {
          await session.messages.postMessage(
            'task_${room.id}',
            TaskUpdate(
              taskId: 1,
              roomId: room.id!,
              status: 'running',
              event: 'agent_start',
              agent: 'PlannerAgent',
              timestamp: DateTime.now().toUtc(),
            ),
            scope: MessageScope.auto,
          );
        } finally {
          await session.close();
        }

        await expectation;
      });

      test('FastApiBridgeService executes workflow and updates SharedTask',
          () async {
        final room = await endpoints.room.createRoom(
          sessionBuilder,
          'Bridge Execution Room',
        );

        final session = sessionBuilder.build();
        try {
          final task = await SharedTask.db.insertRow(
            session,
            SharedTask(
              roomId: room.id!,
              query: 'Compare LangGraph with AutoGen',
              status: 'queued',
              createdAt: DateTime.now().toUtc(),
            ),
          );

          final bridge = FastApiBridgeService(
            client: mockClient,
            baseUrl: 'http://127.0.0.1:8000',
          );

          await bridge.execute(
            serverpod: session.serverpod,
            sharedTaskId: task.id!,
            roomId: room.id!,
            query: task.query,
          );

          // Verify completed state in database
          final completedTask = await SharedTask.db.findById(session, task.id!);
          expect(completedTask, isNotNull);
          expect(completedTask!.status, equals('completed'));
          expect(completedTask.fastapiTaskId, equals('mock-fastapi-uuid-777'));
          expect(
            completedTask.finalAnswer,
            equals('LangGraph offers cyclic graph control.'),
          );
          expect(completedTask.completedAt, isNotNull);
        } finally {
          await session.close();
        }
      });

      test('watchTask rejects invalid or non-existent room', () async {
        final stream = endpoints.task.watchTask(sessionBuilder, 999999);
        expect(
          stream,
          emitsError(isA<FormatException>()),
        );
      });

      test('FastApiBridgeService handles abrupt stream disconnection safely',
          () async {
        final room = await endpoints.room.createRoom(
          sessionBuilder,
          'Disconnect Safety Room',
        );

        final session = sessionBuilder.build();
        try {
          final task = await SharedTask.db.insertRow(
            session,
            SharedTask(
              roomId: room.id!,
              query: 'Disconnect test query',
              status: 'queued',
              createdAt: DateTime.now().toUtc(),
            ),
          );

          // Mock client whose SSE stream closes abruptly without a terminal event
          final disconnectClient = MockClient.streaming((request, bodyStream) async {
            if (request.method == 'POST') {
              return http.StreamedResponse(
                Stream.value(utf8.encode(jsonEncode({'task_id': 'premature-close-uuid'}))),
                200,
                headers: {'content-type': 'application/json'},
              );
            }
            if (request.method == 'GET') {
              // Only emits an agent_start then immediately closes EOF
              final sseData = 'data: {"event": "agent_start", "agent": "PlannerAgent", "data": {}, "timestamp": "2026-11-22T00:00:00Z"}\n\n';
              return http.StreamedResponse(
                Stream.value(utf8.encode(sseData)),
                200,
                headers: {'content-type': 'text/event-stream'},
              );
            }
            return http.StreamedResponse(Stream.value([]), 404);
          });

          final bridge = FastApiBridgeService(
            client: disconnectClient,
            baseUrl: 'http://127.0.0.1:8000',
          );

          await bridge.execute(
            serverpod: session.serverpod,
            sharedTaskId: task.id!,
            roomId: room.id!,
            query: task.query,
          );

          // Task MUST NOT be left in 'running'; it must be marked 'failed'
          final failedTask = await SharedTask.db.findById(session, task.id!);
          expect(failedTask, isNotNull);
          expect(failedTask!.status, equals('failed'));
          expect(failedTask.error, contains('SSE stream closed unexpectedly'));
          expect(failedTask.completedAt, isNotNull);
        } finally {
          await session.close();
        }
      });

      test('watchTask delivers events to multiple concurrent room participants',
          () async {
        final room = await endpoints.room.createRoom(
          sessionBuilder,
          'Multi-Participant Broadcast Room',
        );

        final stream1 = endpoints.task.watchTask(sessionBuilder, room.id!);
        final stream2 = endpoints.task.watchTask(sessionBuilder, room.id!);

        final expectation1 = expectLater(
          stream1,
          emits(
            predicate((dynamic update) =>
                update is TaskUpdate && update.event == 'multi_broadcast_test'),
          ),
        );
        final expectation2 = expectLater(
          stream2,
          emits(
            predicate((dynamic update) =>
                update is TaskUpdate && update.event == 'multi_broadcast_test'),
          ),
        );

        await Future.delayed(const Duration(milliseconds: 100));

        final session = sessionBuilder.build();
        try {
          await session.messages.postMessage(
            'task_${room.id}',
            TaskUpdate(
              taskId: 42,
              roomId: room.id!,
              status: 'running',
              event: 'multi_broadcast_test',
              timestamp: DateTime.now().toUtc(),
            ),
            scope: MessageScope.auto,
          );
        } finally {
          await session.close();
        }

        await Future.wait([expectation1, expectation2]);
      });
    },
  );
}
