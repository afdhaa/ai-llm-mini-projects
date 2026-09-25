import React, { useState, useEffect } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import { Scale, Play, ShieldCheck, Check, X } from "lucide-react";

export default function Menu07_Evals() {
  const { getHeaders } = useSettings();
  const [dataset, setDataset] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState("TC-06");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    churnApi.getEvalsDatasetTier07(getHeaders())
      .then((data) => {
        if (data.cases) setDataset(data.cases);
      })
      .catch((err) => console.error("Error loading eval dataset:", err));
  }, []);

  const handleRunBenchmark = async () => {
    setLoading(true);
    try {
      const res = await churnApi.benchmarkTier07({ case_id: selectedCaseId }, getHeaders());
      setResult(res);
    } catch (e) {
      alert("Benchmark run failed: " + e.message);
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
              07. Automated Evals & Benchmarking (LLM-as-a-Judge)
            </h1>
            <p className="text-xs text-neutral-400 mt-1 max-w-xl leading-relaxed">
              Regression testing suite evaluating non-deterministic pipeline outputs against a golden benchmark dataset using deterministic programmatic rules (Pillar 1) and model-graded rubrics (Pillar 2).
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 border border-neutral-800 bg-[#121416] rounded-md px-2.5 py-1 text-xs">
              <span className="text-[11px] text-neutral-400 font-mono">Test Case:</span>
              <select
                value={selectedCaseId}
                onChange={(e) => setSelectedCaseId(e.target.value)}
                className="bg-transparent text-neutral-100 font-mono text-xs focus:outline-none cursor-pointer"
              >
                {dataset.map((c) => (
                  <option key={c.id} value={c.id} className="bg-[#121416] text-neutral-200">
                    {c.id}: {c.category}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleRunBenchmark}
              disabled={loading}
              className="flex items-center gap-2 rounded-md bg-neutral-100 hover:bg-white text-neutral-950 px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              {loading ? "Grading..." : `Grade ${selectedCaseId}`}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <div className="space-y-6">
          {/* Dual Pillar Scorecards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pillar 1: Deterministic Rules */}
            <div className="p-4 rounded-lg border border-neutral-800 bg-[#121416] space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                  Pillar 1: Programmatic Assertions
                </span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
                  result.pillar1_deterministic_rules.deterministic_verdict === "PASS"
                    ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/60"
                    : "bg-red-950/40 text-red-400 border border-red-800/60"
                }`}>
                  {result.pillar1_deterministic_rules.deterministic_verdict}
                </span>
              </div>

              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between p-2 rounded bg-[#0c0d0e] border border-neutral-800/80">
                  <span className="text-neutral-500">Domain Validity:</span>
                  <span className="text-neutral-200">{result.pillar1_deterministic_rules.domain_validity ? "PASSED" : "FAILED"}</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-[#0c0d0e] border border-neutral-800/80">
                  <span className="text-neutral-500">Bounds Calibration [0.0 - 1.0]:</span>
                  <span className="text-neutral-200">{result.pillar1_deterministic_rules.numerical_bounds ? "PASSED" : "FAILED"}</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-[#0c0d0e] border border-neutral-800/80">
                  <span className="text-neutral-500">Zero Code Leakage:</span>
                  <span className="text-neutral-200">{result.pillar1_deterministic_rules.anti_code_leakage ? "PASSED" : "FAILED"}</span>
                </div>
              </div>
            </div>

            {/* Pillar 2: LLM-as-a-Judge */}
            <div className="p-4 rounded-lg border border-neutral-800 bg-[#121416] space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                  Pillar 2: Model-Graded Judge
                </span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
                  result.pillar2_llm_judge.verdict === "PASS"
                    ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/60"
                    : "bg-red-950/40 text-red-400 border border-red-800/60"
                }`}>
                  {result.pillar2_llm_judge.verdict}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono text-center">
                <div className="p-2.5 rounded bg-[#0c0d0e] border border-neutral-800">
                  <span className="text-neutral-500 text-[10px] block uppercase">Faithfulness</span>
                  <div className="text-xl font-bold text-neutral-100 mt-0.5 tabular-nums">
                    {result.pillar2_llm_judge.faithfulness_score} / 5
                  </div>
                </div>
                <div className="p-2.5 rounded bg-[#0c0d0e] border border-neutral-800">
                  <span className="text-neutral-500 text-[10px] block uppercase">SOP Compliance</span>
                  <div className="text-xl font-bold text-neutral-100 mt-0.5 tabular-nums">
                    {result.pillar2_llm_judge.policy_compliance_score} / 5
                  </div>
                </div>
              </div>

              <p className="text-xs text-neutral-300 bg-[#0c0d0e] p-2.5 rounded border border-neutral-800/80 leading-relaxed font-sans">
                {result.pillar2_llm_judge.judge_rationale}
              </p>
            </div>
          </div>

          <div className="p-3 rounded border border-neutral-800 bg-[#0c0d0e] flex justify-between text-xs font-mono text-neutral-500">
            <span className="truncate max-w-lg">Query: "{result.test_case?.query}"</span>
            <span>Latency: {result.latency_ms}ms | Tokens: {result.token_usage?.total_tokens || 0}</span>
          </div>
        </div>
      )}
    </div>
  );
}
