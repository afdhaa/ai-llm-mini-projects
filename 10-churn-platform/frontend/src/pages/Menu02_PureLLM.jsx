import React, { useState } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Play } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import PromptEditor from "../components/PromptEditor";
import FormattedAIResponse from "../components/FormattedAIResponse";
import { useCustomer } from "../context/CustomerContext";

const DEFAULT_PROMPT = `You are an expert customer retention analyst in an e-commerce platform.
Evaluate the following merchant's account activity and qualitative churn risk:

CUSTOMER: {customer}
- Monthly Transactions: {transactions}
- Active Days (Past 30d): {active_days}
- Inactive Days: {inactive_days}

Provide a concise, professional assessment containing:
1. Qualitative Risk Tier (High / Medium / Low / None)
2. Behavioral Diagnosis (Why are they behaving this way?)
3. Immediate Retention Recommendation`;

export default function Menu02_PureLLM() {
  const { activeCustomer } = useCustomer();
  const { getHeaders, config } = useSettings();
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const res = await churnApi.evaluateTier02(
        { customer: activeCustomer, custom_prompt: prompt },
        getHeaders()
      );
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
              Zero-shot qualitative prompting directly over raw customer activity metrics. Customize the prompt directive below before generating the evaluation.
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

      {/* Interactive Prompt Editor */}
      <PromptEditor
        value={prompt}
        onChange={setPrompt}
        onReset={() => setPrompt(DEFAULT_PROMPT)}
        variables={["customer", "transactions", "active_days", "inactive_days"]}
        title="Zero-Shot Prompt Directive (Customizable)"
        subtitle="You can freely tweak the instructions, add questions, or modify the rubric before executing inference."
      />

      {/* Result Section */}
      {result && (
        <div className="space-y-4">
          <FormattedAIResponse
            content={result.response}
            latencyMs={result.latency_ms}
            tokenUsage={result.token_usage}
            modelName={config.model}
            title={`Qualitative Assessment: ${result.customer}`}
          />
        </div>
      )}
    </div>
  );
}
