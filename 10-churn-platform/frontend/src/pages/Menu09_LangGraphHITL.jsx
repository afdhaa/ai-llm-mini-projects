import React, { useState, useEffect } from "react";
import { churnApi } from "../services/api";
import { useSettings } from "../context/SettingsContext";
import {
  Workflow,
  Play,
  Check,
  X,
  Send,
  AlertCircle,
  FileCheck2,
  History,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Building,
} from "lucide-react";
import PageStoreHeader from "../components/PageStoreHeader";
import { useCustomer } from "../context/CustomerContext";

export default function Menu09_LangGraphHITL() {
  const { activeCustomer, setActiveCustomer } = useCustomer();
  const { getHeaders } = useSettings();
  const [loading, setLoading] = useState(false);
  const [pipelineState, setPipelineState] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [activeTab, setActiveTab] = useState("console"); // console | audit

  // HITL Interactive Controls State
  const [hitlAction, setHitlAction] = useState(null); // approve_all | selective | steer | reject
  const [selectedActionIndices, setSelectedActionIndices] = useState([]);
  const [steeringText, setSteeringText] = useState("");
  const [executingDecision, setExecutingDecision] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);

  // Portfolio Multi-Agent Governance State
  const [portfolioData, setPortfolioData] = useState(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);

  const isAll = activeCustomer === "ALL";

  useEffect(() => {
    if (activeTab === "audit") {
      churnApi.getAuditTier09(getHeaders()).then((res) => {
        if (res.logs) setAuditLogs(res.logs);
      });
    }
  }, [activeTab]);

  useEffect(() => {
    if (isAll) {
      loadPortfolio();
    }
  }, [isAll]);

  const loadPortfolio = async () => {
    setPortfolioLoading(true);
    try {
      const res = await churnApi.getPortfolioTier09(getHeaders());
      setPortfolioData(res);
    } catch (e) {
      alert("Portfolio loading failed: " + e.message);
    } finally {
      setPortfolioLoading(false);
    }
  };

  const handleStartEvaluation = async () => {
    setLoading(true);
    setPipelineState(null);
    setHitlAction(null);
    setSelectedActionIndices([]);
    setSteeringText("");

    const sId = `session-${activeCustomer.replace(/\s+/g, "-").toLowerCase()}-${Date.now()}`;
    setSessionId(sId);

    try {
      const res = await churnApi.evaluateTier09(
        { customer: activeCustomer, session_id: sId },
        getHeaders()
      );
      setPipelineState(res.state);

      if (res.state?.proposal?.action_items) {
        setSelectedActionIndices(res.state.proposal.action_items.map((_, i) => i));
      }
    } catch (e) {
      alert("LangGraph evaluation failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const submitDecision = async (decision, extraPayload = {}) => {
    setExecutingDecision(true);
    try {
      const payload = {
        session_id: sessionId,
        decision,
        ...extraPayload,
      };

      const res = await churnApi.actionTier09(payload, getHeaders());

      if (decision === "steer") {
        setPipelineState((prev) => ({
          ...prev,
          proposal: res.proposal,
          human_feedback: payload.feedback,
        }));
        setHitlAction(null);
        alert("Proposal revised by Supervisor Agent based on operator instructions.");
      } else {
        setPipelineState((prev) => ({
          ...prev,
          hitl_status: res.hitl_status,
          execution_logs: res.execution_logs,
        }));
        setHitlAction(null);
      }
    } catch (e) {
      alert("Decision execution failed: " + e.message);
    } finally {
      setExecutingDecision(false);
    }
  };

  const prop = pipelineState?.proposal;
  const diag = pipelineState?.diagnostic_findings;
  const fin = pipelineState?.financial_assessment;
  const isPendingReview = pipelineState?.hitl_status === "PENDING_REVIEW";

  return (
    <div className="space-y-6 max-w-5xl">
      {/* In-Page Store Selector & Parameter Header */}
      <PageStoreHeader showDatasetAction={false} showFinancials={true} showTickets={true} badge="Multi-Agent Commercial & Technical Profile" />

      {/* Header section */}
      <div className="border-b border-neutral-200 pb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-neutral-900 tracking-tight">
              09. Multi-Agent State Machine & HITL Gate (LangGraph)
            </h1>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Coordinates specialized departmental agents (Diagnostics, Finance, and Supervisor) using a cyclic LangGraph state machine. High-impact operational side-effects pause at an interactive human approval gate.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex rounded-md bg-neutral-100 p-1 border border-neutral-200 text-xs">
              <button
                onClick={() => setActiveTab("console")}
                className={`px-3 py-1 rounded transition text-xs font-medium ${
                  activeTab === "console" ? "bg-white text-neutral-900 shadow-sm" : "text-neutral-500 hover:text-neutral-900"
                }`}
              >
                {isAll ? "Portfolio Governance" : "Deliberation Console"}
              </button>
              <button
                onClick={() => setActiveTab("audit")}
                className={`px-3 py-1 rounded transition text-xs font-medium ${
                  activeTab === "audit" ? "bg-white text-neutral-900 shadow-sm" : "text-neutral-500 hover:text-neutral-900"
                }`}
              >
                Execution Audit Log
              </button>
            </div>

            {!isAll && activeTab === "console" && (
              <button
                onClick={handleStartEvaluation}
                disabled={loading}
                className="flex items-center gap-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition active:scale-[0.99] disabled:opacity-50 shadow-sm"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                {loading ? "Deliberating..." : `Evaluate ${activeCustomer}`}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ALL STORES: Portfolio Multi-Agent Governance Console */}
      {isAll && activeTab === "console" ? (
        <div className="space-y-6">
          {/* Top Aggregate Metric Cards */}
          {portfolioData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg border border-neutral-200 bg-white shadow-sm space-y-1">
                  <span className="text-[10px] font-mono uppercase text-neutral-500">Portfolio Accounts</span>
                  <div className="text-2xl font-bold font-mono text-neutral-900">{portfolioData.total_accounts} Stores</div>
                  <span className="text-[11px] text-neutral-500 block">Evaluated across agents</span>
                </div>

                <div className="p-4 rounded-lg border border-amber-200 bg-amber-50/60 shadow-sm space-y-1">
                  <span className="text-[10px] font-mono uppercase text-amber-700">HITL Review Required</span>
                  <div className="text-2xl font-bold font-mono text-amber-900">{portfolioData.hitl_required_count} Stores</div>
                  <span className="text-[11px] text-amber-800 block">High risk or payout holds</span>
                </div>

                <div className="p-4 rounded-lg border border-emerald-200 bg-emerald-50/60 shadow-sm space-y-1">
                  <span className="text-[10px] font-mono uppercase text-emerald-700">Auto-Approved (Safe)</span>
                  <div className="text-2xl font-bold font-mono text-emerald-900">{portfolioData.auto_approved_count} Stores</div>
                  <span className="text-[11px] text-emerald-800 block">Zero banking liability risk</span>
                </div>

                <div className="p-4 rounded-lg border border-neutral-200 bg-white shadow-sm space-y-1">
                  <span className="text-[10px] font-mono uppercase text-neutral-500">Held Payouts at Stake</span>
                  <div className="text-2xl font-bold font-mono text-red-600">
                    Rp {portfolioData.portfolio_held_payouts_idr.toLocaleString()}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">BCA settlement engine holds</span>
                </div>
              </div>

              {/* Multi-Account Governance Breakdown Table */}
              <div className="rounded-lg border border-neutral-200 bg-white p-5 space-y-3 shadow-sm">
                <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
                  <div>
                    <h2 className="text-sm font-semibold text-neutral-900 flex items-center gap-2">
                      <Layers className="h-4 w-4 text-neutral-600" />
                      Multi-Account Deliberation & Governance Overview
                    </h2>
                    <p className="text-xs text-neutral-500 mt-0.5">
                      Portfolio classification: which accounts are auto-dispatched vs which mandate human operator sign-off.
                    </p>
                  </div>

                  <button
                    onClick={loadPortfolio}
                    disabled={portfolioLoading}
                    className="rounded-md bg-neutral-100 hover:bg-neutral-200 border border-neutral-200 text-neutral-800 px-3 py-1.5 text-xs font-medium transition"
                  >
                    {portfolioLoading ? "Refreshing..." : "Refresh Governance Matrix"}
                  </button>
                </div>

                <div className="border border-neutral-200 rounded-lg overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-neutral-50 text-neutral-500 border-b border-neutral-200">
                      <tr>
                        <th className="py-2.5 px-3">Account</th>
                        <th className="py-2.5 px-3">ML Churn Prob</th>
                        <th className="py-2.5 px-3">Tier</th>
                        <th className="py-2.5 px-3">Monthly GMV</th>
                        <th className="py-2.5 px-3">Held Payout</th>
                        <th className="py-2.5 px-3">Governance Status</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-200 text-neutral-700">
                      {portfolioData.accounts.map((acc, idx) => (
                        <tr key={idx} className="hover:bg-neutral-50/80">
                          <td className="py-2.5 px-3 font-semibold text-neutral-900 font-sans">
                            {acc.customer}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              acc.ml_risk_level === "HIGH RISK"
                                ? "bg-red-50 text-red-700 border border-red-200"
                                : acc.ml_risk_level === "MEDIUM RISK"
                                ? "bg-amber-50 text-amber-800 border border-amber-200"
                                : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            }`}>
                              {acc.churn_percentage}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">{acc.tier}</td>
                          <td className="py-2.5 px-3">Rp {acc.monthly_gmv_idr.toLocaleString()}</td>
                          <td className="py-2.5 px-3">
                            {acc.pending_payout_idr > 0 ? (
                              <span className="text-amber-800 font-bold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                                Rp {acc.pending_payout_idr.toLocaleString()}
                              </span>
                            ) : (
                              "Rp 0"
                            )}
                          </td>
                          <td className="py-2.5 px-3">
                            {acc.requires_hitl ? (
                              <span className="inline-flex items-center gap-1 text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-bold text-[10px]">
                                <ShieldAlert className="h-3 w-3" />
                                {acc.governance_status}
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-medium text-[10px]">
                                <ShieldCheck className="h-3 w-3" />
                                {acc.governance_status}
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <button
                              onClick={() => setActiveCustomer(acc.customer)}
                              className="text-xs text-blue-600 hover:text-blue-800 font-sans font-medium"
                            >
                              Open Deliberation →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex justify-between items-center text-[11px] font-mono text-neutral-400 pt-1">
                  <span>High-liability actions are held at the HITL gate. Click any account to review & authorize directives.</span>
                  <span>Portfolio GMV: Rp {portfolioData.portfolio_monthly_gmv_idr.toLocaleString()}</span>
                </div>
              </div>
            </>
          )}
        </div>
      ) : (
        /* SINGLE STORE CONSOLE */
        activeTab === "console" && pipelineState && (
          <div className="space-y-6">
            {/* 3 Specialist Reports */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* 1. Diagnostics */}
              <div className="p-4 rounded-lg border border-neutral-200 bg-white space-y-2 shadow-sm">
                <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block pb-1 border-b border-neutral-100">
                  1. Technical Diagnostics
                </span>
                {diag ? (
                  <div className="text-xs space-y-1.5 font-mono">
                    <div className="flex justify-between items-center text-neutral-700">
                      <span className="text-neutral-400">Root Cause:</span>
                      <strong className="text-neutral-900">{diag.root_cause}</strong>
                    </div>
                    <div className="flex justify-between items-center text-neutral-700">
                      <span className="text-neutral-400">Severity:</span>
                      <span className="px-1.5 py-0.2 rounded bg-neutral-100 text-neutral-800 font-semibold">{diag.technical_severity}</span>
                    </div>
                    <p className="text-[11px] text-neutral-700 bg-neutral-50 p-2.5 rounded border border-neutral-200 font-sans leading-relaxed line-clamp-3">
                      {diag.key_blocker}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-neutral-400">Diagnosing...</p>
                )}
              </div>

              {/* 2. Finance */}
              <div className="p-4 rounded-lg border border-neutral-200 bg-white space-y-2 shadow-sm">
                <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block pb-1 border-b border-neutral-100">
                  2. Commercial Assessment
                </span>
                {fin ? (
                  <div className="text-xs space-y-1.5 font-mono">
                    <div className="flex justify-between items-center text-neutral-700">
                      <span className="text-neutral-400">Tier:</span>
                      <span className="text-neutral-900">{fin.customer_tier}</span>
                    </div>
                    <div className="flex justify-between items-center text-neutral-700">
                      <span className="text-neutral-400">Exposure:</span>
                      <span className="text-neutral-900">{fin.financial_risk_verdict}</span>
                    </div>
                    <div className="flex justify-between items-center text-neutral-700">
                      <span className="text-neutral-400">Budget Cap:</span>
                      <span className="text-neutral-900 font-semibold">Rp {fin.approved_budget_cap_idr?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center text-neutral-700">
                      <span className="text-neutral-400">Held Payout:</span>
                      <span className="text-neutral-900 font-semibold">Rp {fin.pending_payout_idr?.toLocaleString()}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-neutral-400">Calculating exposure...</p>
                )}
              </div>

              {/* 3. Safety Checkpoint */}
              <div className="p-4 rounded-lg border border-neutral-200 bg-white space-y-2 shadow-sm">
                <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-400 block pb-1 border-b border-neutral-100">
                  3. Safety Gate Status
                </span>
                <div className="text-xs space-y-1.5 font-mono">
                  <div className="flex justify-between items-center text-neutral-700">
                    <span className="text-neutral-400">Status:</span>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                      isPendingReview ? "bg-amber-100 text-amber-800 border border-amber-300" : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                    }`}>
                      {pipelineState.hitl_status}
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-600 font-sans pt-1 leading-relaxed">
                    {prop?.requires_hitl
                      ? prop.hitl_reason
                      : "Low risk / Standard cost -> Safe for Auto-Approval"}
                  </p>
                </div>
              </div>
            </div>

            {/* Supervisor Proposal */}
            {prop && (
              <div className="rounded-lg border border-neutral-200 bg-white p-5 space-y-4 shadow-sm">
                <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
                  <div>
                    <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-500">
                      Supervisor Negotiated Strategy
                    </h3>
                    <p className="text-xs text-neutral-800 mt-1 font-sans">{prop.summary}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-neutral-400 font-mono uppercase block">Total Financial Impact:</span>
                    <span className="text-lg font-mono font-semibold text-neutral-900 tabular-nums">
                      Rp {prop.total_proposed_cost_idr?.toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Action items table */}
                <div className="space-y-2">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 block">
                    Action Directives ({prop.action_items?.length || 0}):
                  </span>
                  {prop.action_items?.map((item, idx) => {
                    const isSelected = selectedActionIndices.includes(idx);
                    return (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border transition flex items-start gap-3 text-xs ${
                          isSelected
                            ? "bg-neutral-50/80 border-neutral-200"
                            : "bg-neutral-100/40 border-neutral-200 opacity-60"
                        }`}
                      >
                        {hitlAction === "selective" && (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedActionIndices([...selectedActionIndices, idx]);
                              } else {
                                setSelectedActionIndices(selectedActionIndices.filter((i) => i !== idx));
                              }
                            }}
                            className="mt-1 h-3.5 w-3.5 rounded border-neutral-300 accent-neutral-900"
                          />
                        )}
                        <div className="flex-1 space-y-0.5 font-mono">
                          <div className="flex justify-between items-center">
                            <span className="font-semibold text-neutral-900">
                              [{idx + 1}] [{item.action_type}] {item.title}
                            </span>
                            {item.cost_idr > 0 && (
                              <span className="text-neutral-700 tabular-nums font-semibold">
                                Rp {item.cost_idr.toLocaleString()}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-neutral-600 font-sans">{item.description}</p>
                          <span className="text-[10px] text-neutral-400 block">Owner: {item.owner_role}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Human-in-the-Loop Decision Box */}
                {isPendingReview && (
                  <div className="rounded-lg border border-amber-300 bg-amber-50/70 p-4 mt-5 space-y-3">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900">
                      <AlertCircle className="h-3.5 w-3.5 text-amber-700" />
                      Human Authorization Required Before Dispatch
                    </div>

                    {!hitlAction ? (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                        <button
                          onClick={() => submitDecision("approve_all")}
                          disabled={executingDecision}
                          className="rounded-md bg-neutral-900 hover:bg-neutral-800 text-white py-2 px-3 text-xs font-semibold transition active:scale-[0.99] flex items-center justify-center gap-1.5 shadow-sm"
                        >
                          <Check className="h-3.5 w-3.5" />
                          Approve All
                        </button>

                        <button
                          onClick={() => setHitlAction("selective")}
                          disabled={executingDecision}
                          className="rounded-md border border-neutral-300 bg-white hover:bg-neutral-50 py-2 px-3 text-xs font-medium text-neutral-800 transition shadow-sm"
                        >
                          Item-by-Item Review
                        </button>

                        <button
                          onClick={() => setHitlAction("steer")}
                          disabled={executingDecision}
                          className="rounded-md border border-neutral-300 bg-white hover:bg-neutral-50 py-2 px-3 text-xs font-medium text-neutral-800 transition shadow-sm"
                        >
                          Steer / Revise Plan
                        </button>

                        <button
                          onClick={() => submitDecision("reject")}
                          disabled={executingDecision}
                          className="rounded-md border border-red-300 bg-red-50 hover:bg-red-100 text-red-700 py-2 px-3 text-xs font-medium transition flex items-center justify-center gap-1.5"
                        >
                          <X className="h-3.5 w-3.5" />
                          Reject All
                        </button>
                      </div>
                    ) : hitlAction === "selective" ? (
                      <div className="space-y-2.5 pt-1">
                        <p className="text-xs text-neutral-800 font-mono">
                          Select individual actions to dispatch ({selectedActionIndices.length} selected):
                        </p>
                        <div className="flex gap-2.5">
                          <button
                            onClick={() => submitDecision("selective", { approved_indices: selectedActionIndices })}
                            disabled={executingDecision}
                            className="rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition"
                          >
                            Confirm Dispatch ({selectedActionIndices.length} actions)
                          </button>
                          <button
                            onClick={() => setHitlAction(null)}
                            className="rounded-md border border-neutral-300 bg-white px-3.5 py-1.5 text-xs font-medium text-neutral-700"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : hitlAction === "steer" ? (
                      <div className="space-y-2.5 pt-1">
                        <label className="text-xs text-neutral-800 block">
                          Enter guidance for the Supervisor Agent to adjust the proposal:
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={steeringText}
                            onChange={(e) => setSteeringText(e.target.value)}
                            placeholder="e.g. Batalkan fee waiver, cukup unfreeze payout dan eskalasi P1 DevOps..."
                            className="flex-1 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-xs text-neutral-900 focus:border-neutral-500 focus:outline-none"
                          />
                          <button
                            onClick={() => submitDecision("steer", { feedback: steeringText })}
                            disabled={executingDecision || !steeringText.trim()}
                            className="rounded-md bg-neutral-900 hover:bg-neutral-800 text-white px-3.5 py-1.5 text-xs font-semibold transition flex items-center gap-1.5"
                          >
                            <Send className="h-3 w-3" />
                            Re-Synthesize
                          </button>
                          <button
                            onClick={() => setHitlAction(null)}
                            className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-xs font-medium text-neutral-700"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            )}

            {/* Execution Log Table */}
            {pipelineState.execution_logs && pipelineState.execution_logs.length > 0 && (
              <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-2.5 shadow-sm">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500 block border-b border-neutral-100 pb-2">
                  Operational Side-Effects Dispatched ({pipelineState.execution_logs.length})
                </span>
                <div className="space-y-1.5 font-mono text-xs">
                  {pipelineState.execution_logs.map((log, i) => (
                    <div key={i} className="p-2.5 rounded bg-neutral-50 border border-neutral-200 space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-neutral-900 font-medium">
                          [{log.status}] [{log.action_type}] ──▶ {log.target_system}
                        </span>
                      </div>
                      <p className="text-[11px] text-neutral-600 font-sans">{log.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* Audit Trail Tab */}
      {activeTab === "audit" && (
        <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
              Audit Trail Records (data/execution_audit.json)
            </span>
            <span className="text-xs font-mono text-neutral-500">{auditLogs.length} entries</span>
          </div>

          {auditLogs.length > 0 ? (
            <div className="space-y-2">
              {auditLogs.map((log, idx) => (
                <div key={idx} className="p-3 rounded bg-neutral-50 border border-neutral-200 text-xs space-y-1 font-mono">
                  <span className="text-neutral-900 font-medium">
                    [{log.status}] [{log.action_type}] ──▶ {log.target_system}
                  </span>
                  <p className="text-neutral-600 font-sans text-[11px]">{log.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-neutral-400 py-6 text-center font-mono">
              No audit logs recorded yet. Authorize actions in Menu 09 to record entries.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
