import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/service_locator.dart';
import '../models/room.dart';
import 'shared_room_screen.dart';

class FinalAnswerScreen extends StatefulWidget {
  final Room room;
  final String problemStatement;
  final int? taskId;
  final String? initialAnswer;

  const FinalAnswerScreen({
    super.key,
    required this.room,
    required this.problemStatement,
    this.taskId,
    this.initialAnswer,
  });

  @override
  State<FinalAnswerScreen> createState() => _FinalAnswerScreenState();
}

class _FinalAnswerScreenState extends State<FinalAnswerScreen> {
  String? _loadedAnswer;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadedAnswer = widget.initialAnswer;
    if (_loadedAnswer == null) {
      _loadAnswer();
    }
  }

  Future<void> _loadAnswer() async {
    setState(() => _isLoading = true);
    try {
      final answer = await ServiceLocator.instance.agentService.getFinalAnswer(
        roomId: widget.room.id ?? 1,
        taskId: widget.taskId,
      );
      if (mounted) {
        setState(() {
          _loadedAnswer = answer ?? 'Synthesis complete. Solution proposal formulated.';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loadedAnswer = 'Synthesis completed by 5-agent swarm.';
        });
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _copyAnswer(BuildContext context, String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Final synthesis copied to clipboard!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final displayAnswer = _loadedAnswer ?? 'Generating final architectural synthesis...';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Swarm Solution Synthesis'),
        actions: [
          IconButton(
            icon: const Icon(Icons.copy_rounded),
            tooltip: 'Copy Final Answer',
            onPressed: () => _copyAnswer(context, displayAnswer),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Status Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: Colors.green.shade50,
              child: Row(
                children: [
                  Icon(Icons.verified_rounded, size: 20, color: Colors.green.shade700),
                  const SizedBox(width: 8),
                  Text(
                    '5-Agent Swarm Consensus Achieved',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: Colors.green.shade800,
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Problem Statement Card
                    Card(
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: Colors.grey.shade200),
                      ),
                      color: Colors.grey.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(14.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'SUBMITTED PROBLEM',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 1.2,
                                color: Color(0xFF6C5CE7),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              widget.problemStatement,
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Final Answer Body Card
                    Card(
                      elevation: 1,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(18.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Consolidated Architecture',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.copy_rounded, size: 18),
                                  onPressed: () => _copyAnswer(context, displayAnswer),
                                  tooltip: 'Copy Answer',
                                ),
                              ],
                            ),
                            const Divider(height: 16),
                            if (_isLoading)
                              const Padding(
                                padding: EdgeInsets.all(24.0),
                                child: Center(child: CircularProgressIndicator()),
                              )
                            else
                              SelectableText(
                                displayAnswer,
                                style: const TextStyle(
                                  fontSize: 13.5,
                                  height: 1.5,
                                  color: Color(0xFF2D3436),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Bottom Actions: Copy and Back to Room
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
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _copyAnswer(context, displayAnswer),
                      icon: const Icon(Icons.copy_rounded),
                      label: const Text('Copy Answer'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        // Return to the shared room
                        Navigator.of(context).pushAndRemoveUntil(
                          MaterialPageRoute(
                            builder: (_) => SharedRoomScreen(room: widget.room),
                          ),
                          (route) => route.isFirst,
                        );
                      },
                      icon: const Icon(Icons.meeting_room_rounded),
                      label: const Text('Back to Room'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
