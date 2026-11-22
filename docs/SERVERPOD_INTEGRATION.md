# SangamX Serverpod 4 Integration Guide

This document is the verified integration reference for the **Flutter frontend** (Divyanshu), the **Serverpod 4 collaboration backend**, and the **FastAPI AI engine** (Ayush).

---

## 1. Architecture Overview

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
│  - Message Central: In-memory pub/sub over 'task_$roomId' & 'room_$roomId'│
│  - Concurrency Guard: DB Transaction preventing duplicate task execution  │
│  - PostgreSQL Database: Port 8090                                         │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      │ HTTP POST /api/v1/engine/run
                                      │ SSE  GET  /api/v1/engine/stream/{task_id}
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        FastAPI 5-Agent AI Engine                          │
│  - LangGraph Execution: planner → researcher ‖ analyst → critic → synth   │
│  - SSE Stream: agent_start, agent_done, disagreement, final_answer, etc.  │
│  - Terminal Events: workflow_completed, workflow_failed, cancelled        │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

* **Operating System:** Windows 10/11, macOS, or Linux.
* **Dart SDK:** `^3.12.2` (Verified with Dart `3.14.0` / Flutter SDK at `C:\src\flutter`).
* **Serverpod CLI:** `4.1.2` (`dart pub global activate serverpod_cli 4.1.2`).
* **Python:** `3.11+` or `3.12+` with virtual environment (`backend/.venv`).
* **PostgreSQL:** Serverpod embedded database or PostgreSQL 14+ on port `8090`.

---

## 3. PostgreSQL Setup

Serverpod runs its development database on port `8090` using either its built-in embedded database or Docker.

### Start Embedded PostgreSQL (Windows PowerShell)
In Terminal 1:
```powershell
cd C:\SangamX-serverpod-worktree\sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
serverpod database start
```
* Status verification: Port `8090` is listening and accepting connections.
* Database name: `sangamx_serverpod` (or as configured in `config/development.yaml`).

---

## 4. Serverpod Setup and Migrations

### A. Resolve Dependencies
```powershell
cd C:\SangamX-serverpod-worktree\sangamx_serverpod
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
dart pub get
```

### B. Code Generation (when schema or endpoints change)
From the server directory:
```powershell
cd C:\SangamX-serverpod-worktree\sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
serverpod generate
```
This updates:
* `sangamx_serverpod_server/lib/src/generated/`
* `sangamx_serverpod_client/lib/src/protocol/` (including `client.dart` and `protocol.dart`).

### C. Apply Database Migrations (Maintenance Mode)
```powershell
cd C:\SangamX-serverpod-worktree\sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
dart run bin/main.dart --role maintenance --apply-migrations
```

Existing migrations:
1. `20261121210633210`: Serverpod core infrastructure tables.
2. `20261121211022791`: `room` and `room_participant` tables.
3. `20261121212443648`: `shared_task` table with foreign key indices.

### D. Start Serverpod Collaboration Server (Port 8080)
In Terminal 2:
```powershell
cd C:\SangamX-serverpod-worktree\sangamx_serverpod\sangamx_serverpod_server
$env:PATH = "C:\src\flutter\bin;$env:LOCALAPPDATA\Pub\Cache\bin;$env:PATH"
dart run bin/main.dart
```
* Server starts on `http://0.0.0.0:8080` (HTTP and WebSockets).

---

## 5. FastAPI Setup and Bridge Configuration

### A. Start FastAPI AI Engine (Port 8000)
In Terminal 3:
```powershell
cd C:\SangamX-serverpod-worktree\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### B. Serverpod Bridge Configuration
* **Environment Variable:** `FASTAPI_BASE_URL` (Optional, defaults to `http://127.0.0.1:8000`).
* **Session Mapping:** When submitting a task, Serverpod maps the room to FastAPI via `session_id: 'room_$roomId'`:
  ```json
  POST /api/v1/engine/run
  {
    "query": "<user_query>",
    "session_id": "room_1"
  }
  ```
* **Failure Guard for Interrupted SSE Streams:** If FastAPI's SSE stream closes unexpectedly before emitting `workflow_completed`, `workflow_failed`, or `cancelled`, Serverpod catches the premature closure, updates `SharedTask.status = 'failed'`, records `'FastAPI SSE stream closed unexpectedly before workflow conclusion.'`, and broadcasts `workflow_failed` to `task_$roomId`.

---

## 6. Generated Flutter Client Installation

The client package is located at:
`sangamx_serverpod/sangamx_serverpod_client`

### Flutter `pubspec.yaml` Configuration
Add the local package to your Flutter project:
```yaml
dependencies:
  flutter:
    sdk: flutter
  serverpod_flutter: ^4.1.2
  sangamx_serverpod_client:
    path: ../sangamx_serverpod/sangamx_serverpod_client
```

Run:
```bash
flutter pub get
```

---

## 7. Client Initialization

Import the generated package entrypoint in your Flutter code:

```dart
import 'package:sangamx_serverpod_client/sangamx_serverpod_client.dart';
import 'package:serverpod_flutter/serverpod_flutter.dart';

// Host machine IP for physical test devices on LAN
// Android Emulator: 'http://10.0.2.2:8080/'
// iOS Simulator / Desktop / Web: 'http://127.0.0.1:8080/'
const serverUrl = 'http://192.168.1.50:8080/';

late Client client;

void initServerpodClient() {
  client = Client(
    serverUrl,
  )..connectivityMonitor = FlutterConnectivityMonitor();
}
```

The `client` instance provides direct typed access to:
* `client.room`: Room creation, joining, info, and event streaming.
* `client.task`: Task submission, polling, active task lookup, and event streaming.
* `client.greeting`: Health check endpoint.

---

## 8. Endpoint Reference

### A. RoomEndpoint (`client.room`)

#### 1. `createRoom`
* **Dart Signature:** `Future<Room> createRoom(String name)`
* **Parameters:**
  * `name` (`String`): Room title.
* **Returns:** `Room`
  * `id` (`int?`): Primary key.
  * `name` (`String`): Room title.
  * `roomCode` (`String`): Unique 6-character alphanumeric code (e.g. `'K8M9PQ'`).
  * `createdAt` (`DateTime`): UTC creation timestamp.
  * `isActive` (`bool`): `true`.

#### 2. `joinRoom`
* **Dart Signature:** `Future<RoomDetail> joinRoom(String roomCode, String participantName)`
* **Parameters:**
  * `roomCode` (`String`): 6-character room code.
  * `participantName` (`String`): Display name of participant.
* **Returns:** `RoomDetail`
  * `room` (`Room`): Room metadata.
  * `participants` (`List<RoomParticipant>`): All participants in the room.
  * `activeTask` (`SharedTask?`): Current queued or running task, if one exists.
* **Side Effect:** Broadcasts `RoomUpdate(updateType: 'participant_joined')` to `room_$roomId`.

#### 3. `getRoom`
* **Dart Signature:** `Future<RoomDetail> getRoom(int roomId)`
* **Parameters:**
  * `roomId` (`int`): Room database ID.
* **Returns:** `RoomDetail` (latest room metadata, participant roster, and active task).

#### 4. `watchRoom`
* **Dart Signature:** `Stream<RoomUpdate> watchRoom(int roomId)`
* **Parameters:**
  * `roomId` (`int`): Room database ID.
* **Returns:** `Stream<RoomUpdate>`
  * `roomId` (`int`): Target room.
  * `updateType` (`String`): `'participant_joined'`.
  * `participant` (`RoomParticipant?`): The participant details.
  * `timestamp` (`DateTime`): UTC event time.

---

### B. TaskEndpoint (`client.task`)

#### 1. `submitTask`
* **Dart Signature:** `Future<SharedTask> submitTask(int roomId, String query)`
* **Parameters:**
  * `roomId` (`int`): Target room.
  * `query` (`String`): Research question / prompt.
* **Returns:** `SharedTask`
  * `id` (`int?`): Task database ID.
  * `roomId` (`int`): Room ID.
  * `query` (`String`): Trimmed query text.
  * `status` (`String`): `'queued'`.
  * `createdAt` (`DateTime`): UTC timestamp.
* **Concurrency Check:** Enforces exactly one active task (`'queued'` or `'running'`) per room inside a database transaction. Throws `FormatException` if another task is active.

#### 2. `getTask`
* **Dart Signature:** `Future<SharedTask?> getTask(int taskId)`
* **Parameters:**
  * `taskId` (`int`): Task database ID.
* **Returns:** `SharedTask?` with `finalAnswer`, `error`, `status`, and `completedAt`.

#### 3. `getActiveTask`
* **Dart Signature:** `Future<SharedTask?> getActiveTask(int roomId)`
* **Parameters:**
  * `roomId` (`int`): Target room.
* **Returns:** `SharedTask?` if a task is currently `'queued'` or `'running'`, or `null` if idle.

#### 4. `watchTask`
* **Dart Signature:** `Stream<TaskUpdate> watchTask(int roomId)`
* **Parameters:**
  * `roomId` (`int`): Target room.
* **Returns:** `Stream<TaskUpdate>` (live broadcast stream over channel `'task_$roomId'`).

---

## 9. Real-Time Event Payload Reference

The `TaskUpdate` stream emitted by `client.task.watchTask(roomId)` contains:

| Field | Dart Type | Description |
|---|---|---|
| `taskId` | `int` | Primary key of the `SharedTask` |
| `roomId` | `int` | Room ID |
| `status` | `String` | Task status: `'running'`, `'completed'`, `'failed'`, `'cancelled'` |
| `event` | `String?` | Event name (see table below) |
| `agent` | `String?` | Agent identifier in **exact lower case** (e.g. `'planner'`, `'researcher'`) |
| `data` | `String?` | JSON-encoded payload containing event attributes |
| `finalAnswer` | `String?` | Merged synthesis answer (present on `'final_answer'` and `'workflow_completed'`) |
| `error` | `String?` | Error description if status is `'failed'` |
| `timestamp` | `DateTime` | UTC timestamp |

### Verified Event Types and Agent Identifiers

All agent identifiers from FastAPI are emitted in **exact lowercase**:

| Event Type (`event`) | Emitting Agent (`agent`) | Payload Data (`data`) | Description |
|---|---|---|---|
| `task_started` | `null` | `{}` | Bridge dispatched task to FastAPI |
| `agent_start` | `'planner'` | `{"message": "Planner decomposing query…"}` | Planner node started |
| `agent_done` | `'planner'` | `{"approach": "...", "complexity": "...", "tasks_count": N}` | Planner plan constructed |
| `agent_start` | `'researcher'` | `{"message": "Researcher starting…"}` | Parallel researcher started |
| `agent_start` | `'analyst'` | `{"message": "Analyst starting…"}` | Parallel analyst started |
| `agent_done` | `'researcher'` | `{"preview": "..."}` | Researcher completed |
| `agent_done` | `'analyst'` | `{"preview": "..."}` | Analyst completed |
| `agent_start` | `'critic'` | `{"message": "Critic evaluating outputs…"}` | Critic review started |
| `agent_done` | `'critic'` | `{"agree": true/false, "confidence": float, "reason": "..."}` | Critic verdict rendered |
| `disagreement` | `null` | `{"reason": "...", "confidence": float}` | Emitted when critic detects dispute |
| `revision_start` | `null` | `{"reason": "...", "round": N}` | Revision loop re-executing |
| `agent_start` | `'synthesizer'` | `{"message": "Synthesizer generating final answer…"}` | Synthesis started |
| `final_answer` | `'synthesizer'` | `{"content": "...", "preview": "..."}` | Answer generated |
| `agent_done` | `'synthesizer'` | `{"message": "Done."}` | Synthesizer finished |
| `workflow_completed` | `null` | `{"final_answer": "..."}` | Terminal success event |
| `workflow_failed` | `null` | `{"error": "...", "message": "..."}` | Terminal error event |
| `cancelled` | `null` | `{"message": "Task was cancelled by user"}` | Task cancelled |

---

## 10. Room Participation and Authorization

* **Access Model:** Any client possessing the valid 6-character `roomCode` can call `joinRoom(roomCode, participantName)`.
* **Roster Tracking:** Each participant is stored in `RoomParticipant` with `roomId`, `participantName`, `joinedAt`, and `isOnline: true`.
* **Join Notification:** `joinRoom` broadcasts `RoomUpdate(updateType: 'participant_joined', participant: ...)` over channel `'room_$roomId'`.
* **Departure Behavior (MVP Limitation):**
  * `leaveRoom` is **NOT implemented** in the hackathon MVP.
  * Disconnecting from WebSockets does **NOT** automatically evict participant records or set `isOnline = false`.
  * The event `'participant_left'` is **NOT emitted**. Participants remain listed in `RoomDetail.participants`.

---

## 11. Reconnection and Event History

### How Serverpod Message Central Works
* Serverpod's `session.messages.createStream` is an **in-memory pub/sub broker**.
* It does **NOT** persist historical streaming events or buffer past messages.
* When a Flutter client connects or reconnects to `watchTask` or `watchRoom`, it only receives events published *after* the stream subscription opens.

### State Recovery Strategy for Reconnecting Clients
To recover state upon reconnecting or opening a room screen:
1. **Recover Room & Roster:** Call `client.room.getRoom(roomId)`.
   * Returns `RoomDetail` with the full `Room`, all `RoomParticipant`s, and the current `activeTask`.
2. **Recover Task State & Final Answer:**
   * If `activeTask` is not null, its `id`, `status` (`'queued'`, `'running'`), and `query` are immediately known.
   * To check if a previous task finished while the client was disconnected: call `client.task.getTask(taskId)`. This queries PostgreSQL and retrieves `finalAnswer`, `status`, `error`, and `completedAt`.
3. **Resume Live Stream:** Open `client.task.watchTask(roomId)` to receive any subsequent live progress and the terminal `workflow_completed` event.

---

## 12. Duplicate Execution Prevention

SangamX enforces strict concurrency control to prevent multiple AI agent workflows from running in the same room simultaneously:

1. **Transaction Isolation:** In `task_endpoint.dart`, `submitTask` runs inside:
   ```dart
   await session.db.transaction<SharedTask>((transaction) async { ... });
   ```
2. **Active Task Check:** Queries PostgreSQL for any existing task in `roomId` with `status IN ('queued', 'running')`.
3. **Rejection:** If an active task is found, it throws `FormatException('A task is already running in room $roomId (Task #X).')`.
4. **Single Background Execution:** The background bridge is only triggered after the task row is successfully committed.

---

## 13. Two-Device Testing Instructions

### Step 1: Network & URL Configuration
* Ensure the host PC and both mobile devices are connected to the same local Wi-Fi.
* Find host IP: run `ipconfig` (e.g. `192.168.1.50`).
* In the Flutter app, initialize Serverpod with:
  ```dart
  final client = Client('http://192.168.1.50:8080/')..connectivityMonitor = FlutterConnectivityMonitor();
  ```

### Step 2: Device A (Host Device)
1. Open Flutter app -> Tap **Create Room**.
2. Enter room name `"SangamX Demo"`.
3. The app displays the generated 6-character room code (e.g. `"K7M2PQ"`).
4. Device A subscribes to `client.room.watchRoom(roomId)` and `client.task.watchTask(roomId)`.

### Step 3: Device B (Collaborator Device)
1. Open Flutter app -> Tap **Join Room**.
2. Enter room code `"K7M2PQ"` and participant name `"Divyanshu"`.
3. App calls `client.room.joinRoom('K7M2PQ', 'Divyanshu')`.
4. **Instant Verification:** Device A's screen receives `RoomUpdate('participant_joined')` and immediately shows `"Divyanshu joined the room"`.

### Step 4: Execute Collaborative AI Task
1. From either Device A or Device B, enter research query:
   `"Analyze benefits of edge computing over cloud computing"`
2. Tap **Submit Task**.
3. Both devices immediately receive `TaskUpdate` events over `watchTask`:
   * `planner`: `"Planner decomposing query…"`
   * `researcher` & `analyst`: Concurrent progress
   * `critic`: Evaluates outputs
   * `synthesizer`: Synthesizes final answer
   * `workflow_completed`: Both devices render the identical final answer simultaneously.

---

## 14. Known Limitations

1. **No Participant Departure (`leaveRoom`):** No endpoint or automatic socket lifecycle hook exists to set `isOnline = false` or emit `participant_left`. Roster is append-only in MVP.
2. **Ephemeral Stream Events:** Intermediate agent progress logs are not stored in PostgreSQL. If a client disconnects mid-workflow, it will not see missed intermediate log lines, but it can fetch the final answer via `client.task.getTask(taskId)`.
3. **Single Task per Room:** A room cannot execute concurrent tasks; subsequent submissions must wait until the running task completes or fails.
4. **FastAPI Replay Scope:** FastAPI SSE replay is stored in-memory in `task_store`; restarting the FastAPI process clears in-flight task history.
