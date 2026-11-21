# SangamX Serverpod 4 Integration Guide

This document describes the verified integration architecture, endpoint APIs, event contracts, database migrations, and client setup instructions for connecting the **Flutter frontend**, **Serverpod 4 collaboration backend**, and the existing **FastAPI AI engine**.

---

## 1. System Architecture

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     Device A (Flutter App)      │       │     Device B (Flutter App)      │
│  - Host: Creates Room (A8B9C0)  │       │  - Joins with Room Code A8B9C0  │
│  - Subscribes: watchTask(roomId)│       │  - Subscribes: watchTask(roomId)│
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 │                                         │
                 │ WebSocket / HTTP (Port 8080)            │
                 ▼                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     Serverpod 4 Collaboration Backend                     │
│  - RoomEndpoint: createRoom, joinRoom, getRoom, watchRoom                 │
│  - TaskEndpoint: submitTask, getTask, getActiveTask, watchTask            │
│  - Message Central: Pub/Sub over room channel ('task_$roomId')            │
│  - Concurrency Guard: DB Transaction preventing duplicate AI execution    │
│  - PostgreSQL Database: Embedded / Docker on port 8090                    │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      │ HTTP POST /api/v1/engine/run
                                      │ SSE  GET  /api/v1/engine/stream/{task_id}
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        FastAPI 5-Agent AI Engine                          │
│  - LangGraph Execution: Planner → Researcher ‖ Analyst → Critic → Synth  │
│  - SSE Stream: agent_start, agent_done, disagreement, final_answer, etc. │
│  - Terminal Events: workflow_completed, workflow_failed, cancelled        │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Serverpod Endpoints & API Contract

### A. RoomEndpoint (`client.room`)
Location: `lib/src/rooms/room_endpoint.dart`

#### 1. `createRoom`
- **Method Signature:** `Future<Room> createRoom(Session session, String name)`
- **Parameters:**
  - `name` (`String`): Human-readable room title (e.g. `"AI Research Room"`).
- **Return Type:** `Room`
  - `id` (`int?`): Database primary key.
  - `name` (`String`): Room title.
  - `roomCode` (`String`): Unique 6-character alphanumeric join code (e.g. `"K3M9PQ"`).
  - `createdAt` (`DateTime`): UTC creation timestamp.
  - `isActive` (`bool`): `true`.

#### 2. `joinRoom`
- **Method Signature:** `Future<RoomDetail> joinRoom(Session session, String roomCode, String participantName)`
- **Parameters:**
  - `roomCode` (`String`): 6-character room code.
  - `participantName` (`String`): Display name of participant.
- **Return Type:** `RoomDetail`
  - `room` (`Room`): Room record.
  - `participants` (`List<RoomParticipant>`): List of active participants with `isOnline: true`.
  - `activeTask` (`SharedTask?`): Currently running or queued task in the room (if any).
- **Real-time Side Effect:** Broadcasts `RoomUpdate(updateType: 'participant_joined', participant: ...)` on channel `'room_$roomId'`.

#### 3. `getRoom`
- **Method Signature:** `Future<RoomDetail> getRoom(Session session, int roomId)`
- **Parameters:**
  - `roomId` (`int`): Primary key of the room.
- **Return Type:** `RoomDetail`: Up-to-date metadata, participant roster, and active task.

#### 4. `watchRoom`
- **Method Signature:** `Stream<RoomUpdate> watchRoom(Session session, int roomId)`
- **Parameters:**
  - `roomId` (`int`): Room to observe.
- **Return Type:** `Stream<RoomUpdate>`
  - `roomId` (`int`)
  - `updateType` (`String`): `'participant_joined'` | `'participant_left'`
  - `participant` (`RoomParticipant?`)
  - `timestamp` (`DateTime`)

---

### B. TaskEndpoint (`client.task`)
Location: `lib/src/tasks/task_endpoint.dart`

#### 1. `submitTask`
- **Method Signature:** `Future<SharedTask> submitTask(Session session, int roomId, String query)`
- **Parameters:**
  - `roomId` (`int`): Room to execute the workflow in.
  - `query` (`String`): User research question / prompt.
- **Return Type:** `SharedTask`
  - `id` (`int?`): Serverpod task ID.
  - `roomId` (`int`): Room ID.
  - `query` (`String`): Cleaned query prompt.
  - `status` (`String`): `'queued'` (initial status).
  - `fastapiTaskId` (`String?`): Null on insert; updated to FastAPI UUID once spawned.
  - `createdAt` (`DateTime`): UTC creation timestamp.
- **Duplicate Execution Prevention:**
  - Executes inside a PostgreSQL `session.db.transaction`.
  - Checks for existing task in `roomId` with `status IN ('queued', 'running')`.
  - Throws `FormatException('A task is already running in room $roomId (Task #X).')` if a conflict exists.
- **Asynchronous Execution:** Launches `FastApiBridgeService.execute` in the background via `unawaited(...)`.

#### 2. `getTask`
- **Method Signature:** `Future<SharedTask?> getTask(Session session, int taskId)`
- **Parameters:**
  - `taskId` (`int`): Task primary key.
- **Return Type:** `SharedTask?` (including `finalAnswer`, `error`, `completedAt`).

#### 3. `getActiveTask`
- **Method Signature:** `Future<SharedTask?> getActiveTask(Session session, int roomId)`
- **Parameters:**
  - `roomId` (`int`): Room to query.
- **Return Type:** `SharedTask?`: Returns active task if `status == 'queued' || status == 'running'`.

#### 4. `watchTask`
- **Method Signature:** `Stream<TaskUpdate> watchTask(Session session, int roomId)`
- **Validation:** Verifies room exists and is active before opening stream; throws `FormatException` otherwise.
- **Return Type:** `Stream<TaskUpdate>` (broadcast stream over channel `'task_$roomId'`).

---

## 3. Real-Time Event Model (`TaskUpdate`)

Each event received by `client.task.watchTask(roomId)` contains:

| Field | Type | Description |
|---|---|---|
| `taskId` | `int` | Serverpod primary key of the task |
| `roomId` | `int` | Room ID associated with the task |
| `status` | `String` | `'running'` \| `'completed'` \| `'failed'` \| `'cancelled'` |
| `event` | `String` | Event discriminator (see table below) |
| `agent` | `String?` | Name of AI agent emitting event (e.g. `'PlannerAgent'`, `'ResearcherAgent'`) |
| `data` | `String?` | JSON-encoded payload containing event attributes |
| `finalAnswer` | `String?` | Available when `event == 'final_answer'` or `'workflow_completed'` |
| `error` | `String?` | Failure error message if `event == 'workflow_failed'` |
| `timestamp` | `DateTime` | UTC event timestamp |

### Event Sequence:
1. `task_started`: Serverpod bridge submitted task to FastAPI; status transitioned to `running`.
2. `agent_start`: An agent begins execution (`PlannerAgent`, `ResearcherAgent`, `AnalystAgent`, `CriticAgent`, `SynthesisAgent`).
3. `agent_done`: An agent completed its step.
4. `disagreement`: Critic detected contradiction between researcher and analyst outputs.
5. `final_answer`: Synthesis agent generated final merged answer.
6. `workflow_completed`: Terminal event indicating successful completion.
7. `workflow_failed`: Terminal event indicating workflow error or unexpected stream disconnect.

---

## 4. FastAPI Bridge Mapping & Failure Guard

- **Endpoint Mapping:**
  - Serverpod forwards `query` and maps `session_id` to `'room_$roomId'` via `POST /api/v1/engine/run`.
  - Serverpod opens SSE stream `GET /api/v1/engine/stream/{task_id}`.
- **Premature Disconnect Guard:**
  - If the FastAPI SSE stream drops or terminates before emitting a terminal event, `FastApiBridgeService` catches the disconnect, marks `SharedTask.status = 'failed'`, records `'FastAPI SSE stream closed unexpectedly before workflow conclusion.'`, and broadcasts `workflow_failed` to Message Central. Tasks are never left indefinitely in `'running'`.

---

## 5. PostgreSQL Database & Migrations

### Database Schema
- **`room`**: `id` (bigserial PK), `name` (text), `roomCode` (text UNIQUE), `createdAt` (timestamp), `isActive` (boolean).
- **`room_participant`**: `id` (bigserial PK), `roomId` (bigint FK -> room.id ON DELETE CASCADE), `participantName` (text), `joinedAt` (timestamp), `isOnline` (boolean).
- **`shared_task`**: `id` (bigserial PK), `roomId` (bigint FK -> room.id ON DELETE CASCADE), `query` (text), `status` (text), `fastapiTaskId` (text NULL), `finalAnswer` (text NULL), `error` (text NULL), `createdAt` (timestamp), `completedAt` (timestamp NULL).

### Migrations List:
1. `20261121210633210`: Core Serverpod tables.
2. `20261121211022791`: `room` and `room_participant` tables.
3. `20261121212443648`: `shared_task` table and foreign key relations.

---

## 6. Flutter Client Integration (for Divyanshu)

### A. Dependency Declaration (`pubspec.yaml`)
In your Flutter project `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  serverpod_flutter: ^4.1.2
  sangamx_serverpod_client:
    path: ../sangamx_serverpod/sangamx_serverpod_client
```

### B. Client Initialization
```dart
import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart';
import 'package:serverpod_flutter/serverpod_flutter.dart';

// Use your host machine's Wi-Fi IP for physical devices (e.g. 'http://192.168.1.50:8080/')
// Use 'http://10.0.2.2:8080/' for Android Emulator
// Use 'http://127.0.0.1:8080/' for iOS Simulator / Desktop
const serverUrl = 'http://192.168.1.50:8080/';

late Client client;

void initServerpodClient() {
  client = Client(
    serverUrl,
  )..connectivityMonitor = FlutterConnectivityMonitor();
}
```

### C. Host: Create Room & Subscribe
```dart
// 1. Create Room
final room = await client.room.createRoom('War Room');
print('Share this 6-character code with teammate: ${room.roomCode}');

// 2. Watch for participant joins
client.room.watchRoom(room.id!).listen((update) {
  if (update.updateType == 'participant_joined') {
    print('${update.participant?.participantName} entered the room!');
  }
});

// 3. Watch for live task AI events
final subscription = client.task.watchTask(room.id!).listen((update) {
  print('[${update.status}] ${update.event} (Agent: ${update.agent})');
  if (update.finalAnswer != null) {
    print('Final Answer: ${update.finalAnswer}');
  }
});
```

### D. Collaborator: Join Room & Submit Task
```dart
// 1. Join room using room code
final detail = await client.room.joinRoom('A8B9C0', 'Divyanshu');
print('Joined room: ${detail.room.name} (ID: ${detail.room.id})');

// 2. Watch task events
client.task.watchTask(detail.room.id!).listen((update) {
  if (update.event == 'agent_start') {
    print('Agent ${update.agent} started...');
  } else if (update.event == 'workflow_completed') {
    print('Synthesized Result: ${update.finalAnswer}');
  }
});

// 3. Submit research query
final task = await client.task.submitTask(
  detail.room.id!,
  'Compare LangGraph with AutoGen for multi-agent workflows',
);
print('Task submitted with ID: ${task.id}');
```

### E. Unsubscribe & Cleanup
```dart
// Always cancel stream subscriptions when leaving room screens
await subscription.cancel();
```

---

## 7. Startup Instructions

### 1. Embedded PostgreSQL Database
In Windows PowerShell (Terminal 1):
```powershell
cd sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
serverpod database start
```
*(Leave running in foreground. Listens on `127.0.0.1:8090`)*

### 2. Apply Database Migrations (Maintenance Mode)
In Windows PowerShell:
```powershell
cd sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
dart run bin/main.dart --role maintenance --apply-migrations
```

### 3. Start FastAPI AI Engine (Port 8000)
In Windows PowerShell (Terminal 2):
```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Start Serverpod Collaboration Server (Port 8080)
In Windows PowerShell (Terminal 3):
```powershell
cd sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
dart run bin/main.dart
```

### 5. Running the Two-Device Demo
1. Ensure both devices and the host machine are connected to the same local network / Wi-Fi.
2. Device 1 (Host) opens Flutter app, taps **Create Room**, enters `"Sprint Planning"`, and sees code `XYZ123`.
3. Device 2 (Collaborator) taps **Join Room**, enters code `XYZ123` and name `"Divyanshu"`.
4. Device 1 immediately shows `"Divyanshu joined the room"`.
5. Device 1 or 2 types a query (e.g. `"Analyze quantum entanglement"`) and taps **Run**.
6. Both devices stream and display agent progress (`PlannerAgent`, `ResearcherAgent`, `AnalystAgent`, `CriticAgent`, `SynthesisAgent`) and final synthesized answer simultaneously in real time.
