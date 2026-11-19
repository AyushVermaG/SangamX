import { useState } from "react";

const MAX_CHARS = 4000;

/**
 * @param {{ onSubmit: (query: string) => void, isLoading: boolean }} props
 */
export default function QueryInput({ onSubmit, isLoading }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || trimmed.length < 1 || isLoading) return;
    onSubmit(trimmed);
  };

  const remaining = MAX_CHARS - query.length;
  const isOverLimit = remaining < 0;
  const canSubmit = query.trim().length >= 1 && !isOverLimit && !isLoading;

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full flex flex-col gap-3"
    >
      <div className="relative">
        <textarea
          className="w-full min-h-[140px] resize-y rounded-xl border border-violet-900/50 bg-white/5 px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-600 transition text-sm leading-relaxed"
          placeholder="Ask anything — your multi-agent team will research, analyse, critique and synthesise the best answer…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          maxLength={MAX_CHARS + 1}
          disabled={isLoading}
        />
        <span
          className={`absolute bottom-2 right-3 text-xs select-none ${
            isOverLimit ? "text-red-400" : remaining < 200 ? "text-yellow-400" : "text-gray-500"
          }`}
        >
          {query.length} / {MAX_CHARS}
        </span>
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        className="self-end rounded-lg bg-violet-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {isLoading ? (
          <>
            <span className="inline-block h-3.5 w-3.5 rounded-full border-2 border-white/40 border-t-white animate-spin" />
            Running…
          </>
        ) : (
          "Run Query"
        )}
      </button>
    </form>
  );
}
