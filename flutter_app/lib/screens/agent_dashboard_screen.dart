import 'dart:async';
import 'package:flutter/material.dart';
import '../core/service_locator.dart';
import '../models/agent.dart';
import '../models/room.dart';
import '../services/agent_service.dart';
import 'final_answer_screen.dart';

class AgentDashboardScreen extends StatefulWidget {
  final Room room;
  final String problemStatement;
  final int? taskId;

  const AgentDashboardScreen({
    super.key,
    required this.room,
    required this.problemStatement,
    this.taskId,
  });

  @override
  State<AgentDashboardScreen> createState() => _AgentDashboardScreenState();
}

class _AgentDashboardScreenState extends State<AgentDashboardScreen> {
  late final AgentService _agentService;
  late List<AgentInfo> _agents;
  StreamSubscription<List<AgentInfo>>? _agentSubscription;
  bool _isSimulating = false;
  bool _isFinished = false;

  @override
  void initState() {
    super.initState();
    _agentService = ServiceLocator.instance.agentService;
    _agents = _agentService.getInitialAgents();
    _startAgentStream();
  }

  @override
  void dispose() {
    _agentSubscription?.cancel();
    super.dispose();
  }

  void _startAgentStream() {
    _agentSubscription?.cancel();
    final isMock = ServiceLocator.instance.isMockMode;

    setState(() {
      _isSimulating = isMock;
      _isFinished = false;
      _agents = _agentService.getInitialAgents();
    });

    _agentSubscription = _agentService
        .watchAgents(
          roomId: widget.room.id ?? 1,
          problemStatement: widget.problemStatement,
          taskId: widget.taskId ?? widget.room.activeTaskId,
        )
        .listen(
      (updatedAgents) {
        if (!mounted) return;
        setState(() {
          _agents = updatedAgents;
          final allDone = _agents.every((a) => a.state == AgentState.completed);
          if (allDone) {
            _isSimulating = false;
            _isFinished = true;
          }
        });
      },
      onDone: () {
        if (!mounted) return;
        setState(() {
          _isSimulating = false;
          _isFinished = true;
        });
      },
    );
  }

  void _triggerSimulatedFailure() {
    _agentSubscription?.cancel();
    setState(() {
      _isSimulating = false;
      _isFinished = false;
      _agents = [
        _agents[0].copyWith(
          state: AgentState.completed,
          currentActivity: 'Decomposition finished',
          outputSummary: '4 objectives identified.',
        ),
        _agents[1].copyWith(
          state: AgentState.failed,
          currentActivity: 'Knowledge-retrieval index timeout (Simulated error state)',
          outputSummary: 'Simulated connection failure to external domain corpus.',
        ),
        _agents[2].copyWith(state: AgentState.waiting, currentActivity: 'Halted due to upstream failure'),
        _agents[3].copyWith(state: AgentState.waiting, currentActivity: 'Halted due to upstream failure'),
        _agents[4].copyWith(state: AgentState.waiting, currentActivity: 'Halted due to upstream failure'),
      ];
    });
  }

  void _resetAgents() {
    _startAgentStream();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isMock = ServiceLocator.instance.isMockMode;

    return Scaffold(
      appBar: AppBar(
        title: const Text('5-Agent Swarm Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Restart / Reconnect',
            onPressed: _startAgentStream,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Banner (Demo Mode or Live Serverpod Stream)
            if (isMock) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: Colors.amber.shade100,
                child: Row(
                  children: [
                    Icon(Icons.science_outlined, size: 18, color: Colors.amber.shade900),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'DEMO MODE: Simulating 5-agent state transitions. Real AI backend will bind to live events.',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Colors.amber.shade900,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ] else ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: Colors.purple.shade50,
                child: Row(
                  children: [
                    Icon(Icons.hub_rounded, size: 18, color: Colors.purple.shade700),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'SERVERPOD LIVE STREAM: Room ${widget.room.id ?? ""} • Task ${widget.taskId ?? widget.room.activeTaskId ?? ""}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Colors.purple.shade800,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Problem Summary Card
            Container(
              margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'TARGET PROBLEM',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.1,
                          color: Color(0xFF6C5CE7),
                        ),
                      ),
                      Text(
                        'Room: ${widget.room.code}',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.problemStatement,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ],
              ),
            ),

            // Demo Control State Switcher (Displayed ONLY in mock mode for test verification)
            if (isMock)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 4.0),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          minimumSize: const Size(0, 36),
                        ),
                        onPressed: _isSimulating ? null : _startAgentStream,
                        child: const Text('Re-run Simulation', style: TextStyle(fontSize: 12)),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          minimumSize: const Size(0, 36),
                          foregroundColor: Colors.redAccent,
                          side: const BorderSide(color: Colors.redAccent),
                        ),
                        onPressed: _triggerSimulatedFailure,
                        child: const Text('Test Fail State', style: TextStyle(fontSize: 12)),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      icon: const Icon(Icons.restart_alt_rounded, size: 20),
                      tooltip: 'Reset to Waiting',
                      onPressed: _resetAgents,
                    ),
                  ],
                ),
              ),

            // Agent List
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                itemCount: _agents.length,
                itemBuilder: (context, index) {
                  return _buildAgentCard(_agents[index]);
                },
              ),
            ),

            // Bottom Navigation to Final Answer
            Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: theme.scaffoldBackgroundColor,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.06),
                    offset: const Offset(0, -2),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => FinalAnswerScreen(
                        room: widget.room,
                        problemStatement: widget.problemStatement,
                        taskId: widget.taskId ?? widget.room.activeTaskId,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.assignment_turned_in_rounded),
                label: Text(_isFinished ? 'View Final Swarm Synthesis' : 'Preview Final Answer (Fast Path)'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isFinished ? const Color(0xFF6C5CE7) : Colors.indigo.shade600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAgentCard(AgentInfo agent) {
    Color stateColor;
    String stateLabel;
    IconData stateIcon;

    switch (agent.state) {
      case AgentState.waiting:
        stateColor = Colors.grey;
        stateLabel = 'WAITING';
        stateIcon = Icons.hourglass_empty_rounded;
        break;
      case AgentState.working:
        stateColor = const Color(0xFF0984E3);
        stateLabel = 'WORKING';
        stateIcon = Icons.sync_rounded;
        break;
      case AgentState.completed:
        stateColor = const Color(0xFF00B894);
        stateLabel = 'COMPLETED';
        stateIcon = Icons.check_circle_rounded;
        break;
      case AgentState.failed:
        stateColor = const Color(0xFFD63031);
        stateLabel = 'FAILED';
        stateIcon = Icons.error_outline_rounded;
        break;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: agent.state == AgentState.working
              ? stateColor.withValues(alpha: 0.8)
              : Colors.grey.shade200,
          width: agent.state == AgentState.working ? 1.5 : 1.0,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Agent Avatar, Name, Status Badge
            Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: stateColor.withValues(alpha: 0.12),
                  child: Icon(
                    _getIconData(agent.avatarIcon),
                    size: 20,
                    color: stateColor,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        agent.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      Text(
                        agent.roleDescription,
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: stateColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(stateIcon, size: 13, color: stateColor),
                      const SizedBox(width: 4),
                      Text(
                        stateLabel,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: stateColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Activity Text
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                agent.currentActivity,
                style: TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: Colors.grey.shade800,
                ),
              ),
            ),

            if (agent.outputSummary != null) ...[
              const SizedBox(height: 6),
              Text(
                'Artifact: ${agent.outputSummary!}',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                  color: Color(0xFF2D3436),
                ),
              ),
            ],

            // Progress bar if working
            if (agent.state == AgentState.working) ...[
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: agent.progress > 0 ? agent.progress : null,
                backgroundColor: stateColor.withValues(alpha: 0.2),
                valueColor: AlwaysStoppedAnimation<Color>(stateColor),
                minHeight: 4,
                borderRadius: BorderRadius.circular(4),
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getIconData(String iconName) {
    switch (iconName) {
      case 'architecture':
        return Icons.account_tree_rounded;
      case 'search':
        return Icons.manage_search_rounded;
      case 'memory':
        return Icons.speed_rounded;
      case 'security':
        return Icons.policy_rounded;
      case 'auto_fix_high':
        return Icons.auto_awesome_rounded;
      default:
        return Icons.psychology_rounded;
    }
  }
}
