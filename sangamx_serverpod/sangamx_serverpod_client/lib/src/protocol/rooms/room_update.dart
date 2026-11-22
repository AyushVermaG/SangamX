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
import '../rooms/room_participant.dart' as _i8tneuh6;

abstract class RoomUpdate
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  RoomUpdate._({
    required this.roomId,
    required this.updateType,
    this.participant,
    required this.timestamp,
  });

  factory RoomUpdate({
    required int roomId,
    required String updateType,
    _i8tneuh6.RoomParticipant? participant,
    required DateTime timestamp,
  }) = _RoomUpdateImpl;

  factory RoomUpdate.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomUpdate(
      roomId: jsonSerialization['roomId'] as int,
      updateType: jsonSerialization['updateType'] as String,
      participant: jsonSerialization['participant'] == null
          ? null
          : _ia0or7hc.Protocol().deserialize<_i8tneuh6.RoomParticipant>(
              jsonSerialization['participant'],
            ),
      timestamp: _isc.DateTimeJsonExtension.fromJson(
        jsonSerialization['timestamp'],
      ),
    );
  }

  int roomId;

  String updateType;

  _i8tneuh6.RoomParticipant? participant;

  DateTime timestamp;

  /// Returns a shallow copy of this [RoomUpdate]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  RoomUpdate copyWith({
    int? roomId,
    String? updateType,
    _i8tneuh6.RoomParticipant? participant =
        const _UndefinedRoomUpdate$participant(),
    DateTime? timestamp,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomUpdate',
      'roomId': roomId,
      'updateType': updateType,
      if (participant != null) 'participant': participant?.toJson(),
      'timestamp': timestamp.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomUpdate',
      'roomId': roomId,
      'updateType': updateType,
      if (participant != null) 'participant': participant?.toJsonForProtocol(),
      'timestamp': timestamp.toJson(),
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _UndefinedRoomUpdate$participant extends _isc.UndefinedSentinel
    implements _i8tneuh6.RoomParticipant {
  const _UndefinedRoomUpdate$participant();
}

class _RoomUpdateImpl extends RoomUpdate {
  _RoomUpdateImpl({
    required int roomId,
    required String updateType,
    _i8tneuh6.RoomParticipant? participant,
    required DateTime timestamp,
  }) : super._(
         roomId: roomId,
         updateType: updateType,
         participant: participant,
         timestamp: timestamp,
       );

  /// Returns a shallow copy of this [RoomUpdate]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  RoomUpdate copyWith({
    int? roomId,
    String? updateType,
    _i8tneuh6.RoomParticipant? participant =
        const _UndefinedRoomUpdate$participant(),
    DateTime? timestamp,
  }) {
    return RoomUpdate(
      roomId: roomId ?? this.roomId,
      updateType: updateType ?? this.updateType,
      participant: participant is _isc.UndefinedSentinel
          ? this.participant?.copyWith()
          : participant,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}
