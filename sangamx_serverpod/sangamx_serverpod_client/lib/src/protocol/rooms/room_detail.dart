/* AUTOMATICALLY GENERATED CODE DO NOT MODIFY */
/*   To generate run: "serverpod generate"    */

// ignore_for_file: implementation_imports
// ignore_for_file: library_private_types_in_public_api
// ignore_for_file: non_constant_identifier_names
// ignore_for_file: public_member_api_docs
// ignore_for_file: type_literal_in_constant_pattern
// ignore_for_file: use_super_parameters
// ignore_for_file: invalid_use_of_internal_member

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:sangamx_serverpod_client/src/protocol/protocol.dart'
    as _ia0or7hc;
import 'package:serverpod_client/serverpod_client.dart' as _isc;
import '../rooms/room.dart' as _ij8xg2ak;
import '../rooms/room_participant.dart' as _i8tneuh6;
import '../tasks/shared_task.dart' as _imfubv9t;

abstract class RoomDetail
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  RoomDetail._({
    required this.room,
    required this.participants,
    this.activeTask,
  });

  factory RoomDetail({
    required _ij8xg2ak.Room room,
    required List<_i8tneuh6.RoomParticipant> participants,
    _imfubv9t.SharedTask? activeTask,
  }) = _RoomDetailImpl;

  factory RoomDetail.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomDetail(
      room: _ia0or7hc.Protocol().deserialize<_ij8xg2ak.Room>(
        jsonSerialization['room'],
      ),
      participants: _ia0or7hc.Protocol()
          .deserialize<List<_i8tneuh6.RoomParticipant>>(
            jsonSerialization['participants'],
          ),
      activeTask: jsonSerialization['activeTask'] == null
          ? null
          : _ia0or7hc.Protocol().deserialize<_imfubv9t.SharedTask>(
              jsonSerialization['activeTask'],
            ),
    );
  }

  _ij8xg2ak.Room room;

  List<_i8tneuh6.RoomParticipant> participants;

  _imfubv9t.SharedTask? activeTask;

  /// Returns a shallow copy of this [RoomDetail]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  RoomDetail copyWith({
    _ij8xg2ak.Room? room,
    List<_i8tneuh6.RoomParticipant>? participants,
    _imfubv9t.SharedTask? activeTask = const _UndefinedRoomDetail$activeTask(),
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomDetail',
      'room': room.toJson(),
      'participants': participants.toJson(valueToJson: (v) => v.toJson()),
      if (activeTask != null) 'activeTask': activeTask?.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomDetail',
      'room': room.toJsonForProtocol(),
      'participants': participants.toJson(
        valueToJson: (v) => v.toJsonForProtocol(),
      ),
      if (activeTask != null) 'activeTask': activeTask?.toJsonForProtocol(),
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _UndefinedRoomDetail$activeTask extends _isc.UndefinedSentinel
    implements _imfubv9t.SharedTask {
  const _UndefinedRoomDetail$activeTask();
}

class _RoomDetailImpl extends RoomDetail {
  _RoomDetailImpl({
    required _ij8xg2ak.Room room,
    required List<_i8tneuh6.RoomParticipant> participants,
    _imfubv9t.SharedTask? activeTask,
  }) : super._(room: room, participants: participants, activeTask: activeTask);

  /// Returns a shallow copy of this [RoomDetail]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  RoomDetail copyWith({
    _ij8xg2ak.Room? room,
    List<_i8tneuh6.RoomParticipant>? participants,
    _imfubv9t.SharedTask? activeTask = const _UndefinedRoomDetail$activeTask(),
  }) {
    return RoomDetail(
      room: room ?? this.room.copyWith(),
      participants:
          participants ?? this.participants.map((e0) => e0.copyWith()).toList(),
      activeTask: activeTask is _isc.UndefinedSentinel
          ? this.activeTask?.copyWith()
          : activeTask,
    );
  }
}
