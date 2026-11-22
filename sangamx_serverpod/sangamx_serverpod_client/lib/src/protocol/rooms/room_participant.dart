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
import 'package:serverpod_client/serverpod_client.dart' as _isc;

abstract class RoomParticipant
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  RoomParticipant._({
    this.id,
    required this.roomId,
    required this.participantName,
    required this.joinedAt,
    required this.isOnline,
  });

  factory RoomParticipant({
    int? id,
    required int roomId,
    required String participantName,
    required DateTime joinedAt,
    required bool isOnline,
  }) = _RoomParticipantImpl;

  factory RoomParticipant.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomParticipant(
      id: jsonSerialization['id'] as int?,
      roomId: jsonSerialization['roomId'] as int,
      participantName: jsonSerialization['participantName'] as String,
      joinedAt: _isc.DateTimeJsonExtension.fromJson(
        jsonSerialization['joinedAt'],
      ),
      isOnline: _isc.BoolJsonExtension.fromJson(jsonSerialization['isOnline']),
    );
  }

  /// The database id, set if the object has been inserted into the
  /// database or if it has been fetched from the database. Otherwise,
  /// the id will be null.
  int? id;

  int roomId;

  String participantName;

  DateTime joinedAt;

  bool isOnline;

  /// Returns a shallow copy of this [RoomParticipant]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  RoomParticipant copyWith({
    int? id,
    int? roomId,
    String? participantName,
    DateTime? joinedAt,
    bool? isOnline,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomParticipant',
      if (id != null) 'id': id,
      'roomId': roomId,
      'participantName': participantName,
      'joinedAt': joinedAt.toJson(),
      'isOnline': isOnline,
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomParticipant',
      if (id != null) 'id': id,
      'roomId': roomId,
      'participantName': participantName,
      'joinedAt': joinedAt.toJson(),
      'isOnline': isOnline,
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _RoomParticipantImpl extends RoomParticipant {
  _RoomParticipantImpl({
    int? id,
    required int roomId,
    required String participantName,
    required DateTime joinedAt,
    required bool isOnline,
  }) : super._(
         id: id,
         roomId: roomId,
         participantName: participantName,
         joinedAt: joinedAt,
         isOnline: isOnline,
       );

  /// Returns a shallow copy of this [RoomParticipant]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  RoomParticipant copyWith({
    Object? id = _Undefined,
    int? roomId,
    String? participantName,
    DateTime? joinedAt,
    bool? isOnline,
  }) {
    return RoomParticipant(
      id: id is int? ? id : this.id,
      roomId: roomId ?? this.roomId,
      participantName: participantName ?? this.participantName,
      joinedAt: joinedAt ?? this.joinedAt,
      isOnline: isOnline ?? this.isOnline,
    );
  }
}
