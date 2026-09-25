import React from "react";
import { useCustomer } from "../context/CustomerContext";
import { Building2, Database, Plus, Edit3, MessageSquare } from "lucide-react";

export default function PageStoreHeader({
  badge = null,
  showFinancials = false,
  showTickets = false,
  showDatasetAction = false,
  children = null,
}) {
  const {
    targets,
    activeCustomer,
    setActiveCustomer,
    setIsDataManagerOpen,
  } = useCustomer();

  const currentTarget = targets.find((t) => t.customer === activeCustomer) || targets[0];
  const ticketCount = currentTarget?.tickets?.length || 0;

  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-3.5 mb-6">
      {/* Top row: Store selection tabs + Action buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-neutral-500" />
          <span className="text-xs font-semibold text-neutral-900 uppercase tracking-wider font-mono">
            Target Account:
          </span>
          <div className="flex flex-wrap items-center gap-1.5">
            {targets.map((t) => {
              const isSelected = t.customer === activeCustomer;
              return (
                <button
                  key={t.customer}
                  onClick={() => setActiveCustomer(t.customer)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                    isSelected
                      ? "bg-neutral-900 text-white shadow-sm font-semibold"
                      : "bg-neutral-50 hover:bg-neutral-100 text-neutral-600 border border-neutral-200"
                  }`}
                >
                  {t.customer}
                </button>
              );
            })}
            <button
              onClick={() => setIsDataManagerOpen(true)}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 border border-dashed border-neutral-300 transition"
              title="Add custom account"
            >
              <Plus className="h-3 w-3" />
              <span>Add</span>
            </button>
          </div>
        </div>

        {/* Action triggers */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsDataManagerOpen(true)}
            className="flex items-center gap-1.5 border border-neutral-200 bg-white hover:bg-neutral-50 px-2.5 py-1 rounded text-xs font-medium text-neutral-700 transition shadow-sm"
            title="Edit store parameters"
          >
            <Edit3 className="h-3 w-3 text-neutral-500" />
            <span>Edit Account</span>
          </button>

          {showDatasetAction && (
            <button
              onClick={() => setIsDataManagerOpen(true)}
              className="flex items-center gap-1.5 border border-neutral-200 bg-white hover:bg-neutral-50 px-2.5 py-1 rounded text-xs font-medium text-neutral-700 transition shadow-sm"
              title="View training dataset and retrain model"
            >
              <Database className="h-3 w-3 text-neutral-500" />
              <span>Dataset & Model</span>
            </button>
          )}
        </div>
      </div>

      {/* Bottom row: Contextual parameters tailored strictly per tier */}
      {currentTarget && (
        <div className="flex flex-wrap items-center justify-between text-xs font-mono text-neutral-600 gap-y-2">
          <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1">
            {/* Core Tabular Signals (Tiers 01 - 09) */}
            <span>
              Transactions: <strong className="text-neutral-900">{currentTarget.transactions} txs/mo</strong>
            </span>
            <span className="text-neutral-300">•</span>
            <span>
              Active: <strong className="text-neutral-900">{currentTarget.active_days}d</strong> / Inactive:{" "}
              <strong className="text-neutral-900">{currentTarget.inactive_days}d</strong>
            </span>

            {/* Unstructured Support Tickets (Menu 08 & 09) */}
            {showTickets && (
              <>
                <span className="text-neutral-300">•</span>
                <span className="flex items-center gap-1 text-neutral-700">
                  <MessageSquare className="h-3 w-3 text-neutral-400" />
                  Tickets: <strong className="text-neutral-900">{ticketCount} on file</strong>
                </span>
              </>
            )}

            {/* Financial Profile & Held Payout (STRICTLY Menu 09) */}
            {showFinancials && (
              <>
                <span className="text-neutral-300">•</span>
                <span>
                  Tier: <strong className="text-neutral-900">{currentTarget.financials?.customer_tier || "GROWTH"}</strong>
                </span>
                <span className="text-neutral-300">•</span>
                <span>
                  Monthly GMV:{" "}
                  <strong className="text-neutral-900">
                    Rp {(currentTarget.financials?.monthly_gmv_idr || 0).toLocaleString()}
                  </strong>
                </span>
                {currentTarget.financials?.pending_payout_idr > 0 && (
                  <>
                    <span className="text-neutral-300">•</span>
                    <span className="text-amber-800 font-semibold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                      Held Payout: Rp {currentTarget.financials.pending_payout_idr.toLocaleString()}
                    </span>
                  </>
                )}
              </>
            )}
          </div>

          {/* Context Badge / Extra slot */}
          <div className="flex items-center gap-2">
            {badge && (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-neutral-100 text-neutral-600 border border-neutral-200">
                {badge}
              </span>
            )}
            {children}
          </div>
        </div>
      )}
    </div>
  );
}
