import { useEffect, useRef } from "react";

/** Colour palette per agent name (cycles through violet shades + others). */
const AGENT_COLORS = {
  planner:     "bg-violet-700 text-violet-100",
  researcher:  "bg-blue-700 text-blue-100",
  analyst:     "bg-cyan-700 text-cyan-100",
  critic:      "bg-amber-700 text-amber-100",
  synthesizer: "bg-emerald-700 text-emerald-100",
};

function agentColor(agent) {
  if (!agent) return "bg-gray-700 text-gray-200";
  const key = agent.toLowerCase();
  return AGENT_COLORS[key] ?? "bg-purple-800 text-purple-100";
}

/** Human-friendly label for event types. */
function eventLabel(type) {
  switch (type) {
    case "agent_start":      return "▶ started";
    case "agent_done":       return "✔ done";
    case "disagreement":     return "⚠ disagreement";
    case "revision_start":   return "↺ revising";
    case "final_answer":     return "★ final answer";
    case "error":            return "✖ error";
    case "done":             return "✓ complete";
    default:                 return type;
  }
}

/** Extract a brief text summary from an event's data object. */
function dataSummary(data) {
  if (!data || typeof data !== "object") return null;
  if (typeof data.message === "string") return data.message;
  if (typeof data.content === "string") return data.content.slice(0, 120);
  if (typeof data.reason === "string") return data.reason;
  return null;
}

/**
 * @param {{ events: Array<{event: string, agent?: string, data?: object, timestamp?: string}> }} props
 */
export default function AgentTrace({ events }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  if (!events || events.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-gray-500 text-sm">
        Agent activity will appear here…
      </div>
    );
  }

  return (
    <div className="overflow-y-auto max-h-72 rounded-xl border border-violet-900/40 bg-white/5 p-3 space-y-2 text-sm scroll-smooth">
      {events.map((ev, i) => {
        const ts = ev.timestamp
          ? new Date(ev.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
          : null;
        const summary = dataSummary(ev.data);

        return (
          <div key={i} className="flex items-start gap-2">
            {/* Agent badge */}
            <span
              className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${agentColor(ev.agent)}`}
            >
              {ev.agent ?? "sys"}
            </span>

            {/* Event label */}
            <span className="text-gray-300 font-medium">{eventLabel(ev.event)}</span>

            {/* Summary */}
            {summary && (
              <span className="text-gray-500 truncate max-w-xs">{summary}</span>
            )}

            {/* Timestamp */}
            {ts && (
              <span className="ml-auto shrink-0 text-gray-600 text-xs">{ts}</span>
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
