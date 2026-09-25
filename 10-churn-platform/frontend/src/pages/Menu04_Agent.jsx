import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Clock, Terminal } from "lucide-react";

const PRESET_QUERIES = [
  "Evaluate Store Critical: predict churn probability using the ML model and suggest retention SOP.",
  "What are the target accounts and which one is at highest churn risk?",
  "Calculate churn probability for 50 txs, 2 active days, and 28 inactive days.",
];

export default function Menu04_Agent({ activeCustomer }) {
  const { getHeaders, config } = useSettings();
  const [query, setQuery] = useState(PRESET_QUERIES[0]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRunAgent = async (overrideQuery = null) => {
    const q = overrideQuery || query;
    setLoading(true);
    try {
      const res = await churnApi.chatTier04({ query: q }, getHeaders());
      setResult(res);
    } catch (e) {
      alert("Agent execution failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header section */}
      <div className="border-b border-neutral-800 pb-5">
        <div>
          <h1 className="text-base font-semibold text-neutral-100 tracking-tight">
            04. Autonomous Agent (Tool Calling)
          </h1>
          <p className="text-xs text-neutral-400 mt-1 max-w-xl leading-relaxed">
            LangChain ReAct agent equipped with dynamic tool calling. The model decides which tools to invoke: querying merchant databases, triggering ML models, and matching company SOP playbooks.
          </p>
        </div>

        {/* Input bar */}
        <div className="mt-4 flex gap-2.5">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRunAgent()}
            placeholder="Instruct the agent or ask about account retention..."
            className="flex-1 rounded-md border border-neutral-800 bg-[#121416] px-3.5 py-2 text-xs text-neutral-200 placeholder-neutral-500 focus:border-neutral-500 focus:outline-none"
          />
          <button
            onClick={() => handleRunAgent()}
            disabled={loading}
            className="flex items-center gap-2 rounded-md bg-neutral-100 hover:bg-white text-neutral-950 px-4 py-2 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {loading ? "Reasoning..." : "Execute"}
          </button>
        </div>

        {/* Presets */}
        <div className="mt-2.5 flex flex-wrap gap-2 items-center">
          <span className="text-[11px] text-neutral-500">Query presets:</span>
          {PRESET_QUERIES.map((pq, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(pq);
                handleRunAgent(pq);
              }}
              className="text-[11px] text-neutral-400 hover:text-neutral-200 bg-[#121416] px-2.5 py-1 rounded border border-neutral-800 hover:border-neutral-700 transition truncate max-w-xs font-mono"
            >
              {pq}
            </button>
          ))}
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          {/* Tool Timeline */}
          {result.tool_timeline && result.tool_timeline.length > 0 && (
            <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-neutral-800">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5 text-neutral-400" />
                  Tool Execution Sequence ({result.total_tools_called} calls)
                </span>
                <span className="text-[10px] font-mono text-neutral-400 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {result.latency_ms}ms
                </span>
              </div>

              <div className="space-y-2.5">
                {result.tool_timeline.map((step, idx) => (
                  <div key={idx} className="p-3 rounded border border-neutral-800/80 bg-[#0c0d0e] font-mono text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-neutral-300">
                      <span className="flex items-center gap-2">
                        <span className="text-neutral-500">[{idx + 1}]</span>
                        <strong className="text-neutral-200">{step.tool}</strong>
                      </span>
                      <span className="text-[10px] text-neutral-500">Iteration {step.turn}</span>
                    </div>

                    <div className="text-[11px] text-neutral-400 truncate">
                      <span className="text-neutral-500">Input:</span> {JSON.stringify(step.arguments)}
                    </div>

                    <div className="text-[11px] text-neutral-300 bg-[#141618] p-2 rounded border border-neutral-800/80 overflow-x-auto">
                      <span className="text-neutral-500">Result:</span> {step.observation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Final Agent Answer */}
          <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4 space-y-3">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block border-b border-neutral-800 pb-2">
              Agent Synthesis Response
            </span>
            <div className="p-3.5 rounded border border-neutral-800/80 bg-[#0c0d0e] text-xs text-neutral-200 whitespace-pre-wrap leading-relaxed font-sans">
              {result.final_answer}
            </div>
            <div className="flex justify-between text-[11px] font-mono text-neutral-500 pt-1">
              <span>Tokens: {result.token_usage?.total_tokens || 0} cumulative</span>
              <span>Tools executed: {result.total_tools_called}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
