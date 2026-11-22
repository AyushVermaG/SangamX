/* AUTOMATICALLY GENERATED CODE DO NOT MODIFY */
/*   To generate run: "serverpod generate"    */

// ignore_for_file: implementation_imports
// ignore_for_file: library_private_types_in_public_api
// ignore_for_file: non_constant_identifier_names
// ignore_for_file: public_member_api_docs
// ignore_for_file: type_literal_in_constant_pattern
// ignore_for_file: use_super_parameters
// ignore_for_file: invalid_use_of_internal_member
// ignore_for_file: dead_code, unnecessary_type_check

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:serverpod_auth_core_client/serverpod_auth_core_client.dart'
    as _iacc;
import 'package:serverpod_auth_idp_client/serverpod_auth_idp_client.dart'
    as _iaic;
import 'package:serverpod_client/serverpod_client.dart' as _isc;
import 'greetings/greeting.dart' as _izw8z7ou;
import 'rooms/room.dart' as _ix383f3m;
import 'rooms/room_detail.dart' as _i47fvyr6;
import 'rooms/room_participant.dart' as _iafq7euw;
import 'rooms/room_update.dart' as _i7lgg7qm;
import 'tasks/shared_task.dart' as _ie6z52ep;
import 'tasks/task_update.dart' as _iwdrvykn;
export 'greetings/greeting.dart';
export 'rooms/room.dart';
export 'rooms/room_detail.dart';
export 'rooms/room_participant.dart';
export 'rooms/room_update.dart';
export 'tasks/shared_task.dart';
export 'tasks/task_update.dart';
export 'client.dart';

class Protocol extends _isc.SerializationManager
    implements _isc.ProtocolDeserializationProvider {
  Protocol._();

  factory Protocol() => _instance;

  static final Protocol _instance = Protocol._().._registerHostProtocols();

  @override
  _isc.ProtocolDeserialization get deserializationMetadata =>
      _isc.ProtocolDeserialization.cached(
        this,
        types: const [
          _isc.getType<_izw8z7ou.Greeting>,
          _isc.getType<_ix383f3m.Room>,
          _isc.getType<_i47fvyr6.RoomDetail>,
          _isc.getType<_iafq7euw.RoomParticipant>,
          _isc.getType<_i7lgg7qm.RoomUpdate>,
          _isc.getType<_ie6z52ep.SharedTask>,
          _isc.getType<_iwdrvykn.TaskUpdate>,
          _isc.getType<_izw8z7ou.Greeting?>,
          _isc.getType<_ix383f3m.Room?>,
          _isc.getType<_i47fvyr6.RoomDetail?>,
          _isc.getType<_iafq7euw.RoomParticipant?>,
          _isc.getType<_i7lgg7qm.RoomUpdate?>,
          _isc.getType<_ie6z52ep.SharedTask?>,
          _isc.getType<_iwdrvykn.TaskUpdate?>,
          _isc.getType<List<_iafq7euw.RoomParticipant>>,
        ],
        modules: const [_iaic.Protocol.new, _iacc.Protocol.new],
        classNames: const [
          'Greeting',
          'Room',
          'RoomDetail',
          'RoomParticipant',
          'RoomUpdate',
          'SharedTask',
          'TaskUpdate',
        ],
      );

  static String? getClassNameFromObjectJson(dynamic data) =>
      _isc.ProtocolDeserialization.readClassName(data);

  @override
  T deserialize<T>(dynamic data, [Type? t]) {
    t ??= T;
    final rawDataClassName = _isc.ProtocolDeserialization.readClassName(data);
    final dataClassName = rawDataClassName;
    if (dataClassName != null && dataClassName != getClassNameForType(t)) {
      try {
        return deserializeByClassName({
          'className': dataClassName,
          'data': data,
        });
      } on _isc.DeserializationClassNameNotFoundException catch (_) {
        // If the className is not recognized (e.g., older client receiving
        // data with a new subtype), fall back to deserializing without the
        // className, using the expected type T.
      }
    }

    if (t == _izw8z7ou.Greeting) {
      return _izw8z7ou.Greeting.fromJson(data) as T;
    }
    if (t == _ix383f3m.Room) {
      return _ix383f3m.Room.fromJson(data) as T;
    }
    if (t == _i47fvyr6.RoomDetail) {
      return _i47fvyr6.RoomDetail.fromJson(data) as T;
    }
    if (t == _iafq7euw.RoomParticipant) {
      return _iafq7euw.RoomParticipant.fromJson(data) as T;
    }
    if (t == _i7lgg7qm.RoomUpdate) {
      return _i7lgg7qm.RoomUpdate.fromJson(data) as T;
    }
    if (t == _ie6z52ep.SharedTask) {
      return _ie6z52ep.SharedTask.fromJson(data) as T;
    }
    if (t == _iwdrvykn.TaskUpdate) {
      return _iwdrvykn.TaskUpdate.fromJson(data) as T;
    }
    if (t == _isc.getType<_izw8z7ou.Greeting?>()) {
      return (data != null ? _izw8z7ou.Greeting.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_ix383f3m.Room?>()) {
      return (data != null ? _ix383f3m.Room.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_i47fvyr6.RoomDetail?>()) {
      return (data != null ? _i47fvyr6.RoomDetail.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_iafq7euw.RoomParticipant?>()) {
      return (data != null ? _iafq7euw.RoomParticipant.fromJson(data) : null)
          as T;
    }
    if (t == _isc.getType<_i7lgg7qm.RoomUpdate?>()) {
      return (data != null ? _i7lgg7qm.RoomUpdate.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_ie6z52ep.SharedTask?>()) {
      return (data != null ? _ie6z52ep.SharedTask.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_iwdrvykn.TaskUpdate?>()) {
      return (data != null ? _iwdrvykn.TaskUpdate.fromJson(data) : null) as T;
    }
    if (t == List<_iafq7euw.RoomParticipant>) {
      return (data as List)
              .map((e) => deserialize<_iafq7euw.RoomParticipant>(e))
              .toList()
          as T;
    }
    final modules = deserializationMetadata.modulesForDeserialization(
      t,
      className: rawDataClassName,
    );
    for (final module in modules) {
      try {
        return module.deserialize<T>(data, t);
      } on _isc.DeserializationTypeNotFoundException catch (_) {}
    }

    return super.deserialize<T>(data, t);
  }

  static String? getClassNameForType(Type type) {
    return switch (type) {
      _izw8z7ou.Greeting => 'Greeting',
      _ix383f3m.Room => 'Room',
      _i47fvyr6.RoomDetail => 'RoomDetail',
      _iafq7euw.RoomParticipant => 'RoomParticipant',
      _i7lgg7qm.RoomUpdate => 'RoomUpdate',
      _ie6z52ep.SharedTask => 'SharedTask',
      _iwdrvykn.TaskUpdate => 'TaskUpdate',
      _ => null,
    };
  }

  @override
  String? getClassNameForObject(Object? data) {
    String? className = super.getClassNameForObject(data);
    if (className != null) return className;

    if (data is Map<String, dynamic> && data['__className__'] is String) {
      return (data['__className__'] as String).replaceFirst(
        'sangamx_serverpod.',
        '',
      );
    }

    switch (data) {
      case _izw8z7ou.Greeting():
        return 'Greeting';
      case _ix383f3m.Room():
        return 'Room';
      case _i47fvyr6.RoomDetail():
        return 'RoomDetail';
      case _iafq7euw.RoomParticipant():
        return 'RoomParticipant';
      case _i7lgg7qm.RoomUpdate():
        return 'RoomUpdate';
      case _ie6z52ep.SharedTask():
        return 'SharedTask';
      case _iwdrvykn.TaskUpdate():
        return 'TaskUpdate';
    }
    className = _iaic.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.')
          ? className
          : 'serverpod_auth_idp.$className';
    }
    className = _iacc.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.')
          ? className
          : 'serverpod_auth_core.$className';
    }
    return null;
  }

  @override
  dynamic deserializeByClassName(Map<String, dynamic> data) {
    var dataClassName = data['className'];
    if (dataClassName is! String) {
      return super.deserializeByClassName(data);
    }
    if (dataClassName == 'Greeting') {
      return deserialize<_izw8z7ou.Greeting>(data['data']);
    }
    if (dataClassName == 'Room') {
      return deserialize<_ix383f3m.Room>(data['data']);
    }
    if (dataClassName == 'RoomDetail') {
      return deserialize<_i47fvyr6.RoomDetail>(data['data']);
    }
    if (dataClassName == 'RoomParticipant') {
      return deserialize<_iafq7euw.RoomParticipant>(data['data']);
    }
    if (dataClassName == 'RoomUpdate') {
      return deserialize<_i7lgg7qm.RoomUpdate>(data['data']);
    }
    if (dataClassName == 'SharedTask') {
      return deserialize<_ie6z52ep.SharedTask>(data['data']);
    }
    if (dataClassName == 'TaskUpdate') {
      return deserialize<_iwdrvykn.TaskUpdate>(data['data']);
    }
    if (dataClassName.startsWith('serverpod_auth_idp.')) {
      return _iaic.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(19),
      });
    }
    if (dataClassName.startsWith('serverpod_auth_core.')) {
      return _iacc.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(20),
      });
    }
    return super.deserializeByClassName(data);
  }

  void _registerHostProtocols() {
    _iaic.Protocol().registerHostProtocol('sangamx_serverpod', this);
    _iacc.Protocol().registerHostProtocol('sangamx_serverpod', this);
  }

  @override
  String getModuleName() => 'sangamx_serverpod';

  /// Maps any `Record`s known to this [Protocol] to their JSON representation
  ///
  /// Throws in case the record type is not known.
  ///
  /// This method will return `null` (only) for `null` inputs.
  Map<String, dynamic>? mapRecordToJson(Record? record) {
    if (record == null) {
      return null;
    }
    try {
      return _iaic.Protocol().mapRecordToJson(record);
    } catch (_) {}
    try {
      return _iacc.Protocol().mapRecordToJson(record);
    } catch (_) {}
    throw Exception('Unsupported record type ${record.runtimeType}');
  }
}
