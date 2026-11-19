import { useState } from "react";
import EnginePage from "./pages/EnginePage";

function App() {
  const [showEngine, setShowEngine] = useState(false);

  if (showEngine) {
    return <EnginePage />;
  }

  return (
    <div className="min-h-screen bg-[#09090f] flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white">
          Sangam<span className="text-violet-500">X</span>
        </h1>
        <p className="mt-4 text-gray-400">
          Collective Intelligence. One Stronger Outcome.
        </p>
        <button
          className="mt-6 rounded-lg bg-violet-600 px-6 py-3 text-white hover:bg-violet-700"
          onClick={() => setShowEngine(true)}
        >
          Get Started
        </button>
      </div>
    </div>
  );
}

export default App;
