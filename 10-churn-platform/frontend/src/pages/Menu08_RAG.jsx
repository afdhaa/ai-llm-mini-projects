import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Ticket, AlertCircle } from "lucide-react";

export default function Menu08_RAG({ activeCustomer }) {
  const { getHeaders } = useSettings();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRunRAG = async () => {
    setLoading(true);
    try {
      const res = await churnApi.ragTier08({ customer: activeCustomer }, getHeaders());
      setResult(res);
    } catch (e) {
      alert("RAG evaluation failed: " + e.message);
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
              08. Contextual Support RAG (Hybrid Synthesis)
            </h1>
            <p className="text-xs text-neutral-400 mt-1 max-w-xl leading-relaxed">
              Synthesizes quantitative ML churn probabilities with unstructured customer support tickets. Diagnoses the genuine operational root cause and overrides tone-deaf standard discount vouchers.
            </p>
          </div>
          <button
            onClick={handleRunRAG}
            disabled={loading}
            className="flex items-center gap-2 rounded-md bg-neutral-100 hover:bg-white text-neutral-950 px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {loading ? "Diagnosing..." : `Diagnose ${activeCustomer}`}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          {/* Top Contrast Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Generic SOP */}
            <div className="p-4 rounded-lg border border-neutral-800 bg-[#121416] space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                  Generic Playbook SOP
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-800 text-neutral-300">
                  {result.tailored_intervention?.is_sop_adequate ? "ADEQUATE" : "OVERRIDDEN"}
                </span>
              </div>
              <p className="text-xs text-neutral-300 font-medium">Default Incentive: {result.generic_sop?.incentive}</p>
              <ul className="text-xs text-neutral-400 space-y-1 list-disc list-inside">
                {result.generic_sop?.actions.map((act, i) => (
                  <li key={i}>{act}</li>
                ))}
              </ul>
              <div className="text-[11px] text-neutral-500 pt-2 border-t border-neutral-800 font-mono">
                Generic guidance ignores infrastructure failure context.
              </div>
            </div>

            {/* Context-Aware Action */}
            <div className="p-4 rounded-lg border border-neutral-800 bg-[#121416] space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                  Tailored Retention Plan
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-800 text-neutral-200 font-semibold">
                  {result.tailored_intervention?.primary_root_cause}
                </span>
              </div>
              <p className="text-xs text-neutral-200 leading-relaxed">{result.tailored_intervention?.override_justification}</p>
              <ul className="text-xs text-neutral-300 space-y-1 list-disc list-inside">
                {result.tailored_intervention?.tailored_action_items.map((act, i) => (
                  <li key={i}>{act}</li>
                ))}
              </ul>
              <div className="text-[11px] text-neutral-400 pt-2 border-t border-neutral-800 font-mono">
                Assigned Owner: <strong className="text-neutral-200">{result.tailored_intervention?.recommended_pic}</strong>
              </div>
            </div>
          </div>

          {/* Retrieved Support Tickets */}
          <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4 space-y-3">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block border-b border-neutral-800 pb-2">
              Retrieved Support Communications ({result.retrieved_tickets?.length || 0} tickets)
            </span>

            {result.retrieved_tickets && result.retrieved_tickets.length > 0 ? (
              <div className="space-y-2">
                {result.retrieved_tickets.map((t, idx) => (
                  <div key={idx} className="p-3 rounded border border-neutral-800/80 bg-[#0c0d0e] text-xs space-y-1 font-mono">
                    <div className="flex justify-between items-center text-neutral-400 text-[11px]">
                      <span className="font-semibold text-neutral-200">[{t.ticket_id}] {t.subject}</span>
                      <span className="text-neutral-500">{t.channel} | {t.timestamp}</span>
                    </div>
                    <p className="text-neutral-300 font-sans">{t.message}</p>
                    <div className="text-[10px] text-neutral-500 flex justify-between pt-1">
                      <span>Category: {t.category}</span>
                      <span>Status: {t.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-neutral-500">No support tickets found on file for this merchant.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
