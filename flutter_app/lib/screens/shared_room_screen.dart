import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/service_locator.dart';
import '../models/room.dart';
import '../models/participant.dart';
import 'problem_submission_screen.dart';
import 'agent_dashboard_screen.dart';

class SharedRoomScreen extends StatefulWidget {
  final Room room;

  const SharedRoomScreen({super.key, required this.room});

  @override
  State<SharedRoomScreen> createState() => _SharedRoomScreenState();
}

class _SharedRoomScreenState extends State<SharedRoomScreen> {
  late Room _room;
  StreamSubscription<Room>? _roomSubscription;

  @override
  void initState() {
    super.initState();
    _room = widget.room;
    _subscribeToRoomUpdates();
  }

  void _subscribeToRoomUpdates() {
    if (_room.id != null) {
      _roomSubscription?.cancel();
      _roomSubscription = ServiceLocator.instance.roomService
          .watchRoom(_room.id!)
          .listen((updatedRoom) {
        if (!mounted) return;
        setState(() {
          _room = updatedRoom;
        });
      });
    }
  }

  @override
  void dispose() {
    _roomSubscription?.cancel();
    super.dispose();
  }

  Future<void> _refreshRoom() async {
    if (_room.id == null) return;
    try {
      final updated = await ServiceLocator.instance.roomService.getRoom(_room.id!);
      if (mounted) {
        setState(() {
          _room = updated;
        });
      }
    } catch (_) {}
  }

  void _copyCode() {
    Clipboard.setData(ClipboardData(text: _room.code));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Room code "${_room.code}" copied to clipboard!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isMock = ServiceLocator.instance.isMockMode;
    final hasActiveTask = _room.status == RoomStatus.analyzing && _room.currentProblem != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(_room.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Roster',
            onPressed: _refreshRoom,
          ),
          IconButton(
            icon: const Icon(Icons.share_rounded),
            tooltip: 'Copy Room Code',
            onPressed: _copyCode,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Room Header Card
            Container(
              margin: const EdgeInsets.all(16.0),
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade200),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.04),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'ROOM CODE',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.2,
                              color: Color(0xFF6C5CE7),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              Text(
                                _room.code,
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 1.5,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.copy_rounded, size: 16),
                                onPressed: _copyCode,
                                constraints: const BoxConstraints(),
                                padding: const EdgeInsets.symmetric(horizontal: 6),
                              ),
                            ],
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.green.shade200),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: Colors.green,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              _room.statusDisplay,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: Colors.green.shade800,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const Divider(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${_room.participants.length} Active Participants',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: Colors.grey.shade700,
                        ),
                      ),
                      if (isMock)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.blueGrey.shade50,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Text(
                            'Demo Swarm Mode',
                            style: TextStyle(fontSize: 11, color: Colors.blueGrey),
                          ),
                        )
                      else
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.purple.shade50,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            'Serverpod Room ${_room.id ?? ""}',
                            style: TextStyle(fontSize: 11, color: Colors.purple.shade700, fontWeight: FontWeight.w600),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),

            // Participants List Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 6.0),
              child: Row(
                children: [
                  const Icon(Icons.people_outline_rounded, size: 18, color: Color(0xFF6C5CE7)),
                  const SizedBox(width: 8),
                  Text(
                    'Collaborators in Room',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),

            // Participants List
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                itemCount: _room.participants.length,
                separatorBuilder: (context, index) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final participant = _room.participants[index];
                  return _buildParticipantTile(participant);
                },
              ),
            ),

            // Bottom Action Area
            Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: theme.scaffoldBackgroundColor,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    offset: const Offset(0, -2),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (hasActiveTask) ...[
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => AgentDashboardScreen(
                              room: _room,
                              problemStatement: _room.currentProblem!,
                              taskId: _room.activeTaskId,
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.visibility_rounded),
                      label: const Text('View Active Task in Dashboard'),
                    ),
                  ] else ...[
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => ProblemSubmissionScreen(room: _room),
                          ),
                        );
                      },
                      icon: const Icon(Icons.edit_note_rounded),
                      label: const Text('Submit Problem Statement'),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildParticipantTile(Participant p) {
    final colors = [
      const Color(0xFF6C5CE7),
      const Color(0xFF00CEC9),
      const Color(0xFFE17055),
      const Color(0xFF0984E3),
      const Color(0xFF6AB04C),
    ];
    final color = colors[p.id.hashCode.abs() % colors.length];

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: p.isCurrentUser ? const Color(0xFF6C5CE7).withValues(alpha: 0.5) : Colors.grey.shade200,
        ),
      ),
      color: p.isCurrentUser ? const Color(0xFF6C5CE7).withValues(alpha: 0.04) : Colors.white,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.15),
          foregroundColor: color,
          radius: 20,
          child: Text(
            p.initials,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
          ),
        ),
        title: Row(
          children: [
            Text(
              p.name,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
            if (p.isCurrentUser) ...[
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF6C5CE7).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'YOU',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF6C5CE7),
                  ),
                ),
              ),
            ],
            if (p.isHost) ...[
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.amber.shade100,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  'HOST',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    color: Colors.amber.shade900,
                  ),
                ),
              ),
            ],
          ],
        ),
        subtitle: Text(
          p.role,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
        trailing: Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: p.isOnline ? Colors.green : Colors.grey,
            shape: BoxShape.circle,
          ),
        ),
      ),
    );
  }
}
