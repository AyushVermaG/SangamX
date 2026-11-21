import 'participant.dart';

enum RoomStatus {
  waiting,
  problemSubmitted,
  analyzing,
  completed,
}

class Room {
  final String code;
  final String name;
  final RoomStatus status;
  final List<Participant> participants;
  final String? currentProblem;
  final DateTime createdAt;
  final bool isDemo;

  const Room({
    required this.code,
    required this.name,
    this.status = RoomStatus.waiting,
    required this.participants,
    this.currentProblem,
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
    String? code,
    String? name,
    RoomStatus? status,
    List<Participant>? participants,
    String? currentProblem,
    DateTime? createdAt,
    bool? isDemo,
  }) {
    return Room(
      code: code ?? this.code,
      name: name ?? this.name,
      status: status ?? this.status,
      participants: participants ?? this.participants,
      currentProblem: currentProblem ?? this.currentProblem,
      createdAt: createdAt ?? this.createdAt,
      isDemo: isDemo ?? this.isDemo,
    );
  }
}
