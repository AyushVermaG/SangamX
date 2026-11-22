import '../models/room.dart';

abstract class RoomService {
  /// Creates a new room with [name] and automatically joins as [hostName].
  Future<Room> createRoom({required String name, required String hostName});

  /// Retrieves a room's details by database [roomId] or code.
  Future<Room> getRoom(int roomId);

  /// Joins an existing room with 6-character [code] as [participantName].
  Future<Room> joinRoom({required String code, required String participantName});

  /// Subscribes to room updates (e.g. participant joins) for [roomId].
  Stream<Room> watchRoom(int roomId);
}
