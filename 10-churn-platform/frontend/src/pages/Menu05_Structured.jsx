import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Clock, Code2 } from "lucide-react";

export default function Menu05_Structured({ activeCustomer }) {
  const { getHeaders } = useSettings();
  const [mode, setMode] = useState("single");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await churnApi.structuredTier05(
        { customer: activeCustomer, mode },
        getHeaders()
      );
      setResult(res);
    } catch (e) {
      alert("Structured output execution failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header section */}
      <div className="border-b border-neutral-800 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-100 tracking-tight">
              05. Structured Outputs (Pydantic Contracts)
            </h1>
            <p className="text-xs text-neutral-400 mt-1 max-w-xl leading-relaxed">
              Eliminates unstructured free-text by enforcing strict Pydantic schemas via function calling. Guarantees deterministic, type-safe JSON contracts for downstream services and database persistence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Mode switch */}
            <div className="flex rounded-md bg-[#121416] p-1 border border-neutral-800 text-xs">
              <button
                onClick={() => setMode("single")}
                className={`px-3 py-1 rounded transition text-xs font-medium ${
                  mode === "single" ? "bg-neutral-800 text-white" : "text-neutral-400 hover:text-neutral-200"
                }`}
              >
                Single Account
              </button>
              <button
                onClick={() => setMode("batch")}
                className={`px-3 py-1 rounded transition text-xs font-medium ${
                  mode === "batch" ? "bg-neutral-800 text-white" : "text-neutral-400 hover:text-neutral-200"
                }`}
              >
                Batch (All 5)
              </button>
            </div>

            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 rounded-md bg-neutral-100 hover:bg-white text-neutral-950 px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              {loading ? "Validating..." : mode === "single" ? `Run ${activeCustomer}` : "Run Batch"}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          {mode === "single" && result.assessment && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Structured Summary & Action Items */}
              <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4 space-y-3.5">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                    Validated Contract Schema
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-neutral-800 text-neutral-200">
                    {result.assessment.risk_level}
                  </span>
                </div>

                <div className="text-xs text-neutral-300 leading-relaxed bg-[#0c0d0e] p-3 rounded border border-neutral-800">
                  {result.assessment.executive_summary}
                </div>

                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-400 block mb-1.5 font-medium">Key Drivers:</span>
                  <ul className="list-disc list-inside text-xs text-neutral-300 space-y-1 font-mono">
                    {result.assessment.key_churn_drivers.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-400 block mb-1.5 font-medium">
                    Prescribed Actions ({result.assessment.prescribed_actions.length}):
                  </span>
                  <div className="space-y-1.5">
                    {result.assessment.prescribed_actions.map((act, i) => (
                      <div key={i} className="p-2.5 rounded bg-[#0c0d0e] border border-neutral-800 text-xs space-y-0.5 font-mono">
                        <div className="flex justify-between items-center text-neutral-200">
                          <span className="font-semibold">[{act.priority}] {act.task}</span>
                          <span className="text-[10px] text-neutral-400">{act.channel}</span>
                        </div>
                        <p className="text-[11px] text-neutral-400 font-sans">Owner: {act.pic}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* JSON Contract Inspector */}
              <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-800">
                    <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                      <Code2 className="h-3.5 w-3.5 text-neutral-400" />
                      JSON Serialization
                    </span>
                    <span className="text-[10px] font-mono text-neutral-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {result.latency_ms}ms
                    </span>
                  </div>
                  <pre className="p-3 rounded border border-neutral-800/80 bg-[#0c0d0e] text-xs font-mono text-neutral-300 whitespace-pre leading-relaxed overflow-x-auto max-h-96">
                    {JSON.stringify(result.assessment, null, 2)}
                  </pre>
                </div>

                <div className="text-[11px] text-neutral-500 pt-3 border-t border-neutral-800 font-mono">
                  Guaranteed Pydantic schema validation.
                </div>
              </div>
            </div>
          )}

          {mode === "batch" && result.assessments && (
            <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                  Batch Execution Contracts ({result.total_accounts} Accounts)
                </span>
                <span className="text-[10px] font-mono text-neutral-400">{result.latency_ms}ms</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.assessments.map((acc, i) => (
                  <div key={i} className="p-3.5 rounded border border-neutral-800 bg-[#0c0d0e] space-y-1.5 font-mono">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-neutral-100">{acc.customer}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-300">
                        {acc.risk_level}
                      </span>
                    </div>
                    <p className="text-[11px] text-neutral-300 font-sans line-clamp-2">{acc.executive_summary}</p>
                    <span className="text-[10px] text-neutral-500 block pt-1">
                      {acc.prescribed_actions.length} action items attached
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
