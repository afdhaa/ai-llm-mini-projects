import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import PromptEditor from "../components/PromptEditor";
import FormattedAIResponse from "../components/FormattedAIResponse";
import { useCustomer } from "../context/CustomerContext";

const DEFAULT_HYBRID_PROMPT = `You are a Senior Strategic Account Manager at a leading B2B e-commerce platform.
Write a formal, actionable account retention briefing for account: "{customer}".

STATISTICAL CHURN RISK PROFILE:
- Calibrated Churn Probability: {churn_percentage}
- Machine Learning Risk Assessment: {ml_risk_level}
- Historical Monthly Transactions: {transactions}
- Platform Engagement: {active_days} of past 30 days active ({inactive_days} days dormant)

REQUIREMENTS:
1. Ground your qualitative narrative strictly on the ML calibrated probability of {churn_percentage}. Do not contradict this score.
2. Explain the operational reason for churn based on the engagement gap.
3. Prescribe 3 concrete intervention steps tailored to this risk level.`;

export default function Menu03_Hybrid() {
  const { activeCustomer } = useCustomer();
  const { getHeaders, config } = useSettings();
  const [prompt, setPrompt] = useState(DEFAULT_HYBRID_PROMPT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await churnApi.briefingTier03(
        { customer: activeCustomer, custom_prompt: prompt },
        getHeaders()
      );
      setResult(res);
    } catch (e) {
      alert("Briefing generation failed: " + e.message);
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

      {/* Interactive Prompt Directive Editor */}
      <PromptEditor
        value={prompt}
        onChange={setPrompt}
        onReset={() => setPrompt(DEFAULT_HYBRID_PROMPT)}
        variables={[
          "customer",
          "churn_percentage",
          "ml_risk_level",
          "transactions",
          "active_days",
          "inactive_days",
        ]}
        title="Hybrid Synthesis Prompt Directive (Customizable)"
        subtitle="You can customize instructions, add corporate rubrics, or alter formatting guidelines before invoking LLM synthesis."
      />

      {/* Execution Results */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
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
              Ground truth numerical bounds (Scikit-Learn).
            </div>
          </div>

          {/* Qualitative Synthesis Column - Formatted AI Response */}
          <div className="md:col-span-2">
            <FormattedAIResponse
              content={result.briefing}
              latencyMs={result.latency_ms}
              tokenUsage={result.token_usage}
              modelName={config.model}
              title={`2. Executive Retention Briefing: ${result.customer}`}
            />
          </div>
        </div>
      )}
    </div>
  );
}
