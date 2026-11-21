class Participant {
  final String id;
  final String name;
  final String role;
  final bool isHost;
  final bool isCurrentUser;

  const Participant({
    required this.id,
    required this.name,
    required this.role,
    this.isHost = false,
    this.isCurrentUser = false,
  });

  String get initials {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts[0].substring(0, 1).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
}
