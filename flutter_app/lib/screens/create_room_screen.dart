import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/service_locator.dart';
import 'shared_room_screen.dart';

class CreateRoomScreen extends StatefulWidget {
  const CreateRoomScreen({super.key});

  @override
  State<CreateRoomScreen> createState() => _CreateRoomScreenState();
}

class _CreateRoomScreenState extends State<CreateRoomScreen> {
  late String _generatedCode;
  final TextEditingController _nameController = TextEditingController(text: 'Lead Architect');
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _generatedCode = 'SANGAM-${Random().nextInt(9000) + 1000}';
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  void _copyToClipboard() {
    Clipboard.setData(ClipboardData(text: _generatedCode));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Room code "$_generatedCode" copied to clipboard!'),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _handleEnterRoom() async {
    setState(() => _isLoading = true);
    try {
      final roomService = ServiceLocator.instance.roomService;
      final hostName = _nameController.text.trim().isEmpty ? 'Host User' : _nameController.text.trim();
      final room = await roomService.createRoom(
        name: 'SangamX Collab Room',
        hostName: hostName,
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => SharedRoomScreen(room: room),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error creating room: $e'),
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
    final isMock = ServiceLocator.instance.isMockMode;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Room'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              Text(
                'Generate Room Code',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Share this code with team members so they can join your collaborative session.',
                style: TextStyle(color: Colors.grey.shade600),
              ),
              const SizedBox(height: 24),

              // Room Code Display Card
              Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: const Color(0xFF6C5CE7).withValues(alpha: 0.3), width: 1.5),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      Text(
                        isMock ? 'DEMO ROOM CODE' : 'ROOM CODE',
                        style: const TextStyle(
                          fontSize: 12,
                          letterSpacing: 1.5,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF6C5CE7),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SelectableText(
                        _generatedCode,
                        style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 3,
                          color: Color(0xFF2D3436),
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextButton.icon(
                        onPressed: _copyToClipboard,
                        icon: const Icon(Icons.copy_rounded, size: 18),
                        label: const Text('Copy Code'),
                        style: TextButton.styleFrom(
                          foregroundColor: const Color(0xFF6C5CE7),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Host Name Input
              Text(
                'Your Display Name',
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  hintText: 'e.g. Lead Architect, Alex, Priya',
                  prefixIcon: Icon(Icons.person_outline_rounded),
                ),
              ),
              const SizedBox(height: 16),

              // Demo mode notice (displayed only in mock mode)
              if (isMock) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.amber.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.amber.shade300),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline_rounded, size: 20, color: Colors.amber.shade900),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Demo Mode: Local state simulation enabled. Real-time multi-device sync will connect to backend.',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.amber.shade900,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              const SizedBox(height: 16),

              // Navigate to Shared Room Button
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _handleEnterRoom,
                icon: _isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.arrow_forward_rounded),
                label: Text(_isLoading ? 'Entering Room...' : 'Enter Shared Room'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
