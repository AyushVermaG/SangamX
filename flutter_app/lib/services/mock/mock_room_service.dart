import 'dart:async';
import 'dart:math';
import '../../models/room.dart';
import '../../models/participant.dart';
import '../room_service.dart';

class MockRoomService implements RoomService {
  static final MockRoomService _instance = MockRoomService._internal();
  factory MockRoomService() => _instance;
  MockRoomService._internal();

  final Map<String, Room> _roomsByCode = {
    'SANGAM-7429': Room(
      id: 7429,
      code: 'SANGAM-7429',
      name: 'SangamX Alpha Collab',
      status: RoomStatus.waiting,
      createdAt: DateTime.now().subtract(const Duration(minutes: 10)),
      participants: const [
        Participant(id: '1', name: 'Alex Johnson', role: 'Architect', isHost: true),
        Participant(id: '2', name: 'Priya Sharma', role: 'ML Researcher'),
        Participant(id: '3', name: 'Marcus Vance', role: 'Systems Engineer'),
      ],
      isDemo: true,
    ),
    'DEMO-2026': Room(
      id: 2026,
      code: 'DEMO-2026',
      name: 'Hackathon War Room',
      status: RoomStatus.waiting,
      createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
      participants: const [
        Participant(id: '10', name: 'Elena Rostova', role: 'Product Lead', isHost: true),
        Participant(id: '11', name: 'Devon Miles', role: 'Full Stack Dev'),
      ],
      isDemo: true,
    ),
  };

  final _roomControllers = <int, StreamController<Room>>{};

  StreamController<Room> _getController(int roomId) {
    return _roomControllers.putIfAbsent(roomId, () => StreamController<Room>.broadcast());
  }

  @override
  Future<Room> createRoom({required String name, required String hostName}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final rand = Random().nextInt(9000) + 1000;
    final code = 'SANGAM-$rand';
    final host = Participant(
      id: 'host_${DateTime.now().millisecondsSinceEpoch}',
      name: hostName.trim().isEmpty ? 'Host User' : hostName.trim(),
      role: 'Room Owner',
      isHost: true,
      isCurrentUser: true,
    );

    final newRoom = Room(
      id: rand,
      code: code,
      name: name.trim().isEmpty ? 'Room $code' : name.trim(),
      status: RoomStatus.waiting,
      createdAt: DateTime.now(),
      participants: [
        host,
        const Participant(id: 'm1', name: 'Alex Johnson', role: 'Architect'),
        const Participant(id: 'm2', name: 'Priya Sharma', role: 'ML Researcher'),
      ],
      isDemo: true,
    );
    _roomsByCode[code] = newRoom;
    _getController(rand).add(newRoom);
    return newRoom;
  }

  @override
  Future<Room> getRoom(int roomId) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final room = _roomsByCode.values.firstWhere(
      (r) => r.id == roomId,
      orElse: () => _roomsByCode.values.first,
    );
    return room;
  }

  @override
  Future<Room> joinRoom({required String code, required String participantName}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final normalized = code.trim().toUpperCase();
    if (!_roomsByCode.containsKey(normalized)) {
      throw Exception("Room '$code' does not exist. Available demo rooms: 'SANGAM-7429' or 'DEMO-2026'");
    }

    final room = _roomsByCode[normalized]!;
    final user = Participant(
      id: 'user_${DateTime.now().millisecondsSinceEpoch}',
      name: participantName.trim().isEmpty ? 'Guest User' : participantName.trim(),
      role: 'Collaborator',
      isCurrentUser: true,
    );

    final updated = room.copyWith(
      participants: [...room.participants, user],
    );
    _roomsByCode[normalized] = updated;
    if (updated.id != null) {
      _getController(updated.id!).add(updated);
    }
    return updated;
  }

  @override
  Stream<Room> watchRoom(int roomId) async* {
    yield await getRoom(roomId);
    yield* _getController(roomId).stream;
  }

  /// Helper for submitting problem in mock mode
  Future<Room> submitProblem({required String roomCode, required String problemStatement}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final normalized = roomCode.trim().toUpperCase();
    final room = _roomsByCode[normalized] ?? _roomsByCode.values.first;
    final updated = room.copyWith(
      currentProblem: problemStatement,
      status: RoomStatus.analyzing,
      activeTaskId: Random().nextInt(8000) + 1000,
    );
    _roomsByCode[normalized] = updated;
    if (updated.id != null) {
      _getController(updated.id!).add(updated);
    }
    return updated;
  }
}
