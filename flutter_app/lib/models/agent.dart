enum AgentState {
  waiting,
  working,
  completed,
  failed,
}

class AgentInfo {
  final String id;
  final String name;
  final String roleDescription;
  final String avatarIcon;
  final AgentState state;
  final String currentActivity;
  final String? outputSummary;
  final double progress; // 0.0 to 1.0

  const AgentInfo({
    required this.id,
    required this.name,
    required this.roleDescription,
    required this.avatarIcon,
    this.state = AgentState.waiting,
    this.currentActivity = 'Awaiting activation',
    this.outputSummary,
    this.progress = 0.0,
  });

  AgentInfo copyWith({
    String? id,
    String? name,
    String? roleDescription,
    String? avatarIcon,
    AgentState? state,
    String? currentActivity,
    String? outputSummary,
    double? progress,
  }) {
    return AgentInfo(
      id: id ?? this.id,
      name: name ?? this.name,
      roleDescription: roleDescription ?? this.roleDescription,
      avatarIcon: avatarIcon ?? this.avatarIcon,
      state: state ?? this.state,
      currentActivity: currentActivity ?? this.currentActivity,
      outputSummary: outputSummary ?? this.outputSummary,
      progress: progress ?? this.progress,
    );
  }
}
