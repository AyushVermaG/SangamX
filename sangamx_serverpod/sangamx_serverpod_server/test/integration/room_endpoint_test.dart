import 'package:test/test.dart';
import 'test_tools/serverpod_test_tools.dart';

void main() {
  withServerpod('Given Room endpoint', (sessionBuilder, endpoints) {
    test('createRoom generates unique room code and saves room', () async {
      final room = await endpoints.room.createRoom(sessionBuilder, 'War Room');

      expect(room.id, isNotNull);
      expect(room.name, equals('War Room'));
      expect(room.roomCode, hasLength(6));
      expect(room.isActive, isTrue);
    });

    test('joinRoom adds participants and getRoom returns them', () async {
      final room = await endpoints.room.createRoom(sessionBuilder, 'Sprint Room');

      // First participant joins
      final detail1 = await endpoints.room.joinRoom(
        sessionBuilder,
        room.roomCode,
        'Alice',
      );

      expect(detail1.room.id, equals(room.id));
      expect(detail1.participants, hasLength(1));
      expect(detail1.participants.first.participantName, equals('Alice'));
      expect(detail1.participants.first.isOnline, isTrue);

      // Second participant joins
      final detail2 = await endpoints.room.joinRoom(
        sessionBuilder,
        room.roomCode,
        'Bob',
      );

      expect(detail2.participants, hasLength(2));
      final names = detail2.participants.map((p) => p.participantName).toList();
      expect(names, containsAll(['Alice', 'Bob']));

      // getRoom verifies persisted state
      final getDetail = await endpoints.room.getRoom(sessionBuilder, room.id!);
      expect(getDetail.participants, hasLength(2));
    });

    test('watchRoom receives live updates when participants join', () async {
      final room = await endpoints.room.createRoom(sessionBuilder, 'Live Room');

      final stream = endpoints.room.watchRoom(sessionBuilder, room.id!);

      final expectation = expectLater(
        stream,
        emits(
          predicate((dynamic update) {
            return update.updateType == 'participant_joined' &&
                update.participant?.participantName == 'Charlie';
          }),
        ),
      );

      await endpoints.room.joinRoom(
        sessionBuilder,
        room.roomCode,
        'Charlie',
      );

      await expectation;
    });
  });
}
