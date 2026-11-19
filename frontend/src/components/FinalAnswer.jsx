/**
 * @param {{ answer: string|null, isLoading: boolean }} props
 */
export default function FinalAnswer({ answer, isLoading }) {
  if (!answer && !isLoading) return null;

  return (
    <div className="rounded-xl border border-violet-700/40 bg-white/5 p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-violet-400">
        Final Answer
      </h2>

      {isLoading && !answer ? (
        /* Pulsing skeleton */
        <div className="space-y-2 animate-pulse">
          <div className="h-3 w-full rounded bg-violet-900/40" />
          <div className="h-3 w-5/6 rounded bg-violet-900/40" />
          <div className="h-3 w-4/6 rounded bg-violet-900/40" />
          <div className="h-3 w-3/6 rounded bg-violet-900/40" />
        </div>
      ) : (
        <p className="whitespace-pre-wrap text-gray-200 leading-relaxed text-sm">
          {answer}
        </p>
      )}
    </div>
  );
}
