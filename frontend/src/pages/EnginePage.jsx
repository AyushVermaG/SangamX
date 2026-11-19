import { useState, useCallback, useEffect, useRef } from "react";
import QueryInput from "../components/QueryInput";
import AgentTrace from "../components/AgentTrace";
import FinalAnswer from "../components/FinalAnswer";
import { submitQuery, streamTaskEvents, getTaskStatus } from "../api/engineApi";

export default function EnginePage() {
  const [query, setQuery]           = useState("");
  const [taskId, setTaskId]         = useState(null);
  const [status, setStatus]         = useState("idle"); // idle | queued | running | done | error
  const [events, setEvents]         = useState([]);
  const [finalAnswer, setFinalAnswer] = useState(null);
  const [error, setError]           = useState(null);
  const [isLoading, setIsLoading]   = useState(false);

  const cleanupRef = useRef(null);

  // Cleanup SSE on unmount
  useEffect(() => () => cleanupRef.current?.(), []);

  const handleSubmit = useCallback(async (q) => {
    setQuery(q);
    setError(null);
    setEvents([]);
    setFinalAnswer(null);
    setIsLoading(true);
    setStatus("queued");

    let newTaskId;
    try {
      const res = await submitQuery(q);
      newTaskId = res.task_id;
      setTaskId(newTaskId);
      setStatus("running");
    } catch (err) {
      setError(err.message ?? "Failed to submit query.");
      setIsLoading(false);
      setStatus("error");
      return;
    }

    // Start streaming
    const cleanup = streamTaskEvents(
      newTaskId,
      // onEvent
      (ev) => {
        setEvents((prev) => [...prev, ev]);
        // Pick up full final answer from the SSE event (backend sends data.content)
        if (ev.event === "final_answer" && ev.data?.content) {
          setFinalAnswer(ev.data.content);
        }
      },
      // onDone — also fetch status in case final_answer missed via SSE
      async () => {
        setIsLoading(false);
        setStatus("done");
        try {
          const st = await getTaskStatus(newTaskId);
          if (st.final_answer) setFinalAnswer((prev) => prev ?? st.final_answer);
        } catch {/* best-effort */}
      },
      // onError
      (errMsg) => {
        setError(errMsg);
        setIsLoading(false);
        setStatus("error");
      }
    );
    cleanupRef.current = cleanup;
  }, []);

  const handleReset = () => {
    cleanupRef.current?.();
    cleanupRef.current = null;
    setQuery("");
    setTaskId(null);
    setStatus("idle");
    setEvents([]);
    setFinalAnswer(null);
    setError(null);
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#09090f] text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-violet-900/30 px-6 py-4 flex items-center justify-between">
        <span className="text-xl font-bold">
          Sangam<span className="text-violet-500">X</span>
        </span>
        <button
          onClick={handleReset}
          className="text-sm text-gray-400 hover:text-white transition rounded-lg border border-violet-900/40 px-4 py-1.5 hover:border-violet-600"
        >
          New Query
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center px-4 py-10 gap-8 w-full max-w-3xl mx-auto">
        {/* Tagline */}
        <div className="text-center">
          <h1 className="text-2xl font-bold">Collective Intelligence.</h1>
          <p className="text-gray-400 text-sm mt-1">
            Your query is researched, analysed, critiqued and synthesised by a multi-agent team.
          </p>
        </div>

        {/* Query input */}
        <div className="w-full">
          <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {/* Status badge */}
        {taskId && (
          <div className="w-full flex items-center gap-2 text-xs text-gray-500">
            <span className="font-mono bg-white/5 rounded px-2 py-0.5">
              task: {taskId}
            </span>
            <span
              className={
                status === "done"
                  ? "text-emerald-400"
                  : status === "error"
                  ? "text-red-400"
                  : "text-violet-400"
              }
            >
              {status}
            </span>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="w-full rounded-xl border border-red-800/50 bg-red-950/30 px-5 py-3 text-red-300 text-sm">
            <span className="font-semibold">Error: </span>{error}
          </div>
        )}

        {/* Agent trace */}
        {events.length > 0 && (
          <div className="w-full">
            <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Agent Activity</p>
            <AgentTrace events={events} />
          </div>
        )}

        {/* Final answer */}
        <div className="w-full">
          <FinalAnswer answer={finalAnswer} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
