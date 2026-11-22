import 'package:test/test.dart';
import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart';

void main() {
  test('verify sangamx_serverpod_client exports and instantiates Client', () {
    final client = Client('http://localhost:8080/');

    expect(client, isNotNull);
    expect(client.room, isNotNull);
    expect(client.task, isNotNull);
    expect(client.greeting, isNotNull);

    // Verify room models
    final now = DateTime.now().toUtc();
    final room = Room(
      id: 1,
      name: 'Test Room',
      roomCode: 'ABC123',
      createdAt: now,
      isActive: true,
    );
    expect(room.roomCode, equals('ABC123'));

    final participant = RoomParticipant(
      id: 10,
      roomId: 1,
      participantName: 'Alice',
      joinedAt: now,
      isOnline: true,
    );
    expect(participant.participantName, equals('Alice'));

    final roomDetail = RoomDetail(
      room: room,
      participants: [participant],
    );
    expect(roomDetail.participants.length, equals(1));

    // Verify task models
    final task = SharedTask(
      id: 100,
      roomId: 1,
      query: 'Test query',
      status: 'queued',
      createdAt: now,
    );
    expect(task.status, equals('queued'));

    final update = TaskUpdate(
      taskId: 100,
      roomId: 1,
      status: 'running',
      event: 'agent_start',
      agent: 'planner',
      timestamp: now,
    );
    expect(update.agent, equals('planner'));
  });
}
