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

abstract class SharedTask
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  SharedTask._({
    this.id,
    required this.roomId,
    required this.query,
    required this.status,
    this.fastapiTaskId,
    this.finalAnswer,
    this.error,
    required this.createdAt,
    this.completedAt,
  });

  factory SharedTask({
    int? id,
    required int roomId,
    required String query,
    required String status,
    String? fastapiTaskId,
    String? finalAnswer,
    String? error,
    required DateTime createdAt,
    DateTime? completedAt,
  }) = _SharedTaskImpl;

  factory SharedTask.fromJson(Map<String, dynamic> jsonSerialization) {
    return SharedTask(
      id: jsonSerialization['id'] as int?,
      roomId: jsonSerialization['roomId'] as int,
      query: jsonSerialization['query'] as String,
      status: jsonSerialization['status'] as String,
      fastapiTaskId: jsonSerialization['fastapiTaskId'] as String?,
      finalAnswer: jsonSerialization['finalAnswer'] as String?,
      error: jsonSerialization['error'] as String?,
      createdAt: _isc.DateTimeJsonExtension.fromJson(
        jsonSerialization['createdAt'],
      ),
      completedAt: jsonSerialization['completedAt'] == null
          ? null
          : _isc.DateTimeJsonExtension.fromJson(
              jsonSerialization['completedAt'],
            ),
    );
  }

  /// The database id, set if the object has been inserted into the
  /// database or if it has been fetched from the database. Otherwise,
  /// the id will be null.
  int? id;

  int roomId;

  String query;

  String status;

  String? fastapiTaskId;

  String? finalAnswer;

  String? error;

  DateTime createdAt;

  DateTime? completedAt;

  /// Returns a shallow copy of this [SharedTask]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  SharedTask copyWith({
    int? id,
    int? roomId,
    String? query,
    String? status,
    String? fastapiTaskId,
    String? finalAnswer,
    String? error,
    DateTime? createdAt,
    DateTime? completedAt = const _isc.$UndefinedDateTime(),
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'SharedTask',
      if (id != null) 'id': id,
      'roomId': roomId,
      'query': query,
      'status': status,
      if (fastapiTaskId != null) 'fastapiTaskId': fastapiTaskId,
      if (finalAnswer != null) 'finalAnswer': finalAnswer,
      if (error != null) 'error': error,
      'createdAt': createdAt.toJson(),
      if (completedAt != null) 'completedAt': completedAt?.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'SharedTask',
      if (id != null) 'id': id,
      'roomId': roomId,
      'query': query,
      'status': status,
      if (fastapiTaskId != null) 'fastapiTaskId': fastapiTaskId,
      if (finalAnswer != null) 'finalAnswer': finalAnswer,
      if (error != null) 'error': error,
      'createdAt': createdAt.toJson(),
      if (completedAt != null) 'completedAt': completedAt?.toJson(),
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _SharedTaskImpl extends SharedTask {
  _SharedTaskImpl({
    int? id,
    required int roomId,
    required String query,
    required String status,
    String? fastapiTaskId,
    String? finalAnswer,
    String? error,
    required DateTime createdAt,
    DateTime? completedAt,
  }) : super._(
         id: id,
         roomId: roomId,
         query: query,
         status: status,
         fastapiTaskId: fastapiTaskId,
         finalAnswer: finalAnswer,
         error: error,
         createdAt: createdAt,
         completedAt: completedAt,
       );

  /// Returns a shallow copy of this [SharedTask]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  SharedTask copyWith({
    Object? id = _Undefined,
    int? roomId,
    String? query,
    String? status,
    Object? fastapiTaskId = _Undefined,
    Object? finalAnswer = _Undefined,
    Object? error = _Undefined,
    DateTime? createdAt,
    DateTime? completedAt = const _isc.$UndefinedDateTime(),
  }) {
    return SharedTask(
      id: id is int? ? id : this.id,
      roomId: roomId ?? this.roomId,
      query: query ?? this.query,
      status: status ?? this.status,
      fastapiTaskId: fastapiTaskId is String?
          ? fastapiTaskId
          : this.fastapiTaskId,
      finalAnswer: finalAnswer is String? ? finalAnswer : this.finalAnswer,
      error: error is String? ? error : this.error,
      createdAt: createdAt ?? this.createdAt,
      completedAt: completedAt is _isc.UndefinedSentinel
          ? this.completedAt
          : completedAt,
    );
  }
}
