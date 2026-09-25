import React, { useState, useEffect } from "react";
import { churnApi } from "../services/api";
import { Table, Play, Database, Clock } from "lucide-react";

export default function Menu01_PureML({ activeCustomer }) {
  const [transactions, setTransactions] = useState(45);
  const [activeDays, setActiveDays] = useState(5);
  const [inactiveDays, setInactiveDays] = useState(30);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dataset, setDataset] = useState(null);
  const [showDataset, setShowDataset] = useState(false);

  useEffect(() => {
    if (activeCustomer === "Store Critical") {
      setTransactions(45);
      setActiveDays(5);
      setInactiveDays(30);
    } else if (activeCustomer === "Store Watchlist") {
      setTransactions(300);
      setActiveDays(18);
      setInactiveDays(12);
    } else if (activeCustomer === "Store Safe") {
      setTransactions(850);
      setActiveDays(28);
      setInactiveDays(1);
    } else if (activeCustomer === "Store Stable") {
      setTransactions(350);
      setActiveDays(22);
      setInactiveDays(8);
    } else if (activeCustomer === "Store Inactive") {
      setTransactions(45);
      setActiveDays(0);
      setInactiveDays(30);
    }
  }, [activeCustomer]);

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
      {/* Header section */}
      <div className="border-b border-neutral-800 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-100 tracking-tight">
              01. Baseline Machine Learning
            </h1>
            <p className="text-xs text-neutral-400 mt-1 max-w-xl leading-relaxed">
              Standard tabular Scikit-Learn pipeline (StandardScaler + LogisticRegression). Calculates calibrated probabilities deterministically on CPU in sub-millisecond time.
            </p>
          </div>
          <button
            onClick={loadDataset}
            className="flex items-center gap-1.5 rounded-md border border-neutral-800 bg-[#141618] hover:bg-neutral-800 px-3 py-1.5 text-xs text-neutral-300 transition"
          >
            <Database className="h-3.5 w-3.5 text-neutral-400" />
            {showDataset ? "Hide Dataset" : "Inspect Dataset"}
          </button>
        </div>
      </div>

      {/* Dataset Drawer */}
      {showDataset && dataset && (
        <div className="rounded-lg border border-neutral-800 bg-[#121416] p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-neutral-400">data/customers.csv (First 15 records)</span>
            <span className="text-[11px] font-mono text-neutral-500">{dataset.length} total rows</span>
          </div>
          <div className="max-h-52 overflow-y-auto border border-neutral-800 rounded">
            <table className="w-full text-left text-xs font-mono">
              <thead className="border-b border-neutral-800 bg-neutral-900/60 text-neutral-400 sticky top-0">
                <tr>
                  <th className="py-1.5 px-3">Customer</th>
                  <th className="py-1.5 px-3">Transactions</th>
                  <th className="py-1.5 px-3">Active Days</th>
                  <th className="py-1.5 px-3">Inactive Days</th>
                  <th className="py-1.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
                {dataset.slice(0, 15).map((row, i) => (
                  <tr key={i} className="hover:bg-neutral-800/30">
                    <td className="py-1 px-3 text-neutral-200 font-sans">{row.customer}</td>
                    <td className="py-1 px-3">{row.transactions}</td>
                    <td className="py-1 px-3">{row.active_days}</td>
                    <td className="py-1 px-3">{row.inactive_days}</td>
                    <td className="py-1 px-3">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] ${row.status === "churned" ? "text-red-400" : "text-emerald-400"}`}>
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
        <div className="rounded-lg border border-neutral-800 bg-[#121416] p-5 space-y-4">
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block border-b border-neutral-800 pb-2">
            Inference Parameters
          </span>

          <div className="space-y-4 pt-1">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-neutral-400">Transactions (30d)</span>
                <span className="font-mono text-neutral-200 font-semibold">{transactions}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1000"
                step="5"
                value={transactions}
                onChange={(e) => setTransactions(Number(e.target.value))}
                className="w-full h-1.5 bg-neutral-800 rounded appearance-none cursor-pointer accent-neutral-300"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-neutral-400">Active Days</span>
                <span className="font-mono text-neutral-200 font-semibold">{activeDays} / 30</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={activeDays}
                onChange={(e) => setActiveDays(Number(e.target.value))}
                className="w-full h-1.5 bg-neutral-800 rounded appearance-none cursor-pointer accent-neutral-300"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-neutral-400">Inactive Days</span>
                <span className="font-mono text-neutral-200 font-semibold">{inactiveDays} / 30</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={inactiveDays}
                onChange={(e) => setInactiveDays(Number(e.target.value))}
                className="w-full h-1.5 bg-neutral-800 rounded appearance-none cursor-pointer accent-neutral-300"
              />
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="w-full rounded-md bg-neutral-100 hover:bg-white text-neutral-950 text-xs font-semibold py-2.5 transition active:scale-[0.99] flex items-center justify-center gap-2 shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            Execute Scikit-Learn Inference
          </button>
        </div>

        {/* Inference Output */}
        <div className="rounded-lg border border-neutral-800 bg-[#121416] p-5 flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block border-b border-neutral-800 pb-2">
              Model Calibration Output
            </span>

            {prediction ? (
              <div className="mt-4 space-y-4">
                <div className="p-4 rounded-md border border-neutral-800 bg-[#0c0d0e] text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500">Predicted Churn Probability</span>
                  <div className="text-4xl font-mono font-semibold text-neutral-100 my-2 tabular-nums">
                    {prediction.churn_percentage}
                  </div>
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold uppercase ${
                      prediction.risk_level === "HIGH RISK"
                        ? "bg-red-950/40 text-red-400 border border-red-800/60"
                        : prediction.risk_level === "MEDIUM RISK"
                        ? "bg-amber-950/40 text-amber-400 border border-amber-800/60"
                        : "bg-emerald-950/40 text-emerald-400 border border-emerald-800/60"
                    }`}
                  >
                    {prediction.risk_level}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
                  <div className="p-2.5 rounded border border-neutral-800 bg-[#0c0d0e]">
                    <span className="text-[10px] text-neutral-500 block">Latency</span>
                    <span className="text-neutral-200 font-medium flex items-center gap-1 mt-0.5">
                      <Clock className="h-3 w-3 text-neutral-400" />
                      {prediction.latency_ms}ms
                    </span>
                  </div>
                  <div className="p-2.5 rounded border border-neutral-800 bg-[#0c0d0e]">
                    <span className="text-[10px] text-neutral-500 block">Model Type</span>
                    <span className="text-neutral-200 font-medium truncate block mt-0.5">
                      LogisticRegression
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-44 flex flex-col items-center justify-center text-center p-6 text-neutral-500 text-xs">
                <span>Adjust parameters and execute inference to view score.</span>
              </div>
            )}
          </div>

          <div className="text-[11px] text-neutral-500 pt-3 border-t border-neutral-800 font-mono">
            Deterministic prediction; zero token cost; sub-millisecond local execution.
          </div>
        </div>
      </div>
    </div>
  );
}
