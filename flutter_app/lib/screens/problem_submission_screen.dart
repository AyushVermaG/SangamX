import 'package:flutter/material.dart';
import '../models/room.dart';
import '../services/mock/mock_room_service.dart';
import 'agent_dashboard_screen.dart';

class ProblemSubmissionScreen extends StatefulWidget {
  final Room room;

  const ProblemSubmissionScreen({super.key, required this.room});

  @override
  State<ProblemSubmissionScreen> createState() => _ProblemSubmissionScreenState();
}

class _ProblemSubmissionScreenState extends State<ProblemSubmissionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _problemController = TextEditingController();
  bool _isLoading = false;

  final List<String> _samplePrompts = [
    'Design an offline-first synchronization engine using conflict-free replicated data types (CRDTs) resilient to intermittent connectivity.',
    'Formulate a distributed consensus architecture for low-power edge nodes handling concurrent telemetry updates.',
    'Construct an automated verification pipeline for smart contract state transitions preventing reentrancy attacks.',
  ];

  @override
  void dispose() {
    _problemController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final problem = _problemController.text.trim();
    setState(() => _isLoading = true);

    try {
      final roomService = MockRoomService();
      await roomService.submitProblem(
        roomCode: widget.room.code,
        problemStatement: problem,
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => AgentDashboardScreen(
            room: widget.room,
            problemStatement: problem,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to submit problem: $e'),
          backgroundColor: Colors.redAccent,
        ),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Submit Problem'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Text(
                  'What would you like the agents to solve?',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Describe the architectural challenge, engineering tradeoff, or problem statement for the 5-Agent swarm.',
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
                ),
                const SizedBox(height: 16),

                // Problem Statement Input
                TextFormField(
                  controller: _problemController,
                  maxLines: 6,
                  decoration: InputDecoration(
                    hintText: 'Enter your technical problem or research topic in detail...',
                    alignLabelWithHint: true,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please provide a problem statement to analyze';
                    }
                    if (value.trim().length < 15) {
                      return 'Please provide a more descriptive problem (at least 15 characters)';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 20),

                // Quick Sample Prompts
                Text(
                  'Quick-Fill Sample Challenges:',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey.shade700,
                  ),
                ),
                const SizedBox(height: 8),
                Column(
                  children: _samplePrompts.map((sample) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8.0),
                      child: InkWell(
                        onTap: () {
                          setState(() {
                            _problemController.text = sample;
                          });
                        },
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.bolt_rounded, size: 16, color: Color(0xFF6C5CE7)),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  sample,
                                  style: const TextStyle(fontSize: 12),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 24),

                // Submit Action
                ElevatedButton.icon(
                  onPressed: _isLoading ? null : _handleSubmit,
                  icon: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Icon(Icons.rocket_launch_rounded),
                  label: Text(_isLoading ? 'Dispatching to Swarm...' : 'Submit to 5-Agent Swarm'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
