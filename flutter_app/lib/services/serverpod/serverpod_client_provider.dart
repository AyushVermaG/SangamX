import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart';
import 'package:serverpod_flutter/serverpod_flutter.dart';

class ServerpodClientProvider {
  static Client? _client;

  /// Retrieves the singleton Serverpod [Client].
  /// Configurable via `--dart-define=SERVERPOD_URL=...`
  /// Defaults to Android emulator host alias `http://10.0.2.2:8080/`.
  static Client getClient({String? serverUrl}) {
    if (_client == null) {
      final url = serverUrl ??
          const String.fromEnvironment(
            'SERVERPOD_URL',
            defaultValue: 'http://10.0.2.2:8080/',
          );
      final normalizedUrl = url.endsWith('/') ? url : '$url/';
      _client = Client(
        normalizedUrl,
      )..connectivityMonitor = FlutterConnectivityMonitor();
    }
    return _client!;
  }

  /// Injects a test client or resets instance.
  static void setClientForTest(Client? client) {
    _client = client;
  }
}
