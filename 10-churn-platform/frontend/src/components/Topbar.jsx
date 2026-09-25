import React from "react";
import { useSettings } from "../context/SettingsContext";
import { useCustomer } from "../context/CustomerContext";
import { SlidersHorizontal, ChevronDown, Database, Building2 } from "lucide-react";

export default function Topbar({ activeMenuTitle }) {
  const { config, setIsModalOpen } = useSettings();
  const { targets, activeCustomer, setActiveCustomer, setIsDataManagerOpen } = useCustomer();

  return (
    <header className="h-14 border-b border-neutral-200 bg-white px-6 flex items-center justify-between flex-shrink-0 z-20">
      {/* Title / Breadcrumb */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-400 font-mono">Workspace</span>
        <span className="text-neutral-300">/</span>
        <h2 className="text-xs font-semibold text-neutral-900 tracking-tight">{activeMenuTitle}</h2>
      </div>

      {/* Center & Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Dynamic Customer Selector */}
        <div className="flex items-center gap-2 border border-neutral-200 bg-neutral-50/70 hover:bg-neutral-100/60 rounded-md px-2.5 py-1 text-xs transition">
          <Building2 className="h-3.5 w-3.5 text-neutral-500" />
          <span className="text-[11px] text-neutral-500 font-medium">Account:</span>
          <div className="relative">
            <select
              value={activeCustomer}
              onChange={(e) => setActiveCustomer(e.target.value)}
              className="bg-transparent text-neutral-900 font-semibold text-xs focus:outline-none cursor-pointer pr-4 appearance-none"
            >
              {targets.map((t) => (
                <option key={t.customer} value={t.customer} className="text-neutral-900">
                  {t.customer}
                </option>
              ))}
            </select>
            <ChevronDown className="h-3 w-3 text-neutral-400 pointer-events-none absolute right-0 top-1" />
          </div>
        </div>

        {/* Data & Targets Manager Trigger */}
        <button
          onClick={() => setIsDataManagerOpen(true)}
          className="flex items-center gap-1.5 border border-neutral-200 bg-white hover:bg-neutral-50 px-2.5 py-1 rounded-md text-xs font-medium text-neutral-700 transition shadow-sm active:scale-[0.99]"
          title="Customize targets, edit dataset, and retrain ML model"
        >
          <Database className="h-3.5 w-3.5 text-neutral-600" />
          <span>Dataset & Targets</span>
        </button>

        {/* Dynamic Model Configuration Trigger */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 border border-neutral-200 bg-white hover:bg-neutral-50 px-2.5 py-1 rounded-md text-xs text-neutral-700 transition shadow-sm active:scale-[0.99] group"
          title="Configure AI model parameters"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span className="text-neutral-400 font-mono text-[10px] uppercase">
            {config.provider}:
          </span>
          <span className="font-mono text-neutral-900 font-medium text-[11px]">
            {config.model || "GLM-5.3-Flash"}
          </span>
          <SlidersHorizontal className="h-3 w-3 text-neutral-400 group-hover:text-neutral-700 ml-0.5" />
        </button>
      </div>
    </header>
  );
}
