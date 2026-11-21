import 'package:flutter/material.dart';
import '../services/mock/mock_room_service.dart';
import 'shared_room_screen.dart';

class JoinRoomScreen extends StatefulWidget {
  const JoinRoomScreen({super.key});

  @override
  State<JoinRoomScreen> createState() => _JoinRoomScreenState();
}

class _JoinRoomScreenState extends State<JoinRoomScreen> {
  final _formKey = GlobalKey<FormState>();
  final _codeController = TextEditingController(text: 'SANGAM-7429');
  final _nameController = TextEditingController(text: 'New Collaborator');
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _codeController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _handleJoinRoom() async {
    setState(() {
      _errorMessage = null;
    });

    if (!_formKey.currentState!.validate()) {
      return;
    }

    final code = _codeController.text.trim().toUpperCase();
    final name = _nameController.text.trim();

    setState(() => _isLoading = true);

    try {
      final roomService = MockRoomService();
      final room = await roomService.joinRoom(code: code, participantName: name);

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => SharedRoomScreen(room: room),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Join Room'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 8),
                Text(
                  'Enter Room Code',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Enter the room code shared by the session host.',
                  style: TextStyle(color: Colors.grey.shade600),
                ),
                const SizedBox(height: 24),

                // Room Code Field
                TextFormField(
                  controller: _codeController,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'Room Code',
                    hintText: 'e.g. SANGAM-7429',
                    prefixIcon: Icon(Icons.meeting_room_outlined),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter a room code';
                    }
                    if (value.trim().length < 4) {
                      return 'Room code must be at least 4 characters';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Participant Name Field
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Your Name',
                    hintText: 'e.g. Marcus Vance',
                    prefixIcon: Icon(Icons.person_outline_rounded),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your name';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Demo Quick Fill Chips
                Text(
                  'Known Demo Rooms (Tap to test):',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey.shade700,
                  ),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    ActionChip(
                      label: const Text('SANGAM-7429 (Valid)'),
                      avatar: const Icon(Icons.check_circle_outline, size: 16, color: Colors.green),
                      onPressed: () {
                        setState(() {
                          _codeController.text = 'SANGAM-7429';
                          _errorMessage = null;
                        });
                      },
                    ),
                    ActionChip(
                      label: const Text('DEMO-2026 (Valid)'),
                      avatar: const Icon(Icons.check_circle_outline, size: 16, color: Colors.green),
                      onPressed: () {
                        setState(() {
                          _codeController.text = 'DEMO-2026';
                          _errorMessage = null;
                        });
                      },
                    ),
                    ActionChip(
                      label: const Text('UNKNOWN-99 (Test Error)'),
                      avatar: const Icon(Icons.cancel_outlined, size: 16, color: Colors.orange),
                      onPressed: () {
                        setState(() {
                          _codeController.text = 'UNKNOWN-99';
                          _errorMessage = null;
                        });
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Error Message Display
                if (_errorMessage != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.error_outline_rounded, color: Colors.red.shade700, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _errorMessage!,
                            style: TextStyle(color: Colors.red.shade800, fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                  ),

                const SizedBox(height: 16),

                // Join Button
                ElevatedButton.icon(
                  onPressed: _isLoading ? null : _handleJoinRoom,
                  icon: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Icon(Icons.login_rounded),
                  label: Text(_isLoading ? 'Joining Room...' : 'Join Shared Room'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
