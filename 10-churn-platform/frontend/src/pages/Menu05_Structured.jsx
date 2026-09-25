import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Clock, Code2 } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import { useCustomer } from "../context/CustomerContext";

export default function Menu05_Structured() {
  const { activeCustomer } = useCustomer();
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
      {/* In-Page Store Selector & Parameter Header */}
      <PageStoreHeader showDatasetAction={false} />

      {/* Header section */}
      <div className="border-b border-neutral-200 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
              05. Structured Outputs (Pydantic Contracts)
            </h1>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Eliminates unstructured free-text by enforcing strict Pydantic schemas via function calling. Guarantees deterministic, type-safe JSON contracts for downstream services and database persistence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Mode switch */}
            <div className="flex rounded-md bg-neutral-100 p-1 border border-neutral-200 text-xs">
              <button
                onClick={() => setMode("single")}
                className={`px-3 py-1 rounded transition text-xs font-medium ${
                  mode === "single" ? "bg-white text-neutral-900 shadow-sm" : "text-neutral-500 hover:text-neutral-900"
                }`}
              >
                Single Account
              </button>
              <button
                onClick={() => setMode("batch")}
                className={`px-3 py-1 rounded transition text-xs font-medium ${
                  mode === "batch" ? "bg-white text-neutral-900 shadow-sm" : "text-neutral-500 hover:text-neutral-900"
                }`}
              >
                Batch (All 5)
              </button>
            </div>

            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
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
              <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-3.5 shadow-sm">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                    Validated Contract Schema
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-neutral-100 text-neutral-700">
                    {result.assessment.risk_level}
                  </span>
                </div>

                <div className="text-xs text-neutral-700 leading-relaxed bg-neutral-50 p-3 rounded border border-neutral-200 font-sans">
                  {result.assessment.executive_summary}
                </div>

                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-500 block mb-1.5 font-medium">Key Drivers:</span>
                  <ul className="list-disc list-inside text-xs text-neutral-700 space-y-1 font-mono">
                    {result.assessment.key_churn_drivers.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <span className="text-[11px] font-mono uppercase text-neutral-500 block mb-1.5 font-medium">
                    Prescribed Actions ({result.assessment.prescribed_actions.length}):
                  </span>
                  <div className="space-y-1.5">
                    {result.assessment.prescribed_actions.map((act, i) => (
                      <div key={i} className="p-2.5 rounded bg-neutral-50 border border-neutral-200 text-xs space-y-0.5 font-mono">
                        <div className="flex justify-between items-center text-neutral-800">
                          <span className="font-semibold">[{act.priority}] {act.task}</span>
                          <span className="text-[10px] text-neutral-500">{act.channel}</span>
                        </div>
                        <p className="text-[11px] text-neutral-500 font-sans">Owner: {act.pic}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* JSON Contract Inspector */}
              <div className="rounded-lg border border-neutral-200 bg-white p-4 flex flex-col justify-between shadow-sm">
                <div>
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100">
                    <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 flex items-center gap-1.5">
                      <Code2 className="h-3.5 w-3.5 text-neutral-500" />
                      JSON Serialization
                    </span>
                    <span className="text-[10px] font-mono text-neutral-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {result.latency_ms}ms
                    </span>
                  </div>
                  <pre className="p-3 rounded border border-neutral-200 bg-neutral-50 text-xs font-mono text-neutral-800 whitespace-pre leading-relaxed overflow-x-auto max-h-96">
                    {JSON.stringify(result.assessment, null, 2)}
                  </pre>
                </div>

                <div className="text-[11px] text-neutral-400 pt-3 border-t border-neutral-100 font-mono">
                  Guaranteed Pydantic schema validation.
                </div>
              </div>
            </div>
          )}

          {mode === "batch" && result.assessments && (
            <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-3 shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                  Batch Execution Contracts ({result.total_accounts} Accounts)
                </span>
                <span className="text-[10px] font-mono text-neutral-500">{result.latency_ms}ms</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.assessments.map((acc, i) => (
                  <div key={i} className="p-3.5 rounded border border-neutral-200 bg-neutral-50 space-y-1.5 font-mono">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-neutral-900">{acc.customer}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-200 text-neutral-700">
                        {acc.risk_level}
                      </span>
                    </div>
                    <p className="text-[11px] text-neutral-600 font-sans line-clamp-2">{acc.executive_summary}</p>
                    <span className="text-[10px] text-neutral-400 block pt-1">
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
