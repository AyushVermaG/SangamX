import 'dart:async';
import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart' as sp;
import '../../models/participant.dart';
import '../../models/room.dart';
import '../room_service.dart';
import 'serverpod_client_provider.dart';

class ServerpodRoomService implements RoomService {
  final sp.Client _client;

  ServerpodRoomService({sp.Client? client})
      : _client = client ?? ServerpodClientProvider.getClient();

  @override
  Future<Room> createRoom({required String name, required String hostName}) async {
    // 1. Create room on Serverpod backend
    final sp.Room createdRoom = await _client.room.createRoom(name);
    final roomCode = createdRoom.roomCode;

    // 2. Automatically join newly created room as creator/host
    final sp.RoomDetail detail = await _client.room.joinRoom(roomCode, hostName);

    // 3. Map RoomDetail to Flutter Room model
    return _mapRoomDetail(detail, currentUserName: hostName, isHostUser: true);
  }

  @override
  Future<Room> joinRoom({required String code, required String participantName}) async {
    final sp.RoomDetail detail = await _client.room.joinRoom(code.trim().toUpperCase(), participantName);
    return _mapRoomDetail(detail, currentUserName: participantName, isHostUser: false);
  }

  @override
  Future<Room> getRoom(int roomId) async {
    final sp.RoomDetail detail = await _client.room.getRoom(roomId);
    return _mapRoomDetail(detail);
  }

  @override
  Stream<Room> watchRoom(int roomId) async* {
    // Emit initial snapshot first
    Room current = await getRoom(roomId);
    yield current;

    // Listen to live Serverpod broadcast stream
    final stream = _client.room.watchRoom(roomId);
    await for (final sp.RoomUpdate update in stream) {
      if (update.updateType == 'participant_joined' && update.participant != null) {
        final p = update.participant!;
        final exists = current.participants.any((x) => x.id == p.id.toString());
        if (!exists) {
          final newParticipant = Participant(
            id: p.id?.toString() ?? p.participantName,
            name: p.participantName,
            role: 'Collaborator',
            isOnline: p.isOnline,
          );
          current = current.copyWith(
            participants: [...current.participants, newParticipant],
          );
          yield current;
        }
      } else {
        // Refresh full room detail on other update events
        current = await getRoom(roomId);
        yield current;
      }
    }
  }

  Room _mapRoomDetail(sp.RoomDetail detail, {String? currentUserName, bool? isHostUser}) {
    final r = detail.room;
    final List<Participant> participants = detail.participants.map((p) {
      final isCurrent = currentUserName != null && p.participantName == currentUserName;
      // First participant in list is conventionally creator/host if isHostUser specified
      final isFirst = detail.participants.isNotEmpty && detail.participants.first.id == p.id;
      final isHost = isHostUser == true ? isCurrent : isFirst;
      return Participant(
        id: p.id?.toString() ?? p.participantName,
        name: p.participantName,
        role: isHost ? 'Room Owner' : 'Collaborator',
        isHost: isHost,
        isCurrentUser: isCurrent,
        isOnline: p.isOnline,
      );
    }).toList();

    RoomStatus status = RoomStatus.waiting;
    if (detail.activeTask != null) {
      final taskStatus = detail.activeTask!.status;
      if (taskStatus == 'completed') {
        status = RoomStatus.completed;
      } else if (taskStatus == 'running') {
        status = RoomStatus.analyzing;
      } else if (taskStatus == 'queued') {
        status = RoomStatus.problemSubmitted;
      }
    }

    return Room(
      id: r.id,
      code: r.roomCode,
      name: r.name,
      status: status,
      participants: participants,
      currentProblem: detail.activeTask?.query,
      activeTaskId: detail.activeTask?.id,
      createdAt: r.createdAt,
      isDemo: false,
    );
  }
}
