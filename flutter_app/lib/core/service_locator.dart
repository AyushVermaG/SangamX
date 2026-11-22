import '../services/room_service.dart';
import '../services/task_service.dart';
import '../services/agent_service.dart';
import '../services/mock/mock_room_service.dart';
import '../services/mock/mock_task_service.dart';
import '../services/mock/mock_agent_service.dart';
import '../services/serverpod/serverpod_room_service.dart';
import '../services/serverpod/serverpod_task_service.dart';
import '../services/serverpod/serverpod_agent_service.dart';

class ServiceLocator {
  static final ServiceLocator _instance = ServiceLocator._internal();
  static ServiceLocator get instance => _instance;
  ServiceLocator._internal();

  bool _isMockMode = const bool.fromEnvironment('USE_MOCK', defaultValue: true);
  late RoomService _roomService;
  late TaskService _taskService;
  late AgentService _agentService;
  bool _initialized = false;

  bool get isMockMode => _isMockMode;
  RoomService get roomService {
    _ensureInitialized();
    return _roomService;
  }

  TaskService get taskService {
    _ensureInitialized();
    return _taskService;
  }

  AgentService get agentService {
    _ensureInitialized();
    return _agentService;
  }

  void _ensureInitialized() {
    if (!_initialized) {
      init();
    }
  }

  /// Initializes the service container.
  /// If [isMock] is true, injects in-memory mock services.
  /// If [isMock] is false, injects live Serverpod adapters.
  void init({
    bool? isMock,
    RoomService? roomService,
    TaskService? taskService,
    AgentService? agentService,
  }) {
    _isMockMode = isMock ?? const bool.fromEnvironment('USE_MOCK', defaultValue: true);

    if (_isMockMode) {
      _roomService = roomService ?? MockRoomService();
      _taskService = taskService ?? MockTaskService();
      _agentService = agentService ?? MockAgentService();
    } else {
      _roomService = roomService ?? ServerpodRoomService();
      _taskService = taskService ?? ServerpodTaskService();
      _agentService = agentService ?? ServerpodAgentService();
    }
    _initialized = true;
  }
}
