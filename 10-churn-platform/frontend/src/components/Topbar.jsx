import React from "react";
import { useSettings } from "../context/SettingsContext";
import { SlidersHorizontal } from "lucide-react";

export default function Topbar({ activeMenuTitle }) {
  const { config, setIsModalOpen } = useSettings();

  return (
    <header className="h-14 border-b border-neutral-200 bg-white px-6 flex items-center justify-between flex-shrink-0 z-20">
      {/* Title / Breadcrumb */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-400 font-mono">Workspace</span>
        <span className="text-neutral-300">/</span>
        <h2 className="text-xs font-semibold text-neutral-900 tracking-tight">{activeMenuTitle}</h2>
      </div>

      {/* Right Controls: Model Configuration */}
      <div className="flex items-center gap-2.5">
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
