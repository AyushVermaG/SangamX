import 'dart:math';
import '../../models/room.dart';
import '../../models/participant.dart';
import '../room_service.dart';

class MockRoomService implements RoomService {
  static final MockRoomService _instance = MockRoomService._internal();
  factory MockRoomService() => _instance;
  MockRoomService._internal();

  final Map<String, Room> _rooms = {
    'SANGAM-7429': Room(
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

  @override
  List<Participant> getDemoParticipants() {
    return const [
      Participant(id: 'p1', name: 'Aarav Patel', role: 'AI Strategist'),
      Participant(id: 'p2', name: 'Sarah Connor', role: 'Security Lead'),
      Participant(id: 'p3', name: 'Kenji Sato', role: 'Cloud Architect'),
    ];
  }

  @override
  Future<Room> createRoom({required String hostName}) async {
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
      code: code,
      name: 'Room $code',
      status: RoomStatus.waiting,
      createdAt: DateTime.now(),
      participants: [
        host,
        const Participant(id: 'm1', name: 'Alex Johnson', role: 'Architect'),
        const Participant(id: 'm2', name: 'Priya Sharma', role: 'ML Researcher'),
      ],
      isDemo: true,
    );
    _rooms[code] = newRoom;
    return newRoom;
  }

  @override
  Future<Room> getRoom(String code) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final normalized = code.trim().toUpperCase();
    if (_rooms.containsKey(normalized)) {
      return _rooms[normalized]!;
    }
    throw Exception("Room code '$code' not found. Available demo codes: 'SANGAM-7429', 'DEMO-2026'");
  }

  @override
  Future<Room> joinRoom({required String code, required String participantName}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final normalized = code.trim().toUpperCase();
    if (!_rooms.containsKey(normalized)) {
      throw Exception("Room '$code' does not exist. Available demo rooms: 'SANGAM-7429' or 'DEMO-2026'");
    }

    final room = _rooms[normalized]!;
    final user = Participant(
      id: 'user_${DateTime.now().millisecondsSinceEpoch}',
      name: participantName.trim().isEmpty ? 'Guest User' : participantName.trim(),
      role: 'Collaborator',
      isCurrentUser: true,
    );

    final updated = room.copyWith(
      participants: [...room.participants, user],
    );
    _rooms[normalized] = updated;
    return updated;
  }

  @override
  Future<Room> submitProblem({required String roomCode, required String problemStatement}) async {
    await Future.delayed(const Duration(milliseconds: 400));
    final normalized = roomCode.trim().toUpperCase();
    final room = _rooms[normalized] ?? await getRoom(normalized);
    final updated = room.copyWith(
      currentProblem: problemStatement,
      status: RoomStatus.analyzing,
    );
    _rooms[normalized] = updated;
    return updated;
  }
}
