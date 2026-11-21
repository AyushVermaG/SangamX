import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/main.dart';
import 'package:flutter_app/screens/create_room_screen.dart';
import 'package:flutter_app/screens/join_room_screen.dart';

void main() {
  testWidgets('SangamX renders Home Screen with branding and buttons', (WidgetTester tester) async {
    await tester.pumpWidget(const SangamXApp());

    expect(find.text('SangamX'), findsOneWidget);
    expect(find.text('Create Room'), findsOneWidget);
    expect(find.text('Join Room'), findsOneWidget);
  });

  testWidgets('Navigates to Create Room screen', (WidgetTester tester) async {
    await tester.pumpWidget(const SangamXApp());

    await tester.tap(find.text('Create Room'));
    await tester.pumpAndSettle();

    expect(find.byType(CreateRoomScreen), findsOneWidget);
    expect(find.text('Generate Room Code'), findsOneWidget);
    expect(find.text('Copy Code'), findsOneWidget);
  });

  testWidgets('Navigates to Join Room screen and validates input', (WidgetTester tester) async {
    await tester.pumpWidget(const SangamXApp());

    await tester.tap(find.text('Join Room'));
    await tester.pumpAndSettle();

    expect(find.byType(JoinRoomScreen), findsOneWidget);
    expect(find.text('Enter Room Code'), findsOneWidget);
  });
}
