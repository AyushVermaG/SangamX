"""
Engine Adapter for SangamX
===========================

Provides a clean backend adapter layer between FastAPI/SSE infrastructure
and the multi-agent AI engine.

Responsibilities:
- Decouples FastAPI from internal LangGraph execution details.
- Wraps the existing `run_graph(initial_state, internal_queue, model_config)` interface.
- Handles task ID tracking, session propagation, and event routing.
- Consumes events from the internal queue, attaching task IDs and timezone-aware UTC timestamps.
- Ensures every retrieved queue item is acknowledged with task_done(), even if callback fails.
- Detects successful completion or failure from the returned AgentState or raised exceptions.
- Guarantees exactly-once backend terminal event emission:
    - 'workflow_completed' on successful execution.
    - 'workflow_failed' on failed execution.
- Never emits the legacy 'done' event.
- Prevents duplicate 'error' events if an engine node already emitted one.
- Propagates asyncio.CancelledError cleanly without emitting workflow_completed or workflow_failed.
- Cancels and bounds awaiting of the consumer task (5-second deadline) so unresponsive callbacks cannot deadlock the backend; cooperative callbacks terminate immediately.
- Preserves all AI-engine owned files without modification.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from app.config import Settings, get_settings
from app.engine.state import AgentState, ModelConfig

try:
    from app.engine.graph import run_graph
except ImportError:
    run_graph = None  # type: ignore

logger = logging.getLogger(__name__)

# Internal sentinel used to signal the event consumer to cleanly stop
_SENTINEL = object()


class EngineAdapter:
    """
    Adapter between the backend task orchestration layer and the LangGraph engine.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        run_graph_func: Optional[Callable[..., Awaitable[AgentState]]] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._run_graph = run_graph_func
        # Internal reference to the most recent consumer task (used for test lifecycle verification)
        self._last_consumer_task: Optional[asyncio.Task] = None

    @staticmethod
    def _create_initial_state(
        query: str,
        session_id: Optional[str] = None,
    ) -> AgentState:
        """Create a pristine AgentState typed dictionary for a new workflow run."""
        return {
            "query": query,
            "session_id": session_id,
            "plan": None,
            "research_out": None,
            "analyst_out": None,
            "critic_verdict": None,
            "revision_count": 0,
            "final_answer": None,
            "streaming_log": [],
            "error": None,
        }

    async def execute_task(
        self,
        query: str,
        config: Optional[ModelConfig] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_callback: Optional[Callable[[dict[str, Any]], Awaitable[None]]] = None,
        external_queue: Optional[asyncio.Queue] = None,
    ) -> dict[str, Any]:
        """
        Execute an engine workflow run.

        Args:
            query: User's query prompt.
            config: Optional model configuration overrides.
            task_id: Unique identifier for this task run.
            session_id: Optional session identifier.
            event_callback: Async callback invoked for every stream event emitted.
            external_queue: Optional asyncio.Queue receiving raw event dictionaries.

        Returns:
            Dictionary containing final execution results:
            {
                "task_id": str,
                "status": "done" | "error",
                "final_answer": str | None,
                "error": str | None,
                "state": AgentState | None,
            }
        """
        model_config = config or ModelConfig()
        initial_state = self._create_initial_state(query, session_id=session_id or task_id)
        internal_queue: asyncio.Queue = asyncio.Queue()

        error_emitted = False
        terminal_emitted = False

        async def _forward_event(event_dict: dict[str, Any]) -> None:
            nonlocal error_emitted, terminal_emitted
            evt_name = event_dict.get("event", "message")
            if evt_name == "error":
                error_emitted = True
            elif evt_name in ("workflow_completed", "workflow_failed"):
                terminal_emitted = True

            # Attach task_id if provided and not present
            if task_id and not event_dict.get("task_id"):
                event_dict["task_id"] = task_id

            # Ensure timezone-aware UTC ISO-8601 timestamp
            ts = event_dict.get("timestamp")
            if not ts:
                event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
            elif isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                event_dict["timestamp"] = ts.isoformat()

            if event_callback:
                try:
                    await event_callback(event_dict)
                except Exception as cb_err:
                    logger.warning("Event callback raised an error: %s", cb_err)

            if external_queue:
                try:
                    await external_queue.put(event_dict)
                except Exception as q_err:
                    logger.warning("External queue put raised an error: %s", q_err)

        # Background consumer that continuously forwards events from the internal queue
        async def _consumer() -> None:
            while True:
                try:
                    item = await internal_queue.get()
                except asyncio.CancelledError:
                    break

                if item is _SENTINEL:
                    internal_queue.task_done()
                    break

                try:
                    await _forward_event(item)
                except Exception as ex:
                    logger.exception("Error while forwarding event: %s", ex)
                finally:
                    internal_queue.task_done()

        consumer_task = asyncio.create_task(_consumer())
        self._last_consumer_task = consumer_task

        final_state: Optional[AgentState] = None
        task_error: Optional[str] = None
        is_cancelled: bool = False

        run_func = self._run_graph or run_graph
        if run_func is None:
            try:
                from app.engine.graph import run_graph as dynamic_run_graph
                run_func = dynamic_run_graph
            except ImportError as err:
                raise RuntimeError(
                    f"AI Engine dependencies (langgraph) are missing: {err}. Please install backend/requirements.txt"
                ) from err

        try:
            final_state = await run_func(initial_state, internal_queue, model_config)
            # Detect completion or failure from the returned AgentState
            if final_state is None:
                task_error = "Workflow returned no state"
            elif final_state.get("error") and str(final_state.get("error")).strip():
                task_error = str(final_state["error"])
            else:
                answer = final_state.get("final_answer")
                if answer is None or not str(answer).strip():
                    task_error = "Workflow completed without producing a final answer."
        except asyncio.CancelledError:
            is_cancelled = True
            logger.info("Engine task %s received cancellation.", task_id)
            raise
        except Exception as exc:
            logger.exception("Engine execution failed for task %s: %s", task_id, exc)
            task_error = str(exc)
        finally:
            # 1. Put sentinel into internal_queue to signal the consumer to finish if running
            try:
                internal_queue.put_nowait(_SENTINEL)
            except Exception:
                pass

            # 2. Stop and await consumer task to prevent task leak.
            # Normal cooperative callbacks terminate immediately upon cancellation.
            # A 5-second deadline prevents indefinite hangs if a callback ignores cancellation.
            # If the deadline expires, the consumer remains pending in the loop and a warning is logged.
            if not consumer_task.done():
                if is_cancelled:
                    consumer_task.cancel()
                else:
                    try:
                        await asyncio.wait_for(asyncio.shield(consumer_task), timeout=5.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        consumer_task.cancel()

                # Ensure consumer is awaited to completion with a bound to avoid hanging
                loop = asyncio.get_running_loop()
                deadline = loop.time() + 5.0
                while not consumer_task.done():
                    remaining = deadline - loop.time()
                    if remaining <= 0:
                        logger.warning("Consumer task for %s did not terminate within cleanup deadline.", task_id)
                        break
                    try:
                        await asyncio.wait_for(asyncio.shield(consumer_task), timeout=min(remaining, 1.0))
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

            # 3. Drain remaining items in internal_queue
            # (Guarantees no pending events are silently discarded, and queue join does not deadlock)
            while not internal_queue.empty():
                try:
                    item = internal_queue.get_nowait()
                except (asyncio.QueueEmpty, ValueError):
                    break

                try:
                    if item is not _SENTINEL and not is_cancelled:
                        try:
                            await _forward_event(item)
                        except Exception as ex:
                            logger.exception("Error forwarding drained event: %s", ex)
                finally:
                    internal_queue.task_done()

            # 4. Emit exactly one backend terminal event if not cancelled
            if not is_cancelled:
                if task_error:
                    # Failure path
                    # Avoid duplicate error events: only emit "error" if engine didn't already emit one
                    if not error_emitted:
                        await _forward_event({
                            "event": "error",
                            "agent": None,
                            "data": {"message": task_error},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "task_id": task_id,
                        })
                    if not terminal_emitted:
                        terminal_emitted = True
                        await _forward_event({
                            "event": "workflow_failed",
                            "agent": None,
                            "data": {
                                "error": task_error,
                                "message": task_error,
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "task_id": task_id,
                        })
                else:
                    # Successful path
                    if not terminal_emitted:
                        terminal_emitted = True
                        final_answer = final_state.get("final_answer") if final_state else None
                        await _forward_event({
                            "event": "workflow_completed",
                            "agent": None,
                            "data": {
                                "final_answer": final_answer,
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "task_id": task_id,
                        })

        status = "error" if task_error else "done"
        raw_answer = final_state.get("final_answer") if final_state else None
        final_answer = str(raw_answer) if (raw_answer and not task_error) else None

        return {
            "task_id": task_id,
            "status": status,
            "final_answer": final_answer,
            "error": task_error,
            "state": final_state,
        }
