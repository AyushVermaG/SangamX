import 'participant.dart';

enum RoomStatus {
  waiting,
  problemSubmitted,
  analyzing,
  completed,
}

class Room {
  /// The Serverpod database ID (integer).
  final int? id;

  /// The human-readable 6-character room code (e.g. 'A8B9C0' or 'SANGAM-7429').
  final String code;

  final String name;
  final RoomStatus status;
  final List<Participant> participants;
  final String? currentProblem;

  /// The Serverpod shared task ID (integer).
  final int? activeTaskId;

  final DateTime createdAt;
  final bool isDemo;

  const Room({
    this.id,
    required this.code,
    required this.name,
    this.status = RoomStatus.waiting,
    required this.participants,
    this.currentProblem,
    this.activeTaskId,
    required this.createdAt,
    this.isDemo = true,
  });

  String get statusDisplay {
    switch (status) {
      case RoomStatus.waiting:
        return 'Waiting for Problem';
      case RoomStatus.problemSubmitted:
        return 'Problem Submitted';
      case RoomStatus.analyzing:
        return 'Agents Analyzing';
      case RoomStatus.completed:
        return 'Synthesis Completed';
    }
  }

  Room copyWith({
    int? id,
    String? code,
    String? name,
    RoomStatus? status,
    List<Participant>? participants,
    String? currentProblem,
    int? activeTaskId,
    DateTime? createdAt,
    bool? isDemo,
  }) {
    return Room(
      id: id ?? this.id,
      code: code ?? this.code,
      name: name ?? this.name,
      status: status ?? this.status,
      participants: participants ?? this.participants,
      currentProblem: currentProblem ?? this.currentProblem,
      activeTaskId: activeTaskId ?? this.activeTaskId,
      createdAt: createdAt ?? this.createdAt,
      isDemo: isDemo ?? this.isDemo,
    );
  }
}
