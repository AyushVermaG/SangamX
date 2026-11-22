import 'dart:math';
import 'package:serverpod/serverpod.dart';
import '../generated/protocol.dart';

String _generateRoomCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  final random = Random();
  return List.generate(6, (_) => chars[random.nextInt(chars.length)]).join();
}

class RoomEndpoint extends Endpoint {
  /// Create a new collaborative room with a unique room code.
  Future<Room> createRoom(Session session, String name) async {
    final now = DateTime.now().toUtc();
    String code = _generateRoomCode();

    // Ensure unique room code
    for (int i = 0; i < 5; i++) {
      final existing = await Room.db.findFirstRow(
        session,
        where: (t) => t.roomCode.equals(code),
      );
      if (existing == null) break;
      code = _generateRoomCode();
    }

    final room = Room(
      name: name,
      roomCode: code,
      createdAt: now,
      isActive: true,
    );

    return await Room.db.insertRow(session, room);
  }

  /// Join an existing room by its room code.
  Future<RoomDetail> joinRoom(
    Session session,
    String roomCode,
    String participantName,
  ) async {
    final room = await Room.db.findFirstRow(
      session,
      where: (t) => t.roomCode.equals(roomCode) & t.isActive.equals(true),
    );

    if (room == null || room.id == null) {
      throw FormatException('Room not found or inactive: $roomCode');
    }

    final now = DateTime.now().toUtc();

    // Check if participant already exists in room
    var participant = await RoomParticipant.db.findFirstRow(
      session,
      where: (t) =>
          t.roomId.equals(room.id!) & t.participantName.equals(participantName),
    );

    if (participant == null) {
      participant = await RoomParticipant.db.insertRow(
        session,
        RoomParticipant(
          roomId: room.id!,
          participantName: participantName,
          joinedAt: now,
          isOnline: true,
        ),
      );
    } else {
      participant.isOnline = true;
      participant = await RoomParticipant.db.updateRow(session, participant);
    }

    // Publish participant update to room stream
    final update = RoomUpdate(
      roomId: room.id!,
      updateType: 'participant_joined',
      participant: participant,
      timestamp: now,
    );
    await session.messages.postMessage(
      'room_${room.id}',
      update,
      scope: MessageScope.auto,
    );

    // Retrieve all participants
    final participants = await RoomParticipant.db.find(
      session,
      where: (t) => t.roomId.equals(room.id!),
      orderBy: (t) => t.joinedAt,
    );

    final activeTask = await SharedTask.db.findFirstRow(
      session,
      where: (t) =>
          t.roomId.equals(room.id!) &
          (t.status.equals('queued') | t.status.equals('running')),
    );

    return RoomDetail(
      room: room,
      participants: participants,
      activeTask: activeTask,
    );
  }

  /// Retrieve room details and participant list by room ID.
  Future<RoomDetail> getRoom(Session session, int roomId) async {
    final room = await Room.db.findById(session, roomId);
    if (room == null) {
      throw FormatException('Room not found: $roomId');
    }

    final participants = await RoomParticipant.db.find(
      session,
      where: (t) => t.roomId.equals(roomId),
      orderBy: (t) => t.joinedAt,
    );

    final activeTask = await SharedTask.db.findFirstRow(
      session,
      where: (t) =>
          t.roomId.equals(roomId) &
          (t.status.equals('queued') | t.status.equals('running')),
    );

    return RoomDetail(
      room: room,
      participants: participants,
      activeTask: activeTask,
    );
  }

  /// Real-time stream of room events (e.g. participant joins/leaves, task updates).
  Stream<RoomUpdate> watchRoom(Session session, int roomId) async* {
    yield* session.messages.createStream<RoomUpdate>('room_$roomId');
  }
}
