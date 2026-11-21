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
import 'dart:async' as _ida;
import 'package:serverpod/serverpod.dart' as _is;

abstract class SharedTask
    implements _is.TableRow<int?>, _is.ProtocolSerialization {
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
      createdAt: _is.DateTimeJsonExtension.fromJson(
        jsonSerialization['createdAt'],
      ),
      completedAt: jsonSerialization['completedAt'] == null
          ? null
          : _is.DateTimeJsonExtension.fromJson(
              jsonSerialization['completedAt'],
            ),
    );
  }

  static final t = SharedTaskTable();

  static const db = SharedTaskRepository._();

  @override
  int? id;

  int roomId;

  String query;

  String status;

  String? fastapiTaskId;

  String? finalAnswer;

  String? error;

  DateTime createdAt;

  DateTime? completedAt;

  @override
  _is.Table<int?> get table => t;

  /// Returns a shallow copy of this [SharedTask]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  SharedTask copyWith({
    int? id,
    int? roomId,
    String? query,
    String? status,
    String? fastapiTaskId,
    String? finalAnswer,
    String? error,
    DateTime? createdAt,
    DateTime? completedAt = const _is.$UndefinedDateTime(),
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

  static SharedTaskInclude include() {
    return SharedTaskInclude._();
  }

  static SharedTaskIncludeList includeList({
    _is.WhereExpressionBuilder<SharedTaskTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    SharedTaskInclude? include,
  }) {
    return SharedTaskIncludeList._(
      where: where,
      limit: limit,
      offset: offset,
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      include: include,
    );
  }

  @override
  String toString() {
    return _is.SerializationManager.encode(this);
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
  @_is.useResult
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
    DateTime? completedAt = const _is.$UndefinedDateTime(),
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
      completedAt: completedAt is _is.UndefinedSentinel
          ? this.completedAt
          : completedAt,
    );
  }
}

class SharedTaskUpdateTable extends _is.UpdateTable<SharedTaskTable> {
  SharedTaskUpdateTable(super.table);

  _is.ColumnValue<int, int> roomId(int value) => _is.ColumnValue(
    table.roomId,
    value,
  );

  _is.ColumnValue<String, String> query(String value) => _is.ColumnValue(
    table.query,
    value,
  );

  _is.ColumnValue<String, String> status(String value) => _is.ColumnValue(
    table.status,
    value,
  );

  _is.ColumnValue<String, String> fastapiTaskId(String? value) =>
      _is.ColumnValue(
        table.fastapiTaskId,
        value,
      );

  _is.ColumnValue<String, String> finalAnswer(String? value) => _is.ColumnValue(
    table.finalAnswer,
    value,
  );

  _is.ColumnValue<String, String> error(String? value) => _is.ColumnValue(
    table.error,
    value,
  );

  _is.ColumnValue<DateTime, DateTime> createdAt(DateTime value) =>
      _is.ColumnValue(
        table.createdAt,
        value,
      );

  _is.ColumnValue<DateTime, DateTime> completedAt(DateTime? value) =>
      _is.ColumnValue(
        table.completedAt,
        value,
      );
}

class SharedTaskTable extends _is.Table<int?> {
  SharedTaskTable({super.tableRelation}) : super(tableName: 'shared_task') {
    updateTable = SharedTaskUpdateTable(this);
    roomId = _is.ColumnInt(
      'roomId',
      this,
    );
    query = _is.ColumnString(
      'query',
      this,
    );
    status = _is.ColumnString(
      'status',
      this,
    );
    fastapiTaskId = _is.ColumnString(
      'fastapiTaskId',
      this,
    );
    finalAnswer = _is.ColumnString(
      'finalAnswer',
      this,
    );
    error = _is.ColumnString(
      'error',
      this,
    );
    createdAt = _is.ColumnDateTime(
      'createdAt',
      this,
    );
    completedAt = _is.ColumnDateTime(
      'completedAt',
      this,
    );
  }

  late final SharedTaskUpdateTable updateTable;

  late final _is.ColumnInt roomId;

  late final _is.ColumnString query;

  late final _is.ColumnString status;

  late final _is.ColumnString fastapiTaskId;

  late final _is.ColumnString finalAnswer;

  late final _is.ColumnString error;

  late final _is.ColumnDateTime createdAt;

  late final _is.ColumnDateTime completedAt;

  @override
  List<_is.Column> get columns => [
    id,
    roomId,
    query,
    status,
    fastapiTaskId,
    finalAnswer,
    error,
    createdAt,
    completedAt,
  ];
}

class SharedTaskInclude extends _is.IncludeObject {
  SharedTaskInclude._();

  @override
  Map<String, _is.Include?> get includes => {};

  @override
  _is.Table<int?> get table => SharedTask.t;
}

class SharedTaskIncludeList extends _is.IncludeList {
  SharedTaskIncludeList._({
    _is.WhereExpressionBuilder<SharedTaskTable>? where,
    super.limit,
    super.offset,
    super.orderBy,
    super.orderByList,
    super.include,
  }) {
    super.where = where?.call(SharedTask.t);
  }

  @override
  Map<String, _is.Include?> get includes => include?.includes ?? {};

  @override
  _is.Table<int?> get table => SharedTask.t;
}

class SharedTaskRepository {
  const SharedTaskRepository._();

  /// Returns a list of [SharedTask]s matching the given query parameters.
  ///
  /// Use [where] to specify which items to include in the return value.
  /// If none is specified, all items will be returned.
  ///
  /// To specify the order of the items use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// The maximum number of items can be set by [limit]. If no limit is set,
  /// all items matching the query will be returned.
  ///
  /// [offset] defines how many items to skip, after which [limit] (or all)
  /// items are read from the database.
  ///
  /// ```dart
  /// var persons = await Persons.db.find(
  ///   session,
  ///   where: (t) => t.lastName.equals('Jones'),
  ///   orderBy: (t) => t.firstName,
  ///   limit: 100,
  /// );
  /// ```
  Future<List<SharedTask>> find(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<SharedTaskTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.find<SharedTask>(
      where: where?.call(SharedTask.t),
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      limit: limit,
      offset: offset,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Emits [SharedTask]s matching the given query parameters every time the
  /// source tables are modified.
  ///
  /// Use [where] to specify which items to include in the return value.
  /// If none is specified, all items will be returned.
  ///
  /// To specify the order of the items use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// The maximum number of items can be set by [limit]. If no limit is set,
  /// all items matching the query will be returned.
  ///
  /// [offset] defines how many items to skip, after which [limit] (or all)
  /// items are read from the database.
  ///
  /// Use [throttle] to specify the minimum interval between queries. It can
  /// also be set to `null`, in which case the stream will only be throttled
  /// when its subscription is paused.
  ///
  /// Source tables are collected from the queried table, [where], [orderBy],
  /// [orderByList], and the [include] graph. [alsoTriggerOnTables] is added
  /// to that set. Pass [Table] instances such as `SharedTask.t`.
  ///
  /// Raw [Expression] SQL is not inspected. Tables referenced only in raw
  /// SQL must be passed via [alsoTriggerOnTables].
  ///
  /// The stream always reads committed state and never joins an ambient
  /// [Transaction]. Emissions for a write fire after that write commits.
  ///
  /// Currently only supported on SQLite. Calling this method on PostgreSQL
  /// throws an [UnsupportedError].
  ///
  /// ```dart
  /// var subscription = Persons.db.watch(
  ///   session,
  ///   where: (t) => t.lastName.equals('Jones'),
  ///   orderBy: (t) => t.firstName,
  ///   limit: 100,
  /// ).listen((persons) {
  ///   // Handle the latest matching rows.
  /// });
  /// ```
  _ida.Stream<List<SharedTask>> watch(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<SharedTaskTable>? where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    Duration? throttle = const Duration(milliseconds: 30),
    Iterable<_is.Table>? alsoTriggerOnTables,
  }) {
    return session.db.watch<SharedTask>(
      where: where?.call(SharedTask.t),
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      limit: limit,
      offset: offset,
      throttle: throttle,
      alsoTriggerOnTables: alsoTriggerOnTables,
    );
  }

  /// Returns the first matching [SharedTask] matching the given query parameters.
  ///
  /// Use [where] to specify which items to include in the return value.
  /// If none is specified, all items will be returned.
  ///
  /// To specify the order use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// [offset] defines how many items to skip, after which the next one will be picked.
  ///
  /// ```dart
  /// var youngestPerson = await Persons.db.findFirstRow(
  ///   session,
  ///   where: (t) => t.lastName.equals('Jones'),
  ///   orderBy: (t) => t.age,
  /// );
  /// ```
  Future<SharedTask?> findFirstRow(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<SharedTaskTable>? where,
    int? offset,
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.findFirstRow<SharedTask>(
      where: where?.call(SharedTask.t),
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      offset: offset,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Finds a single [SharedTask] by its [id] or null if no such row exists.
  Future<SharedTask?> findById(
    _is.DatabaseSession session,
    int id, {
    _is.Transaction? transaction,
    _is.LockMode? lockMode,
    _is.LockBehavior? lockBehavior,
  }) async {
    return session.db.findById<SharedTask>(
      id,
      transaction: transaction,
      lockMode: lockMode,
      lockBehavior: lockBehavior,
    );
  }

  /// Inserts all [SharedTask]s in the list and returns the inserted rows.
  ///
  /// The returned [SharedTask]s will have their `id` fields set.
  ///
  /// This is an atomic operation, meaning that if one of the rows fails to
  /// insert, none of the rows will be inserted.
  ///
  /// If [ignoreConflicts] is set to `true`, rows that conflict with existing
  /// rows are silently skipped, and only the successfully inserted rows are
  /// returned.
  ///
  /// If [noReturn] is set to `true`, the inserted rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<SharedTask>> insert(
    _is.DatabaseSession session,
    List<SharedTask> rows, {
    _is.Transaction? transaction,
    bool ignoreConflicts = false,
    bool noReturn = false,
  }) async {
    return session.db.insert<SharedTask>(
      rows,
      transaction: transaction,
      ignoreConflicts: ignoreConflicts,
      noReturn: noReturn,
    );
  }

  /// Inserts a single [SharedTask] and returns the inserted row.
  ///
  /// The returned [SharedTask] will have its `id` field set.
  Future<SharedTask> insertRow(
    _is.DatabaseSession session,
    SharedTask row, {
    _is.Transaction? transaction,
  }) async {
    return session.db.insertRow<SharedTask>(
      row,
      transaction: transaction,
    );
  }

  /// Upserts all [SharedTask]s in the list and returns the resulting rows.
  ///
  /// If a row conflicts on the given [conflictColumns], the existing row is
  /// updated with the new values. Otherwise, a new row is inserted.
  ///
  /// If [updateColumns] is provided, only those columns will be updated on
  /// conflict. If null, all non-conflict, non-id columns are updated.
  ///
  /// If [updateWhere] is provided, the update only applies to rows matching the
  /// given expression. Conflicting rows that don't match are skipped and not
  /// returned, so the resulting list may be shorter than [rows].
  ///
  /// The returned [SharedTask]s will have their `id` fields set.
  ///
  /// This is an atomic operation, meaning that if one of the rows fails,
  /// none of the rows will be affected.
  ///
  /// If [noReturn] is set to `true`, the resulting rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<SharedTask>> upsert(
    _is.DatabaseSession session,
    List<SharedTask> rows, {
    required _is.ColumnSelections<SharedTaskTable> conflictColumns,
    _is.ColumnSelections<SharedTaskTable>? updateColumns,
    _is.WhereExpressionBuilder<SharedTaskTable>? updateWhere,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.upsert<SharedTask>(
      rows,
      conflictColumns: conflictColumns(SharedTask.t),
      updateColumns: updateColumns?.call(SharedTask.t),
      updateWhere: updateWhere?.call(SharedTask.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Upserts a single [SharedTask] and returns the resulting row.
  ///
  /// If the row conflicts on the given [conflictColumns], the existing row is
  /// updated. Otherwise, a new row is inserted.
  ///
  /// If [updateColumns] is provided, only those columns will be updated on
  /// conflict. If null, all non-conflict, non-id columns are updated.
  ///
  /// If [updateWhere] is provided, the update only applies when the existing
  /// row matches the expression. Returns `null` if no row was affected — for
  /// example when [updateWhere] does not match the conflicting row.
  ///
  /// The returned [SharedTask] will have its `id` field set.
  Future<SharedTask?> upsertRow(
    _is.DatabaseSession session,
    SharedTask row, {
    required _is.ColumnSelections<SharedTaskTable> conflictColumns,
    _is.ColumnSelections<SharedTaskTable>? updateColumns,
    _is.WhereExpressionBuilder<SharedTaskTable>? updateWhere,
    _is.Transaction? transaction,
  }) async {
    return session.db.upsertRow<SharedTask>(
      row,
      conflictColumns: conflictColumns(SharedTask.t),
      updateColumns: updateColumns?.call(SharedTask.t),
      updateWhere: updateWhere?.call(SharedTask.t),
      transaction: transaction,
    );
  }

  /// Updates all [SharedTask]s in the list and returns the updated rows. If
  /// [columns] is provided, only those columns will be updated. Defaults to
  /// all columns.
  /// This is an atomic operation, meaning that if one of the rows fails to
  /// update, none of the rows will be updated.
  ///
  /// If [noReturn] is set to `true`, the updated rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<SharedTask>> update(
    _is.DatabaseSession session,
    List<SharedTask> rows, {
    _is.ColumnSelections<SharedTaskTable>? columns,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.update<SharedTask>(
      rows,
      columns: columns?.call(SharedTask.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Updates a single [SharedTask]. The row needs to have its id set.
  /// Optionally, a list of [columns] can be provided to only update those
  /// columns. Defaults to all columns.
  Future<SharedTask> updateRow(
    _is.DatabaseSession session,
    SharedTask row, {
    _is.ColumnSelections<SharedTaskTable>? columns,
    _is.Transaction? transaction,
  }) async {
    return session.db.updateRow<SharedTask>(
      row,
      columns: columns?.call(SharedTask.t),
      transaction: transaction,
    );
  }

  /// Updates a single [SharedTask] by its [id] with the specified [columnValues].
  /// Returns the updated row or null if no row with the given id exists.
  Future<SharedTask?> updateById(
    _is.DatabaseSession session,
    int id, {
    required _is.ColumnValueListBuilder<SharedTaskUpdateTable> columnValues,
    _is.Transaction? transaction,
  }) async {
    return session.db.updateById<SharedTask>(
      id,
      columnValues: columnValues(SharedTask.t.updateTable),
      transaction: transaction,
    );
  }

  /// Updates all [SharedTask]s matching the [where] expression with the specified [columnValues].
  /// Returns the list of updated rows.
  ///
  /// If [noReturn] is set to `true`, the updated rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<SharedTask>> updateWhere(
    _is.DatabaseSession session, {
    required _is.ColumnValueListBuilder<SharedTaskUpdateTable> columnValues,
    required _is.WhereExpressionBuilder<SharedTaskTable> where,
    int? limit,
    int? offset,
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.updateWhere<SharedTask>(
      columnValues: columnValues(SharedTask.t.updateTable),
      where: where(SharedTask.t),
      limit: limit,
      offset: offset,
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Deletes all [SharedTask]s in the list and returns the deleted rows.
  ///
  /// To specify the order of the returned rows use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// This is an atomic operation, meaning that if one of the rows fail to
  /// be deleted, none of the rows will be deleted.
  ///
  /// If [noReturn] is set to `true`, the deleted rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<SharedTask>> delete(
    _is.DatabaseSession session,
    List<SharedTask> rows, {
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.delete<SharedTask>(
      rows,
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Deletes a single [SharedTask].
  Future<SharedTask> deleteRow(
    _is.DatabaseSession session,
    SharedTask row, {
    _is.Transaction? transaction,
  }) async {
    return session.db.deleteRow<SharedTask>(
      row,
      transaction: transaction,
    );
  }

  /// Deletes all rows matching the [where] expression.
  ///
  /// To specify the order of the returned rows use [orderBy] or [orderByList]
  /// when sorting by multiple columns.
  ///
  /// If [noReturn] is set to `true`, the deleted rows are not read back from
  /// the database and an empty list is returned. This avoids the overhead of
  /// transferring and deserializing the rows when the result is not needed.
  Future<List<SharedTask>> deleteWhere(
    _is.DatabaseSession session, {
    required _is.WhereExpressionBuilder<SharedTaskTable> where,
    _is.OrderByBuilder<SharedTaskTable>? orderBy,
    _is.OrderByListBuilder<SharedTaskTable>? orderByList,
    _is.Transaction? transaction,
    bool noReturn = false,
  }) async {
    return session.db.deleteWhere<SharedTask>(
      where: where(SharedTask.t),
      orderBy: orderBy?.call(SharedTask.t),
      orderByList: orderByList?.call(SharedTask.t),
      transaction: transaction,
      noReturn: noReturn,
    );
  }

  /// Counts the number of rows matching the [where] expression. If omitted,
  /// will return the count of all rows in the table.
  Future<int> count(
    _is.DatabaseSession session, {
    _is.WhereExpressionBuilder<SharedTaskTable>? where,
    int? limit,
    _is.Transaction? transaction,
  }) async {
    return session.db.count<SharedTask>(
      where: where?.call(SharedTask.t),
      limit: limit,
      transaction: transaction,
    );
  }

  /// Acquires row-level locks on [SharedTask] rows matching the [where] expression.
  Future<void> lockRows(
    _is.DatabaseSession session, {
    required _is.WhereExpressionBuilder<SharedTaskTable> where,
    required _is.LockMode lockMode,
    required _is.Transaction transaction,
    _is.LockBehavior lockBehavior = _is.LockBehavior.wait,
  }) async {
    return session.db.lockRows<SharedTask>(
      where: where(SharedTask.t),
      lockMode: lockMode,
      lockBehavior: lockBehavior,
      transaction: transaction,
    );
  }
}
