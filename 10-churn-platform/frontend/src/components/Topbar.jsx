import React from "react";
import { useSettings } from "../context/SettingsContext";
import { SlidersHorizontal, ChevronDown } from "lucide-react";

export const TARGET_CUSTOMERS = [
  "Store Critical",
  "Store Watchlist",
  "Store Safe",
  "Store Stable",
  "Store Inactive",
];

export default function Topbar({ activeCustomer, setActiveCustomer, activeMenuTitle }) {
  const { config, setIsModalOpen } = useSettings();

  return (
    <header className="h-14 border-b border-neutral-800 bg-[#0c0d0e]/90 backdrop-blur-md px-6 flex items-center justify-between flex-shrink-0 z-20">
      {/* Title / Breadcrumb */}
      <div className="flex items-center gap-2.5">
        <span className="text-xs text-neutral-500 font-mono">Workspace</span>
        <span className="text-neutral-700">/</span>
        <h2 className="text-xs font-semibold text-neutral-200 tracking-tight">{activeMenuTitle}</h2>
      </div>

      {/* Center & Right Controls */}
      <div className="flex items-center gap-3">
        {/* Customer Selector */}
        <div className="flex items-center gap-2 border border-neutral-800 bg-[#121416] rounded-md px-2.5 py-1 text-xs">
          <span className="text-[11px] text-neutral-400">Account:</span>
          <div className="relative">
            <select
              value={activeCustomer}
              onChange={(e) => setActiveCustomer(e.target.value)}
              className="bg-transparent text-neutral-100 font-medium text-xs focus:outline-none cursor-pointer pr-4 appearance-none"
            >
              {TARGET_CUSTOMERS.map((c) => (
                <option key={c} value={c} className="bg-[#121416] text-neutral-200">
                  {c}
                </option>
              ))}
            </select>
            <ChevronDown className="h-3 w-3 text-neutral-500 pointer-events-none absolute right-0 top-1" />
          </div>
        </div>

        {/* Dynamic Model Status & Trigger */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 border border-neutral-800 bg-[#121416] hover:bg-neutral-800/80 px-2.5 py-1 rounded-md text-xs text-neutral-300 transition group active:scale-[0.99]"
          title="Configure AI model parameters"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span className="text-neutral-400 font-mono text-[11px] uppercase">
            {config.provider}:
          </span>
          <span className="font-mono text-neutral-200 font-medium text-[11px]">
            {config.model || "GLM-5.3-Flash"}
          </span>
          <SlidersHorizontal className="h-3 w-3 text-neutral-500 group-hover:text-neutral-300 ml-1" />
        </button>
      </div>
    </header>
  );
}
