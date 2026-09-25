import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Clock } from "lucide-react";

export default function Menu03_Hybrid({ activeCustomer }) {
  const { getHeaders, config } = useSettings();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await churnApi.briefingTier03({ customer: activeCustomer }, getHeaders());
      setResult(res);
    } catch (e) {
      alert("Briefing generation failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header section */}
      <div className="border-b border-neutral-200 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
              03. Hybrid Architecture (ML + LLM)
            </h1>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Combines statistical probability from Scikit-Learn with qualitative explanation from the LLM. The ML model establishes the exact calibrated percentage, and the LLM interprets the operational drivers.
            </p>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex items-center gap-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {loading ? "Generating..." : `Synthesize Briefing for ${activeCustomer}`}
          </button>
        </div>
      </div>

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Statistical Truth Column */}
          <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-3 shadow-sm">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 block border-b border-neutral-100 pb-2">
              1. Statistical ML Truth
            </span>

            <div className="p-3.5 rounded border border-neutral-200 bg-neutral-50 text-center">
              <span className="text-[10px] font-mono uppercase text-neutral-500">Calibrated Churn Prob</span>
              <div className="text-3xl font-mono font-semibold text-neutral-900 my-1 tabular-nums">
                {result.churn_percentage}
              </div>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-neutral-200 text-neutral-700">
                {result.ml_risk_level}
              </span>
            </div>

            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between p-2 rounded bg-neutral-50 border border-neutral-100">
                <span className="text-neutral-500">Transactions:</span>
                <span className="text-neutral-800">{result.transactions}</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-neutral-50 border border-neutral-100">
                <span className="text-neutral-500">Active Days:</span>
                <span className="text-neutral-800">{result.active_days} / 30</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-neutral-50 border border-neutral-100">
                <span className="text-neutral-500">Inactive Days:</span>
                <span className="text-neutral-800">{result.inactive_days} / 30</span>
              </div>
            </div>

            <div className="text-[11px] text-neutral-400 pt-2 border-t border-neutral-100 font-mono">
              Ground truth numerical bounds.
            </div>
          </div>

          {/* Qualitative Synthesis Column */}
          <div className="md:col-span-2 rounded-lg border border-neutral-200 bg-white p-4 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                  2. Executive Briefing (Anchored Narrative)
                </span>
                <span className="text-[10px] font-mono text-neutral-500 flex items-center gap-1">
                  <Clock className="h-3 w-3 text-neutral-400" />
                  {result.latency_ms}ms
                </span>
              </div>
              <div className="p-3 rounded border border-neutral-200 bg-neutral-50/70 text-xs text-neutral-800 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto font-sans">
                {result.briefing}
              </div>
            </div>

            <div className="text-[11px] text-neutral-400 pt-3 border-t border-neutral-100 font-mono flex justify-between">
              <span>Tokens: {result.token_usage?.total_tokens || 0}</span>
              <span>Grounding: 100% anchored on {result.churn_percentage}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
