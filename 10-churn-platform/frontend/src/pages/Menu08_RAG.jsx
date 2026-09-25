import React, { useState, useEffect } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play, Layers, MessageSquare, AlertTriangle, CheckCircle2, Ticket } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import PromptEditor from "../components/PromptEditor";

const DEFAULT_RAG_PROMPT = `You are an Enterprise Retention Director synthesizing quantitative ML scores with qualitative customer support signals.

CUSTOMER: {customer}
- ML Churn Probability : {churn_percentage} [{risk_level}]
- Activity Signals      : {transactions} transactions, {active_days} active days, {inactive_days} inactive days

GENERIC PLAYBOOK SOP (Tabular Guidance):
- Prescribed Generic Incentive: {generic_incentive}
- Default Generic Actions: {generic_actions}

UNSTRUCTURED SUPPORT TICKETS & WHATSAPP LOGS (RAG Context):
{tickets_json}

INSTRUCTIONS:
1. Examine the retrieved support tickets to discover the true underlying problem.
2. Determine whether the generic SOP (e.g. offering a discount voucher) is adequate or tone-deaf (e.g. if the customer's webhooks or payouts are broken, a discount damages trust).
3. Return a validated ContextAwareIntervention schema.`;
import { useCustomer } from "../context/CustomerContext";

export default function Menu08_RAG() {
  const { activeCustomer, setActiveCustomer } = useCustomer();
  const { getHeaders } = useSettings();
  const [result, setResult] = useState(null);
  const [prompt, setPrompt] = useState(DEFAULT_RAG_PROMPT);
  const [loading, setLoading] = useState(false);

  // Portfolio matrix state
  const [matrixData, setMatrixData] = useState(null);
  const [matrixLoading, setMatrixLoading] = useState(false);

  const isAll = activeCustomer === "ALL";

  useEffect(() => {
    if (isAll) {
      loadMatrix();
    }
  }, [isAll]);

  const loadMatrix = async () => {
    setMatrixLoading(true);
    try {
      const res = await churnApi.getMatrixTier08(getHeaders());
      setMatrixData(res);
    } catch (e) {
      alert("Matrix loading failed: " + e.message);
    } finally {
      setMatrixLoading(false);
    }
  };

  const handleRunRAG = async () => {
    setLoading(true);
    try {
      const res = await churnApi.ragTier08(
        { customer: activeCustomer, custom_prompt: prompt },
        getHeaders()
      );
      setResult(res);
    } catch (e) {
      alert("RAG evaluation failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* In-Page Store Selector & Parameter Header */}
      <PageStoreHeader showDatasetAction={false} showFinancials={false} showTickets={true} badge="RAG Support Signals" />

      {/* Header section */}
      <div className="border-b border-neutral-200 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
              08. Contextual Support RAG (Hybrid Synthesis)
            </h1>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Synthesizes quantitative ML churn probabilities with unstructured customer support tickets. Diagnoses the genuine operational root cause and overrides tone-deaf standard discount vouchers.
            </p>
          </div>
          {!isAll && (
            <button
              onClick={handleRunRAG}
              disabled={loading}
              className="flex items-center gap-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              {loading ? "Diagnosing..." : `Diagnose ${activeCustomer}`}
            </button>
          )}
        </div>
      </div>
      {/* Interactive Prompt Directive Editor (Single Store Mode) */}
      {!isAll && (
        <PromptEditor
          value={prompt}
          onChange={setPrompt}
          onReset={() => setPrompt(DEFAULT_RAG_PROMPT)}
          variables={[
            "customer",
            "churn_percentage",
            "risk_level",
            "transactions",
            "active_days",
            "inactive_days",
            "generic_incentive",
            "generic_actions",
            "tickets_json",
          ]}
          title="Contextual Support RAG Prompt Directive (Customizable)"
          subtitle="Tune how the LLM evaluates unstructured support tickets versus generic retention playbook SOPs."
        />
      )}


      {/* ALL STORES: Portfolio Intelligence Comparison Matrix */}
      {isAll ? (
        <div className="rounded-lg border border-neutral-200 bg-white p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
            <div>
              <h2 className="text-sm font-semibold text-neutral-900 flex items-center gap-2">
                <Layers className="h-4 w-4 text-neutral-600" />
                Cross-Account Retention Intelligence Matrix
              </h2>
              <p className="text-xs text-neutral-500 mt-0.5">
                Contrasting quantitative ML churn scores against qualitative customer support tickets across all accounts.
              </p>
            </div>

            <button
              onClick={loadMatrix}
              disabled={matrixLoading}
              className="rounded-md bg-neutral-100 hover:bg-neutral-200 border border-neutral-200 text-neutral-800 px-3 py-1.5 text-xs font-medium transition"
            >
              {matrixLoading ? "Loading..." : "Refresh Matrix"}
            </button>
          </div>

          {matrixData && (
            <div className="space-y-3">
              <div className="border border-neutral-200 rounded-lg overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-neutral-50 text-neutral-500 border-b border-neutral-200">
                    <tr>
                      <th className="py-2.5 px-3">Account</th>
                      <th className="py-2.5 px-3">ML Churn Prob</th>
                      <th className="py-2.5 px-3">Generic SOP Incentive</th>
                      <th className="py-2.5 px-3">Tickets (RAG Signals)</th>
                      <th className="py-2.5 px-3">Diagnosed Root Cause</th>
                      <th className="py-2.5 px-3">Tailored Action Strategy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-200 text-neutral-700">
                    {matrixData.matrix.map((row, idx) => (
                      <tr key={idx} className="hover:bg-neutral-50/80">
                        <td className="py-2.5 px-3 font-semibold text-neutral-900 font-sans">
                          <button
                            onClick={() => setActiveCustomer(row.customer)}
                            className="text-left hover:text-blue-600 transition"
                            title="Inspect single account RAG"
                          >
                            {row.customer} →
                          </button>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                            row.ml_risk_level === "HIGH RISK"
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : row.ml_risk_level === "MEDIUM RISK"
                              ? "bg-amber-50 text-amber-800 border border-amber-200"
                              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          }`}>
                            {row.churn_percentage}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-sans text-neutral-600 max-w-xs truncate">
                          {row.generic_sop_incentive}
                        </td>
                        <td className="py-2.5 px-3 font-sans text-neutral-600">
                          {row.ticket_count > 0 ? (
                            <span className="font-mono text-neutral-900 font-medium">
                              {row.ticket_count} tickets
                            </span>
                          ) : (
                            <span className="text-neutral-400">0 tickets</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            !row.is_sop_adequate ? "bg-neutral-900 text-white" : "bg-neutral-100 text-neutral-700"
                          }`}>
                            {row.primary_root_cause}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-sans text-neutral-800 max-w-sm text-[11px] leading-tight">
                          {row.tailored_action_summary}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-between items-center text-[11px] font-mono text-neutral-400 pt-1">
                <span>RAG synthesis eliminates tabular blind spots across the merchant portfolio.</span>
                <span>Click any account to view individual ticket snippets</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* SINGLE STORE: Contrast Cards & Tickets */
        result && (
          <div className="space-y-6">
            {/* Top Contrast Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Generic SOP */}
              <div className="p-4 rounded-lg border border-neutral-200 bg-white space-y-2.5 shadow-sm">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                    Generic Playbook SOP
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-100 text-neutral-600">
                    {result.tailored_intervention?.is_sop_adequate ? "ADEQUATE" : "OVERRIDDEN"}
                  </span>
                </div>
                <p className="text-xs text-neutral-700 font-medium">Default Incentive: {result.generic_sop?.incentive}</p>
                <ul className="text-xs text-neutral-500 space-y-1 list-disc list-inside">
                  {result.generic_sop?.actions.map((act, i) => (
                    <li key={i}>{act}</li>
                  ))}
                </ul>
                <div className="text-[11px] text-neutral-400 pt-2 border-t border-neutral-100 font-mono">
                  Generic guidance ignores infrastructure failure context.
                </div>
              </div>

              {/* Context-Aware Action */}
              <div className="p-4 rounded-lg border border-neutral-200 bg-white space-y-2.5 shadow-sm">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                    Tailored Retention Plan
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-900 text-white font-semibold">
                    {result.tailored_intervention?.primary_root_cause}
                  </span>
                </div>
                <p className="text-xs text-neutral-800 leading-relaxed font-sans">{result.tailored_intervention?.override_justification}</p>
                <ul className="text-xs text-neutral-700 space-y-1 list-disc list-inside font-sans">
                  {result.tailored_intervention?.tailored_action_items.map((act, i) => (
                    <li key={i}>{act}</li>
                  ))}
                </ul>
                <div className="text-[11px] text-neutral-500 pt-2 border-t border-neutral-100 font-mono">
                  Assigned Owner: <strong className="text-neutral-900">{result.tailored_intervention?.recommended_pic}</strong>
                </div>
              </div>
            </div>

            {/* Retrieved Support Tickets */}
            <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-3 shadow-sm">
              <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 block border-b border-neutral-100 pb-2">
                Retrieved Support Communications ({result.retrieved_tickets?.length || 0} tickets)
              </span>

              {result.retrieved_tickets && result.retrieved_tickets.length > 0 ? (
                <div className="space-y-2">
                  {result.retrieved_tickets.map((t, idx) => (
                    <div key={idx} className="p-3 rounded border border-neutral-200 bg-neutral-50/70 text-xs space-y-1 font-mono">
                      <div className="flex justify-between items-center text-neutral-500 text-[11px]">
                        <span className="font-semibold text-neutral-900">[{t.ticket_id}] {t.subject}</span>
                        <span>{t.channel} | {t.timestamp}</span>
                      </div>
                      <p className="text-neutral-700 font-sans">{t.message}</p>
                      <div className="text-[10px] text-neutral-500 flex justify-between pt-1">
                        <span>Category: {t.category}</span>
                        <span>Status: {t.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-neutral-400">No support tickets found on file for this merchant.</p>
              )}
            </div>
          </div>
        )
      )}
    </div>
  );
}
