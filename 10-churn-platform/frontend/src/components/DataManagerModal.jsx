import React, { useState, useEffect } from "react";
import { Dialog } from "@base-ui/react";
import { useCustomer } from "../context/CustomerContext";
import { churnApi } from "../services/api";
import {
  X,
  Plus,
  Trash2,
  RefreshCw,
  RotateCcw,
  Check,
  AlertCircle,
  Database,
  Building,
  Sliders,
  ChevronRight,
} from "lucide-react";

export default function DataManagerModal() {
  const { targets, isDataManagerOpen, setIsDataManagerOpen, refreshTargets } = useCustomer();
  const [activeTab, setActiveTab] = useState("targets"); // targets | training

  // Target Form State
  const [editingTarget, setEditingTarget] = useState({
    customer: "",
    transactions: 100,
    active_days: 10,
    inactive_days: 15,
    customer_tier: "GROWTH",
    monthly_gmv_idr: 50000000,
    pending_payout_idr: 0,
    ticket_subject: "",
    ticket_message: "",
  });
  const [targetSaving, setTargetSaving] = useState(false);

  // Training Data State
  const [trainingData, setTrainingData] = useState([]);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [newTrainingRow, setNewTrainingRow] = useState({
    customer: "",
    transactions: 200,
    active_days: 15,
    inactive_days: 10,
    status: "active",
  });
  const [retrainResult, setRetrainResult] = useState(null);
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    if (activeTab === "training" && isDataManagerOpen) {
      loadTrainingData();
    }
  }, [activeTab, isDataManagerOpen]);

  const loadTrainingData = async () => {
    setTrainingLoading(true);
    try {
      const res = await churnApi.getTrainingData();
      if (res.records) setTrainingData(res.records);
    } catch (e) {
      console.error(e);
    } finally {
      setTrainingLoading(false);
    }
  };

  const handleSaveTarget = async (e) => {
    e.preventDefault();
    if (!editingTarget.customer.trim()) return;

    setTargetSaving(true);
    try {
      const tickets = [];
      if (editingTarget.ticket_subject && editingTarget.ticket_message) {
        tickets.push({
          ticket_id: `TCK-${Math.floor(1000 + Math.random() * 9000)}`,
          customer: editingTarget.customer,
          timestamp: new Date().toISOString().replace("T", " ").slice(0, 19),
          channel: "WhatsApp",
          subject: editingTarget.ticket_subject,
          message: editingTarget.ticket_message,
          category: "Operational / Billing",
          status: "OPEN",
        });
      }

      await churnApi.upsertTarget({
        customer: editingTarget.customer,
        transactions: editingTarget.transactions,
        active_days: editingTarget.active_days,
        inactive_days: editingTarget.inactive_days,
        financials: {
          customer_tier: editingTarget.customer_tier,
          monthly_gmv_idr: editingTarget.monthly_gmv_idr,
          platform_fee_rate: 0.02,
          monthly_revenue_idr: editingTarget.monthly_gmv_idr * 0.02,
          pending_payout_idr: editingTarget.pending_payout_idr,
          max_retention_budget_idr: editingTarget.monthly_gmv_idr * 0.05,
          contract_renewal_days: 30,
          margin_percentage: 0.65,
        },
        tickets: tickets.length > 0 ? tickets : undefined,
      });

      await refreshTargets();
      alert(`Target account '${editingTarget.customer}' saved successfully!`);
      setEditingTarget({
        customer: "",
        transactions: 100,
        active_days: 10,
        inactive_days: 15,
        customer_tier: "GROWTH",
        monthly_gmv_idr: 50000000,
        pending_payout_idr: 0,
        ticket_subject: "",
        ticket_message: "",
      });
    } catch (err) {
      alert("Error saving target: " + err.message);
    } finally {
      setTargetSaving(false);
    }
  };

  const handleDeleteTarget = async (customerName) => {
    if (!confirm(`Are you sure you want to delete target '${customerName}'?`)) return;
    try {
      await churnApi.deleteTarget(customerName);
      await refreshTargets();
    } catch (e) {
      alert("Error deleting target: " + e.message);
    }
  };

  const handleAddTrainingRow = async (e) => {
    e.preventDefault();
    if (!newTrainingRow.customer.trim()) return;
    try {
      await churnApi.addTrainingRow(newTrainingRow);
      await loadTrainingData();
      setNewTrainingRow({
        customer: "",
        transactions: 200,
        active_days: 15,
        inactive_days: 10,
        status: "active",
      });
    } catch (e) {
      alert("Error adding training row: " + e.message);
    }
  };

  const handleDeleteTrainingRow = async (customerName) => {
    try {
      await churnApi.deleteTrainingRow(customerName);
      await loadTrainingData();
    } catch (e) {
      alert("Error deleting training row: " + e.message);
    }
  };

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainResult(null);
    try {
      const res = await churnApi.retrainModel();
      setRetrainResult(res);
    } catch (e) {
      alert("Retraining failed: " + e.message);
    } finally {
      setRetraining(false);
    }
  };

  const handleResetDefaults = async () => {
    if (!confirm("Reset all targets and training data to initial repository defaults?")) return;
    try {
      await churnApi.resetDataToDefaults();
      await refreshTargets();
      if (activeTab === "training") await loadTrainingData();
      alert("All data and models restored to defaults.");
    } catch (e) {
      alert("Reset failed: " + e.message);
    }
  };

  return (
    <Dialog.Root open={isDataManagerOpen} onOpenChange={setIsDataManagerOpen}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-50 bg-neutral-950/40 backdrop-blur-sm transition-opacity" />
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <Dialog.Popup className="w-full max-w-4xl rounded-xl border border-neutral-200 bg-white p-6 shadow-2xl text-neutral-900 focus:outline-none max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-neutral-200 flex-shrink-0">
              <div>
                <Dialog.Title className="text-base font-semibold text-neutral-900 tracking-tight">
                  Dynamic Dataset & Target Account Manager
                </Dialog.Title>
                <Dialog.Description className="text-xs text-neutral-500 mt-0.5">
                  Add, customize, or delete target merchants, edit training datasets, and retrain the ML model on the fly.
                </Dialog.Description>
              </div>
              <Dialog.Close className="rounded-md p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700 transition">
                <X className="h-4 w-4" />
              </Dialog.Close>
            </div>

            {/* Tabs Bar */}
            <div className="flex items-center justify-between mt-4 border-b border-neutral-200 pb-3 flex-shrink-0">
              <div className="flex gap-2 text-xs font-medium">
                <button
                  onClick={() => setActiveTab("targets")}
                  className={`px-3 py-1.5 rounded-md transition ${
                    activeTab === "targets"
                      ? "bg-neutral-900 text-white shadow-sm"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                  }`}
                >
                  Target Accounts ({targets.length})
                </button>
                <button
                  onClick={() => setActiveTab("training")}
                  className={`px-3 py-1.5 rounded-md transition ${
                    activeTab === "training"
                      ? "bg-neutral-900 text-white shadow-sm"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                  }`}
                >
                  Training Dataset & Model Retrain
                </button>
              </div>

              <button
                onClick={handleResetDefaults}
                className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-red-600 font-mono transition"
                title="Restore original datasets"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Reset Defaults
              </button>
            </div>

            {/* Tab 1: Target Customers */}
            {activeTab === "targets" && (
              <div className="flex-1 overflow-y-auto pt-4 space-y-6">
                {/* Table of Targets */}
                <div>
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-500 mb-2">
                    Current Target Accounts (Evaluated Across Menus 01–09)
                  </h3>
                  <div className="border border-neutral-200 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-neutral-50 border-b border-neutral-200 text-neutral-500">
                        <tr>
                          <th className="py-2 px-3">Account</th>
                          <th className="py-2 px-3">Txs</th>
                          <th className="py-2 px-3">Active / Inact</th>
                          <th className="py-2 px-3">Tier</th>
                          <th className="py-2 px-3">GMV</th>
                          <th className="py-2 px-3">Held Payout</th>
                          <th className="py-2 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-200 text-neutral-700">
                        {targets.map((t, idx) => (
                          <tr key={idx} className="hover:bg-neutral-50/80">
                            <td className="py-2 px-3 font-semibold text-neutral-900 font-sans">{t.customer}</td>
                            <td className="py-2 px-3">{t.transactions}</td>
                            <td className="py-2 px-3">{t.active_days}d / {t.inactive_days}d</td>
                            <td className="py-2 px-3">
                              <span className="px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-600 text-[10px]">
                                {t.financials?.customer_tier || "GROWTH"}
                              </span>
                            </td>
                            <td className="py-2 px-3">Rp {(t.financials?.monthly_gmv_idr || 0).toLocaleString()}</td>
                            <td className="py-2 px-3">
                              {t.financials?.pending_payout_idr > 0 ? (
                                <span className="text-amber-700 font-semibold">
                                  Rp {t.financials.pending_payout_idr.toLocaleString()}
                                </span>
                              ) : (
                                "Rp 0"
                              )}
                            </td>
                            <td className="py-2 px-3 text-right space-x-2">
                              <button
                                onClick={() => {
                                  setEditingTarget({
                                    customer: t.customer,
                                    transactions: t.transactions,
                                    active_days: t.active_days,
                                    inactive_days: t.inactive_days,
                                    customer_tier: t.financials?.customer_tier || "GROWTH",
                                    monthly_gmv_idr: t.financials?.monthly_gmv_idr || 50000000,
                                    pending_payout_idr: t.financials?.pending_payout_idr || 0,
                                    ticket_subject: t.tickets?.[0]?.subject || "",
                                    ticket_message: t.tickets?.[0]?.message || "",
                                  });
                                }}
                                className="text-blue-600 hover:text-blue-800 text-[11px]"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteTarget(t.customer)}
                                className="text-red-500 hover:text-red-700 text-[11px]"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Add / Edit Form */}
                <form onSubmit={handleSaveTarget} className="border border-neutral-200 bg-neutral-50/70 p-4 rounded-lg space-y-4">
                  <div className="flex items-center justify-between border-b border-neutral-200 pb-2">
                    <span className="text-xs font-semibold text-neutral-900">
                      {editingTarget.customer ? `Edit Target: ${editingTarget.customer}` : "Add New Target Account"}
                    </span>
                    <span className="text-[11px] font-mono text-neutral-500">Affects Topbar & all 9 Tiers</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Account Name *</label>
                      <input
                        type="text"
                        value={editingTarget.customer}
                        onChange={(e) => setEditingTarget({ ...editingTarget, customer: e.target.value })}
                        placeholder="e.g. Toko Baru"
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900 focus:outline-none focus:border-neutral-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Transactions (30d)</label>
                      <input
                        type="number"
                        value={editingTarget.transactions}
                        onChange={(e) => setEditingTarget({ ...editingTarget, transactions: Number(e.target.value) })}
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Active Days (0-30)</label>
                      <input
                        type="number"
                        min="0"
                        max="30"
                        value={editingTarget.active_days}
                        onChange={(e) => setEditingTarget({ ...editingTarget, active_days: Number(e.target.value) })}
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Inactive Days (0-30)</label>
                      <input
                        type="number"
                        min="0"
                        max="30"
                        value={editingTarget.inactive_days}
                        onChange={(e) => setEditingTarget({ ...editingTarget, inactive_days: Number(e.target.value) })}
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900 font-mono"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Tier</label>
                      <select
                        value={editingTarget.customer_tier}
                        onChange={(e) => setEditingTarget({ ...editingTarget, customer_tier: e.target.value })}
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900"
                      >
                        <option value="ENTERPRISE">ENTERPRISE</option>
                        <option value="GROWTH">GROWTH</option>
                        <option value="MICRO">MICRO</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Monthly GMV (IDR)</label>
                      <input
                        type="number"
                        step="1000000"
                        value={editingTarget.monthly_gmv_idr}
                        onChange={(e) => setEditingTarget({ ...editingTarget, monthly_gmv_idr: Number(e.target.value) })}
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-neutral-600 font-medium block mb-1">Held Payout (IDR)</label>
                      <input
                        type="number"
                        step="1000000"
                        value={editingTarget.pending_payout_idr}
                        onChange={(e) => setEditingTarget({ ...editingTarget, pending_payout_idr: Number(e.target.value) })}
                        className="w-full rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900 font-mono"
                      />
                    </div>
                  </div>

                  {/* Optional support ticket */}
                  <div className="space-y-2 pt-1 border-t border-neutral-200">
                    <span className="text-[11px] font-mono text-neutral-500 uppercase">Optional Support Complaint Ticket (RAG Signal)</span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <input
                        type="text"
                        value={editingTarget.ticket_subject}
                        onChange={(e) => setEditingTarget({ ...editingTarget, ticket_subject: e.target.value })}
                        placeholder="Subject: e.g. Kendala Gateway Webhook"
                        className="rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900"
                      />
                      <input
                        type="text"
                        value={editingTarget.ticket_message}
                        onChange={(e) => setEditingTarget({ ...editingTarget, ticket_message: e.target.value })}
                        placeholder="Message: e.g. Transaksi sering error saat checkout..."
                        className="rounded border border-neutral-300 bg-white px-2.5 py-1.5 text-neutral-900"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="submit"
                      disabled={targetSaving}
                      className="rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-4 py-2 text-xs font-semibold shadow-sm transition active:scale-[0.99] disabled:opacity-50"
                    >
                      {targetSaving ? "Saving..." : "Save Target Account"}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Tab 2: Training Data & Retraining */}
            {activeTab === "training" && (
              <div className="flex-1 overflow-y-auto pt-4 space-y-6">
                {/* Retrain Action Box */}
                <div className="border border-neutral-200 bg-neutral-50 p-4 rounded-lg flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-neutral-900 block">
                      Live Model Retraining
                    </span>
                    <span className="text-xs text-neutral-500 mt-0.5 block">
                      Train a fresh StandardScaler + LogisticRegression pipeline on current {trainingData.length} records.
                    </span>
                  </div>

                  <button
                    onClick={handleRetrain}
                    disabled={retraining}
                    className="flex items-center gap-1.5 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-4 py-2 text-xs font-semibold shadow-sm transition disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${retraining ? "animate-spin" : ""}`} />
                    {retraining ? "Retraining..." : "Re-train Model Now"}
                  </button>
                </div>

                {/* Retrain Report */}
                {retrainResult && (
                  <div className="p-3.5 rounded-lg border border-emerald-300 bg-emerald-50 text-xs font-mono space-y-1.5 text-emerald-900">
                    <div className="flex justify-between items-center font-bold">
                      <span>✅ Model Retrained & Deployed Successfully</span>
                      <span>Accuracy: {retrainResult.accuracy_formatted}</span>
                    </div>
                    <div className="text-[11px] text-emerald-800 flex justify-between">
                      <span>Total Samples: {retrainResult.total_samples} ({retrainResult.churned_samples} churned, {retrainResult.active_samples} active)</span>
                      <span>Latency: {retrainResult.latency_ms}ms</span>
                    </div>
                    <div className="text-[10px] text-emerald-700 pt-1 border-t border-emerald-200">
                      Coefficients: {JSON.stringify(retrainResult.coefficients)}
                    </div>
                  </div>
                )}

                {/* Add Training Row Form */}
                <form onSubmit={handleAddTrainingRow} className="border border-neutral-200 bg-white p-3.5 rounded-lg space-y-3">
                  <span className="text-xs font-semibold text-neutral-900 block">
                    Add Training Observation Row
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
                    <input
                      type="text"
                      placeholder="Account Name"
                      value={newTrainingRow.customer}
                      onChange={(e) => setNewTrainingRow({ ...newTrainingRow, customer: e.target.value })}
                      className="rounded border border-neutral-300 px-2 py-1 text-neutral-900"
                      required
                    />
                    <input
                      type="number"
                      placeholder="Txs"
                      value={newTrainingRow.transactions}
                      onChange={(e) => setNewTrainingRow({ ...newTrainingRow, transactions: Number(e.target.value) })}
                      className="rounded border border-neutral-300 px-2 py-1 text-neutral-900 font-mono"
                    />
                    <input
                      type="number"
                      placeholder="Active Days"
                      value={newTrainingRow.active_days}
                      onChange={(e) => setNewTrainingRow({ ...newTrainingRow, active_days: Number(e.target.value) })}
                      className="rounded border border-neutral-300 px-2 py-1 text-neutral-900 font-mono"
                    />
                    <input
                      type="number"
                      placeholder="Inactive Days"
                      value={newTrainingRow.inactive_days}
                      onChange={(e) => setNewTrainingRow({ ...newTrainingRow, inactive_days: Number(e.target.value) })}
                      className="rounded border border-neutral-300 px-2 py-1 text-neutral-900 font-mono"
                    />
                    <select
                      value={newTrainingRow.status}
                      onChange={(e) => setNewTrainingRow({ ...newTrainingRow, status: e.target.value })}
                      className="rounded border border-neutral-300 px-2 py-1 text-neutral-900 font-semibold"
                    >
                      <option value="active">active (0)</option>
                      <option value="churned">churned (1)</option>
                    </select>
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="rounded bg-neutral-800 hover:bg-neutral-900 text-white px-3 py-1 text-xs font-medium"
                    >
                      Add to customers.csv
                    </button>
                  </div>
                </form>

                {/* Training Dataset Table */}
                <div>
                  <span className="text-xs font-mono font-semibold uppercase text-neutral-500 block mb-2">
                    Training Records (customers.csv)
                  </span>
                  <div className="border border-neutral-200 rounded-lg max-h-60 overflow-y-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-neutral-50 text-neutral-500 border-b border-neutral-200 sticky top-0">
                        <tr>
                          <th className="py-1.5 px-3">Customer</th>
                          <th className="py-1.5 px-3">Txs</th>
                          <th className="py-1.5 px-3">Active</th>
                          <th className="py-1.5 px-3">Inactive</th>
                          <th className="py-1.5 px-3">Status</th>
                          <th className="py-1.5 px-3 text-right">Delete</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-200 text-neutral-700">
                        {trainingData.map((row, idx) => (
                          <tr key={idx} className="hover:bg-neutral-50">
                            <td className="py-1.5 px-3 font-sans font-medium text-neutral-900">{row.customer}</td>
                            <td className="py-1.5 px-3">{row.transactions}</td>
                            <td className="py-1.5 px-3">{row.active_days}</td>
                            <td className="py-1.5 px-3">{row.inactive_days}</td>
                            <td className="py-1.5 px-3">
                              <span className={`px-1.5 py-0.2 rounded text-[10px] ${
                                row.status === "churned" ? "text-red-600 bg-red-50 font-bold" : "text-emerald-700 bg-emerald-50 font-bold"
                              }`}>
                                {row.status}
                              </span>
                            </td>
                            <td className="py-1.5 px-3 text-right">
                              <button
                                onClick={() => handleDeleteTrainingRow(row.customer)}
                                className="text-neutral-400 hover:text-red-600"
                              >
                                <Trash2 className="h-3.5 w-3.5 inline" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </Dialog.Popup>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
