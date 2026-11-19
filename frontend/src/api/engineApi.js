const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Submit a query to the engine.
 * @param {string} query
 * @param {string|null} sessionId
 * @param {object|null} modelConfig
 * @returns {Promise<{task_id: string, status: string}>}
 */
export async function submitQuery(query, sessionId = null, modelConfig = null) {
  const body = { query };
  if (sessionId) body.session_id = sessionId;
  if (modelConfig) body.config = modelConfig;

  const res = await fetch(`${BASE_URL}/api/v1/engine/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Engine run failed (${res.status}): ${text}`);
  }

  return res.json();
}

/**
 * Poll the task status.
 * @param {string} taskId
 * @returns {Promise<{task_id: string, status: string, final_answer: string|null, error: string|null, events_count: number}>}
 */
export async function getTaskStatus(taskId) {
  const res = await fetch(`${BASE_URL}/api/v1/engine/status/${taskId}`);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Status fetch failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Open an SSE stream for a task.
 *
 * The backend emits *named* SSE events (e.g. `event: agent_start\ndata: {...}`).
 * We therefore listen to each event type explicitly instead of using `onmessage`
 * (which only fires for unnamed `event: message` frames).
 *
 * @param {string} taskId
 * @param {(event: object) => void} onEvent  - called for every SSE frame
 * @param {() => void} onDone               - called when stream ends cleanly
 * @param {(err: string) => void} onError    - called on stream error
 * @returns {() => void} cleanup function to close the stream
 */
export function streamTaskEvents(taskId, onEvent, onDone, onError) {
  const url = `${BASE_URL}/api/v1/engine/stream/${taskId}`;
  const es = new EventSource(url);

  const EVENT_TYPES = [
    "agent_start",
    "agent_done",
    "disagreement",
    "revision_start",
    "final_answer",
    "error",
    "done",
    "message", // fallback for unnamed frames
  ];

  function handleFrame(eventType, raw) {
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = { raw };
    }
    // Normalise: ensure the event type field is set
    const ev = typeof parsed === "object" && parsed !== null
      ? { event: eventType, ...parsed }
      : { event: eventType, data: parsed };

    onEvent(ev);

    if (eventType === "done") {
      es.close();
      onDone();
    } else if (eventType === "error") {
      es.close();
      onError(ev.data?.message ?? parsed?.message ?? "An error occurred in the engine.");
    }
  }

  EVENT_TYPES.forEach((type) => {
    es.addEventListener(type, (e) => handleFrame(type, e.data));
  });

  es.onerror = () => {
    es.close();
    onError("SSE connection lost.");
  };

  return () => es.close();
}
