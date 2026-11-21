import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/main.dart';
import 'package:flutter_app/screens/create_room_screen.dart';
import 'package:flutter_app/screens/join_room_screen.dart';
import 'package:flutter_app/screens/shared_room_screen.dart';
import 'package:flutter_app/screens/problem_submission_screen.dart';
import 'package:flutter_app/screens/agent_dashboard_screen.dart';
import 'package:flutter_app/screens/final_answer_screen.dart';

void main() {
  testWidgets('Complete Navigation Flow through all 7 screens', (WidgetTester tester) async {
    // 1. Home Screen
    await tester.pumpWidget(const SangamXApp());
    expect(find.text('SangamX'), findsOneWidget);
    expect(find.text('Create Room'), findsOneWidget);
    expect(find.text('Join Room'), findsOneWidget);

    // 2. Navigate to Create Room
    await tester.tap(find.text('Create Room'));
    await tester.pumpAndSettle();
    expect(find.byType(CreateRoomScreen), findsOneWidget);
    expect(find.text('Copy Code'), findsOneWidget);

    // Scroll to and Enter Shared Room
    final enterButton = find.text('Enter Shared Room');
    await tester.ensureVisible(enterButton);
    await tester.tap(enterButton);
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();

    // 4. Shared Room
    expect(find.byType(SharedRoomScreen), findsOneWidget);
    expect(find.text('Submit Problem Statement'), findsOneWidget);
    expect(find.textContaining('Active Participants'), findsWidgets);

    // 5. Navigate to Problem Submission
    await tester.tap(find.text('Submit Problem Statement'));
    await tester.pumpAndSettle();
    expect(find.byType(ProblemSubmissionScreen), findsOneWidget);
    expect(find.text('Submit to 5-Agent Swarm'), findsOneWidget);

    // Fill problem statement using quick sample prompt
    final sampleFinder = find.byIcon(Icons.bolt_rounded).first;
    await tester.ensureVisible(sampleFinder);
    await tester.tap(sampleFinder);
    await tester.pumpAndSettle();

    // Scroll to and Submit to Swarm
    final submitButton = find.text('Submit to 5-Agent Swarm');
    await tester.ensureVisible(submitButton);
    await tester.tap(submitButton);
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();

    // 6. Five-Agent Dashboard
    expect(find.byType(AgentDashboardScreen), findsOneWidget);
    expect(find.text('Planner Agent'), findsOneWidget);
    expect(find.text('Researcher Agent'), findsOneWidget);

    await tester.scrollUntilVisible(find.text('Technical Analyst'), 100);
    expect(find.text('Technical Analyst'), findsOneWidget);

    await tester.scrollUntilVisible(find.text('Critic Agent'), 100);
    expect(find.text('Critic Agent'), findsOneWidget);

    await tester.scrollUntilVisible(find.text('Synthesizer Agent'), 100);
    expect(find.text('Synthesizer Agent'), findsOneWidget);

    // Scroll back to top to access controls
    final failButton = find.text('Test Fail State');
    await tester.ensureVisible(failButton);
    await tester.tap(failButton);
    await tester.pump();
    await tester.scrollUntilVisible(find.text('FAILED'), -100);
    expect(find.text('FAILED'), findsOneWidget);

    // 7. Navigate to Final Answer
    await tester.tap(find.text('Preview Final Answer (Fast Path)'));
    await tester.pumpAndSettle();
    expect(find.byType(FinalAnswerScreen), findsOneWidget);
    expect(find.text('Consolidated Architecture'), findsOneWidget);
    expect(find.text('Copy Answer'), findsOneWidget);
    expect(find.text('Back to Room'), findsOneWidget);

    // Back to Room
    await tester.tap(find.text('Back to Room'));
    await tester.pumpAndSettle();
    expect(find.byType(SharedRoomScreen), findsOneWidget);
  });

  testWidgets('Join Room validates error and joins valid room', (WidgetTester tester) async {
    await tester.pumpWidget(const SangamXApp());
    await tester.tap(find.text('Join Room'));
    await tester.pumpAndSettle();

    expect(find.byType(JoinRoomScreen), findsOneWidget);

    // Tap Unknown error test chip
    await tester.tap(find.text('UNKNOWN-99 (Test Error)'));
    await tester.pump();
    await tester.tap(find.text('Join Shared Room'));
    await tester.pumpAndSettle(const Duration(milliseconds: 400));
    expect(find.textContaining("Room 'UNKNOWN-99' does not exist"), findsOneWidget);

    // Tap Valid room chip
    await tester.tap(find.text('SANGAM-7429 (Valid)'));
    await tester.pump();
    await tester.tap(find.text('Join Shared Room'));
    await tester.pumpAndSettle(const Duration(milliseconds: 600));
    expect(find.byType(SharedRoomScreen), findsOneWidget);
  });
}
