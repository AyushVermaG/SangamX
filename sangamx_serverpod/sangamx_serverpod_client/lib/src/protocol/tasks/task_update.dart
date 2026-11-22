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

abstract class TaskUpdate
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  TaskUpdate._({
    required this.taskId,
    required this.roomId,
    required this.status,
    this.event,
    this.agent,
    this.data,
    this.finalAnswer,
    this.error,
    required this.timestamp,
  });

  factory TaskUpdate({
    required int taskId,
    required int roomId,
    required String status,
    String? event,
    String? agent,
    String? data,
    String? finalAnswer,
    String? error,
    required DateTime timestamp,
  }) = _TaskUpdateImpl;

  factory TaskUpdate.fromJson(Map<String, dynamic> jsonSerialization) {
    return TaskUpdate(
      taskId: jsonSerialization['taskId'] as int,
      roomId: jsonSerialization['roomId'] as int,
      status: jsonSerialization['status'] as String,
      event: jsonSerialization['event'] as String?,
      agent: jsonSerialization['agent'] as String?,
      data: jsonSerialization['data'] as String?,
      finalAnswer: jsonSerialization['finalAnswer'] as String?,
      error: jsonSerialization['error'] as String?,
      timestamp: _isc.DateTimeJsonExtension.fromJson(
        jsonSerialization['timestamp'],
      ),
    );
  }

  int taskId;

  int roomId;

  String status;

  String? event;

  String? agent;

  String? data;

  String? finalAnswer;

  String? error;

  DateTime timestamp;

  /// Returns a shallow copy of this [TaskUpdate]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  TaskUpdate copyWith({
    int? taskId,
    int? roomId,
    String? status,
    String? event,
    String? agent,
    String? data,
    String? finalAnswer,
    String? error,
    DateTime? timestamp,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'TaskUpdate',
      'taskId': taskId,
      'roomId': roomId,
      'status': status,
      if (event != null) 'event': event,
      if (agent != null) 'agent': agent,
      if (data != null) 'data': data,
      if (finalAnswer != null) 'finalAnswer': finalAnswer,
      if (error != null) 'error': error,
      'timestamp': timestamp.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'TaskUpdate',
      'taskId': taskId,
      'roomId': roomId,
      'status': status,
      if (event != null) 'event': event,
      if (agent != null) 'agent': agent,
      if (data != null) 'data': data,
      if (finalAnswer != null) 'finalAnswer': finalAnswer,
      if (error != null) 'error': error,
      'timestamp': timestamp.toJson(),
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _TaskUpdateImpl extends TaskUpdate {
  _TaskUpdateImpl({
    required int taskId,
    required int roomId,
    required String status,
    String? event,
    String? agent,
    String? data,
    String? finalAnswer,
    String? error,
    required DateTime timestamp,
  }) : super._(
         taskId: taskId,
         roomId: roomId,
         status: status,
         event: event,
         agent: agent,
         data: data,
         finalAnswer: finalAnswer,
         error: error,
         timestamp: timestamp,
       );

  /// Returns a shallow copy of this [TaskUpdate]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  TaskUpdate copyWith({
    int? taskId,
    int? roomId,
    String? status,
    Object? event = _Undefined,
    Object? agent = _Undefined,
    Object? data = _Undefined,
    Object? finalAnswer = _Undefined,
    Object? error = _Undefined,
    DateTime? timestamp,
  }) {
    return TaskUpdate(
      taskId: taskId ?? this.taskId,
      roomId: roomId ?? this.roomId,
      status: status ?? this.status,
      event: event is String? ? event : this.event,
      agent: agent is String? ? agent : this.agent,
      data: data is String? ? data : this.data,
      finalAnswer: finalAnswer is String? ? finalAnswer : this.finalAnswer,
      error: error is String? ? error : this.error,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}
