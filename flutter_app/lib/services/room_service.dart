import '../models/room.dart';
import '../models/participant.dart';

abstract class RoomService {
  Future<Room> createRoom({required String hostName});
  Future<Room> getRoom(String code);
  Future<Room> joinRoom({required String code, required String participantName});
  Future<Room> submitProblem({required String roomCode, required String problemStatement});
  List<Participant> getDemoParticipants();
}
