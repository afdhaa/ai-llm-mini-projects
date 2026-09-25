import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Clock, FileText } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import { useCustomer } from "../context/CustomerContext";

export default function Menu02_PureLLM() {
  const { activeCustomer } = useCustomer();
  const { getHeaders, config } = useSettings();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const res = await churnApi.evaluateTier02({ customer: activeCustomer }, getHeaders());
      setResult(res);
    } catch (e) {
      alert("Evaluation failed: " + e.message);
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
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
              02. Pure Foundation LLM (Zero-Shot)
            </h1>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Zero-shot qualitative prompting directly over raw customer activity metrics without traditional ML training. Produces readable behavioral narratives, but lacks statistical probability calibration.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleEvaluate}
              disabled={loading}
              className="flex items-center gap-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              {loading ? "Generating..." : `Evaluate ${activeCustomer}`}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Prompt Section */}
          <div className="rounded-lg border border-neutral-200 bg-white p-4 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                  Constructed Prompt
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-600">Zero-Shot</span>
              </div>
              <pre className="p-3 rounded border border-neutral-200 bg-neutral-50/70 text-xs font-mono text-neutral-800 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
                {result.prompt}
              </pre>
            </div>
            <div className="text-[11px] text-neutral-400 pt-3 border-t border-neutral-100 font-mono">
              Raw metrics injected directly into prompt template.
            </div>
          </div>

          {/* Model Response */}
          <div className="rounded-lg border border-neutral-200 bg-white p-4 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                  LLM Qualitative Output
                </span>
                <span className="text-[10px] font-mono text-neutral-500 flex items-center gap-1">
                  <Clock className="h-3 w-3 text-neutral-400" />
                  {result.latency_ms}ms
                </span>
              </div>
              <div className="p-3 rounded border border-neutral-200 bg-neutral-50/70 text-xs text-neutral-800 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto font-sans">
                {result.response}
              </div>
            </div>

            <div className="text-[11px] text-neutral-400 pt-3 border-t border-neutral-100 font-mono flex justify-between">
              <span>Tokens: {result.token_usage?.total_tokens || 0}</span>
              <span>Model: {config.model}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
