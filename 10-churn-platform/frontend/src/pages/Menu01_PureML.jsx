import React, { useState, useEffect } from "react";
import { churnApi } from "../services/api";
import { Play, Database, Clock } from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import { useCustomer } from "../context/CustomerContext";

export default function Menu01_PureML() {
  const { targets, activeCustomer } = useCustomer();
  const [transactions, setTransactions] = useState(45);
  const [activeDays, setActiveDays] = useState(5);
  const [inactiveDays, setInactiveDays] = useState(30);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dataset, setDataset] = useState(null);
  const [showDataset, setShowDataset] = useState(false);

  useEffect(() => {
    const target = targets.find((t) => t.customer.toLowerCase() === activeCustomer?.toLowerCase());
    if (target) {
      setTransactions(target.transactions);
      setActiveDays(target.active_days);
      setInactiveDays(target.inactive_days);
    }
  }, [activeCustomer, targets]);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const res = await churnApi.predictTier01({
        transactions,
        active_days: activeDays,
        inactive_days: inactiveDays,
      });
      setPrediction(res);
    } catch (e) {
      alert("Prediction error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDataset = async () => {
    if (dataset) {
      setShowDataset(!showDataset);
      return;
    }
    try {
      const res = await churnApi.getDatasetTier01();
      setDataset(res.records);
      setShowDataset(true);
    } catch (e) {
      alert("Error loading dataset: " + e.message);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* In-Page Store Selector & Parameter Header */}
      <PageStoreHeader showDatasetAction={true} />

      {/* Header section */}
      <div className="border-b border-neutral-200 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
              01. Baseline Machine Learning
            </h1>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Standard tabular Scikit-Learn pipeline (StandardScaler + LogisticRegression). Calculates calibrated probabilities deterministically on CPU in sub-millisecond time.
            </p>
          </div>
          <button
            onClick={loadDataset}
            className="flex items-center gap-1.5 rounded-md border border-neutral-200 bg-white hover:bg-neutral-50 px-3 py-1.5 text-xs font-medium text-neutral-700 shadow-sm transition"
          >
            <Database className="h-3.5 w-3.5 text-neutral-500" />
            {showDataset ? "Hide Dataset" : "Inspect Dataset"}
          </button>
        </div>
      </div>

      {/* Dataset Drawer */}
      {showDataset && dataset && (
        <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-neutral-500">data/customers.csv (First 15 records)</span>
            <span className="text-[11px] font-mono text-neutral-400">{dataset.length} total rows</span>
          </div>
          <div className="max-h-52 overflow-y-auto border border-neutral-200 rounded">
            <table className="w-full text-left text-xs font-mono">
              <thead className="border-b border-neutral-200 bg-neutral-50 text-neutral-600 sticky top-0">
                <tr>
                  <th className="py-1.5 px-3">Customer</th>
                  <th className="py-1.5 px-3">Transactions</th>
                  <th className="py-1.5 px-3">Active Days</th>
                  <th className="py-1.5 px-3">Inactive Days</th>
                  <th className="py-1.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 text-neutral-700">
                {dataset.slice(0, 15).map((row, i) => (
                  <tr key={i} className="hover:bg-neutral-50/80">
                    <td className="py-1 px-3 text-neutral-900 font-sans font-medium">{row.customer}</td>
                    <td className="py-1 px-3">{row.transactions}</td>
                    <td className="py-1 px-3">{row.active_days}</td>
                    <td className="py-1 px-3">{row.inactive_days}</td>
                    <td className="py-1 px-3">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] ${row.status === "churned" ? "text-red-700 bg-red-50 font-bold" : "text-emerald-700 bg-emerald-50 font-bold"}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Inputs and Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input sliders */}
        <div className="rounded-lg border border-neutral-200 bg-white p-5 space-y-4 shadow-sm">
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 block border-b border-neutral-100 pb-2">
            Inference Parameters
          </span>

          <div className="space-y-4 pt-1">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-neutral-500">Transactions (30d)</span>
                <span className="font-mono text-neutral-900 font-semibold">{transactions}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1000"
                step="5"
                value={transactions}
                onChange={(e) => setTransactions(Number(e.target.value))}
                className="w-full h-1.5 bg-neutral-200 rounded appearance-none cursor-pointer accent-neutral-900"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-neutral-500">Active Days</span>
                <span className="font-mono text-neutral-900 font-semibold">{activeDays} / 30</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={activeDays}
                onChange={(e) => setActiveDays(Number(e.target.value))}
                className="w-full h-1.5 bg-neutral-200 rounded appearance-none cursor-pointer accent-neutral-900"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-neutral-500">Inactive Days</span>
                <span className="font-mono text-neutral-900 font-semibold">{inactiveDays} / 30</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={inactiveDays}
                onChange={(e) => setInactiveDays(Number(e.target.value))}
                className="w-full h-1.5 bg-neutral-200 rounded appearance-none cursor-pointer accent-neutral-900"
              />
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="w-full rounded-md bg-neutral-900 hover:bg-neutral-800 text-white text-xs font-semibold py-2.5 transition active:scale-[0.99] flex items-center justify-center gap-2 shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            Execute Scikit-Learn Inference
          </button>
        </div>

        {/* Inference Output */}
        <div className="rounded-lg border border-neutral-200 bg-white p-5 flex flex-col justify-between shadow-sm">
          <div>
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 block border-b border-neutral-100 pb-2">
              Model Calibration Output
            </span>

            {prediction ? (
              <div className="mt-4 space-y-4">
                <div className="p-4 rounded-md border border-neutral-200 bg-neutral-50 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500">Predicted Churn Probability</span>
                  <div className="text-4xl font-mono font-semibold text-neutral-900 my-2 tabular-nums">
                    {prediction.churn_percentage}
                  </div>
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold uppercase ${
                      prediction.risk_level === "HIGH RISK"
                        ? "bg-red-50 text-red-700 border border-red-200"
                        : prediction.risk_level === "MEDIUM RISK"
                        ? "bg-amber-50 text-amber-800 border border-amber-200"
                        : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    }`}
                  >
                    {prediction.risk_level}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
                  <div className="p-2.5 rounded border border-neutral-200 bg-neutral-50">
                    <span className="text-[10px] text-neutral-500 block">Latency</span>
                    <span className="text-neutral-900 font-medium flex items-center gap-1 mt-0.5">
                      <Clock className="h-3 w-3 text-neutral-500" />
                      {prediction.latency_ms}ms
                    </span>
                  </div>
                  <div className="p-2.5 rounded border border-neutral-200 bg-neutral-50">
                    <span className="text-[10px] text-neutral-500 block">Model Type</span>
                    <span className="text-neutral-900 font-medium truncate block mt-0.5">
                      LogisticRegression
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-44 flex flex-col items-center justify-center text-center p-6 text-neutral-400 text-xs">
                <span>Adjust parameters and execute inference to view score.</span>
              </div>
            )}
          </div>

          <div className="text-[11px] text-neutral-400 pt-3 border-t border-neutral-100 font-mono">
            Deterministic prediction; zero token cost; sub-millisecond local execution.
          </div>
        </div>
      </div>
    </div>
  );
}
