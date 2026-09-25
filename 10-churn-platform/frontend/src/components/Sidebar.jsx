import React from "react";
import {
  BarChart3,
  Bot,
  Zap,
  Wrench,
  FileCode,
  ShieldCheck,
  Scale,
  Search,
  Workflow,
  Command,
} from "lucide-react";

export const MENUS = [
  {
    id: "tier01",
    phase: "Phase 1: Foundations",
    number: "01",
    title: "Pure ML Baseline",
    subtitle: "Scikit-Learn Logistic Regression",
    icon: BarChart3,
  },
  {
    id: "tier02",
    phase: "Phase 1: Foundations",
    number: "02",
    title: "Pure Foundation LLM",
    subtitle: "Zero-Shot Qualitative Prompting",
    icon: Bot,
  },
  {
    id: "tier03",
    phase: "Phase 1: Foundations",
    number: "03",
    title: "Hybrid (ML + LLM)",
    subtitle: "Calibrated Probability + Narrative",
    icon: Zap,
  },
  {
    id: "tier04",
    phase: "Phase 1: Foundations",
    number: "04",
    title: "Autonomous Agent",
    subtitle: "LangChain ReAct & Dynamic Tools",
    icon: Wrench,
  },
  {
    id: "tier05",
    phase: "Phase 2: Hardening & Quality",
    number: "05",
    title: "Structured Outputs",
    subtitle: "Pydantic Schema & Batch Contracts",
    icon: FileCode,
  },
  {
    id: "tier06",
    phase: "Phase 2: Hardening & Quality",
    number: "06",
    title: "Guarded Agent",
    subtitle: "3-Layer Security & Injection Defense",
    icon: ShieldCheck,
  },
  {
    id: "tier07",
    phase: "Phase 2: Hardening & Quality",
    number: "07",
    title: "Automated Evals",
    subtitle: "LLM-as-a-Judge & Benchmark Suite",
    icon: Scale,
  },
  {
    id: "tier08",
    phase: "Phase 2: Hardening & Quality",
    number: "08",
    title: "Contextual Support RAG",
    subtitle: "Ticket Signals & Root Cause Override",
    icon: Search,
  },
  {
    id: "tier09",
    phase: "Phase 3: Multi-Agent & Execution",
    number: "09",
    title: "LangGraph State Machine",
    subtitle: "Multi-Agent Deliberation & HITL Gate",
    icon: Workflow,
  },
];

export default function Sidebar({ activeMenu, setActiveMenu }) {
  const phases = Array.from(new Set(MENUS.map((m) => m.phase)));

  return (
    <aside className="w-72 flex-shrink-0 border-r border-neutral-200 bg-[#f8f9fa] flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="h-14 px-4 border-b border-neutral-200 flex items-center justify-between bg-white">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-md bg-neutral-900 flex items-center justify-center text-white shadow-sm">
            <Command className="h-3.5 w-3.5" />
          </div>
          <div>
            <span className="text-xs font-semibold text-neutral-900 tracking-tight block">
              Retention Console
            </span>
            <span className="text-[10px] text-neutral-500 font-mono block">
              10-Tier Platform
            </span>
          </div>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-neutral-100 text-neutral-600 border border-neutral-200">
          v10.0
        </span>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {phases.map((phaseTitle) => {
          const items = MENUS.filter((m) => m.phase === phaseTitle);
          return (
            <div key={phaseTitle} className="space-y-1">
              <div className="px-2 pb-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-400">
                {phaseTitle}
              </div>
              {items.map((item) => {
                const Icon = item.icon;
                const isActive = activeMenu === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveMenu(item.id)}
                    className={`w-full group text-left px-2.5 py-2 rounded-lg border transition flex items-center gap-2.5 ${
                      isActive
                        ? "bg-white border-neutral-200/90 text-neutral-900 shadow-sm font-semibold"
                        : "border-transparent text-neutral-600 hover:bg-neutral-200/50 hover:text-neutral-900"
                    }`}
                  >
                    <Icon className={`h-4 w-4 flex-shrink-0 ${isActive ? "text-neutral-900" : "text-neutral-400 group-hover:text-neutral-700"}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[10px] text-neutral-400">{item.number}</span>
                        <span className="text-xs truncate">{item.title}</span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-neutral-200 bg-white text-[11px] font-mono text-neutral-500 flex items-center justify-between">
        <span>Flask REST API</span>
        <span>React 18</span>
      </div>
    </aside>
  );
}
