import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Clock, Terminal } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import FormattedAIResponse from "../components/FormattedAIResponse";
import { useCustomer } from "../context/CustomerContext";
const PRESET_QUERIES = [
  "Evaluate Store Critical: predict churn probability using the ML model and suggest retention SOP.",
  "What are the target accounts and which one is at highest churn risk?",
  "Calculate churn probability for 50 txs, 2 active days, and 28 inactive days.",
];

export default function Menu04_Agent() {
  const { activeCustomer } = useCustomer();
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
      {/* In-Page Store Selector & Parameter Header */}
      <PageStoreHeader showDatasetAction={false} showFinancials={false} showTickets={false} badge="Tabular Signals" />

      {/* Header section */}
      <div className="border-b border-neutral-200 pb-5">
        <div>
          <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
            04. Autonomous Agent (Tool Calling)
          </h1>
          <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
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
            className="flex-1 rounded-md border border-neutral-300 bg-white px-3.5 py-2 text-xs text-neutral-900 placeholder-neutral-400 focus:border-neutral-500 focus:outline-none shadow-sm"
          />
          <button
            onClick={() => handleRunAgent()}
            disabled={loading}
            className="flex items-center gap-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-4 py-2 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
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
              className="text-[11px] text-neutral-600 hover:text-neutral-900 bg-white px-2.5 py-1 rounded border border-neutral-200 hover:border-neutral-300 shadow-sm transition truncate max-w-xs font-mono"
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
            <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-neutral-100">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5 text-neutral-500" />
                  Tool Execution Sequence ({result.total_tools_called} calls)
                </span>
                <span className="text-[10px] font-mono text-neutral-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {result.latency_ms}ms
                </span>
              </div>

              <div className="space-y-2.5">
                {result.tool_timeline.map((step, idx) => (
                  <div key={idx} className="p-3 rounded border border-neutral-200 bg-neutral-50 font-mono text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-neutral-700">
                      <span className="flex items-center gap-2">
                        <span className="text-neutral-400">[{idx + 1}]</span>
                        <strong className="text-neutral-900">{step.tool}</strong>
                      </span>
                      <span className="text-[10px] text-neutral-400">Iteration {step.turn}</span>
                    </div>

                    <div className="text-[11px] text-neutral-500 truncate">
                      <span className="text-neutral-400">Input:</span> {JSON.stringify(step.arguments)}
                    </div>

                    <div className="text-[11px] text-neutral-700 bg-white p-2 rounded border border-neutral-200 overflow-x-auto">
                      <span className="text-neutral-400">Result:</span> {step.observation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Final Agent Answer */}
          <FormattedAIResponse
            content={result.final_answer}
            latencyMs={result.latency_ms}
            tokenUsage={result.token_usage}
            modelName={config.model}
            title="Agent Autonomous Synthesis & Execution Summary"
          />
        </div>
      )}
    </div>
  );
}
