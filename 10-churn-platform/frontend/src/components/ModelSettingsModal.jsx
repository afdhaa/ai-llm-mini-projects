import React, { useState } from "react";
import { Dialog } from "@base-ui/react";
import { useSettings, PRESETS } from "../context/SettingsContext";
import { X, Check, AlertCircle, Loader2, Eye, EyeOff, SlidersHorizontal, ArrowRight } from "lucide-react";

export default function ModelSettingsModal() {
  const {
    config,
    updateConfig,
    applyPreset,
    isModalOpen,
    setIsModalOpen,
    connStatus,
    testConnection,
  } = useSettings();
  const [showKey, setShowKey] = useState(false);

  return (
    <Dialog.Root open={isModalOpen} onOpenChange={setIsModalOpen}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm transition-opacity" />
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <Dialog.Popup className="w-full max-w-lg rounded-xl border border-neutral-800 bg-[#121416] p-6 shadow-2xl text-neutral-200 focus:outline-none">
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-neutral-800/80">
              <div>
                <Dialog.Title className="text-base font-semibold text-neutral-100 tracking-tight">
                  Inference Provider Configuration
                </Dialog.Title>
                <Dialog.Description className="text-xs text-neutral-400 mt-1">
                  Configure LLM endpoints dynamically per-session. Credentials are saved locally in browser storage.
                </Dialog.Description>
              </div>
              <Dialog.Close className="rounded-md p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200 transition">
                <X className="h-4 w-4" />
              </Dialog.Close>
            </div>

            {/* Presets Grid */}
            <div className="mt-4">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 block mb-2">
                Provider Presets
              </label>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {Object.entries(PRESETS).map(([key, p]) => {
                  const isSelected = config.provider === p.provider && config.model === p.model;
                  return (
                    <button
                      key={key}
                      onClick={() => applyPreset(key)}
                      className={`text-left px-2.5 py-2 rounded-lg border text-xs font-medium transition ${
                        isSelected
                          ? "border-neutral-500 bg-neutral-800/90 text-white shadow-sm"
                          : "border-neutral-800/80 bg-neutral-900/40 text-neutral-400 hover:border-neutral-700 hover:text-neutral-200"
                      }`}
                    >
                      <div className="truncate text-[11px] font-semibold text-neutral-200">{p.label.split("(")[0].trim()}</div>
                      <div className="truncate text-[10px] text-neutral-400 font-mono mt-0.5">{p.model}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Form Fields */}
            <div className="mt-5 space-y-3.5">
              <div>
                <label className="text-xs font-medium text-neutral-300 block mb-1">
                  Provider Adapter
                </label>
                <select
                  value={config.provider}
                  onChange={(e) => updateConfig({ provider: e.target.value })}
                  className="w-full rounded-lg border border-neutral-800 bg-[#0c0d0e] px-3 py-2 text-xs text-neutral-200 focus:border-neutral-500 focus:outline-none"
                >
                  <option value="custom">Custom / OpenAI-Compatible (Z.ai, Ollama, DeepSeek, vLLM)</option>
                  <option value="openai">OpenAI (Direct API)</option>
                  <option value="gemini">Google Gemini (Direct API)</option>
                  <option value="anthropic">Anthropic Claude (Direct API)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-300 block mb-1">
                  API Base URL
                </label>
                <input
                  type="text"
                  value={config.base_url || ""}
                  onChange={(e) => updateConfig({ base_url: e.target.value })}
                  placeholder="https://api.z.ai/api/coding/paas/v4"
                  className="w-full rounded-lg border border-neutral-800 bg-[#0c0d0e] px-3 py-2 text-xs font-mono text-neutral-200 placeholder-neutral-600 focus:border-neutral-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-neutral-300 block mb-1">
                    Model Identifier
                  </label>
                  <input
                    type="text"
                    value={config.model}
                    onChange={(e) => updateConfig({ model: e.target.value })}
                    placeholder="GLM-5.3-Flash"
                    className="w-full rounded-lg border border-neutral-800 bg-[#0c0d0e] px-3 py-2 text-xs font-mono text-neutral-200 placeholder-neutral-600 focus:border-neutral-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-neutral-300 block mb-1">
                    Temperature (0.0 - 1.0)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.temperature ?? 0.0}
                    onChange={(e) => updateConfig({ temperature: parseFloat(e.target.value) || 0.0 })}
                    className="w-full rounded-lg border border-neutral-800 bg-[#0c0d0e] px-3 py-2 text-xs font-mono text-neutral-200 focus:border-neutral-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-300 block mb-1">
                  Authentication Token (API Key)
                </label>
                <div className="relative">
                  <input
                    type={showKey ? "text" : "password"}
                    value={config.api_key || ""}
                    onChange={(e) => updateConfig({ api_key: e.target.value })}
                    placeholder="Enter bearer token or API key"
                    className="w-full rounded-lg border border-neutral-800 bg-[#0c0d0e] px-3 py-2 pr-10 text-xs font-mono text-neutral-200 placeholder-neutral-600 focus:border-neutral-500 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2.5 top-2 text-neutral-400 hover:text-neutral-200"
                  >
                    {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Test Connection Banner */}
            {connStatus && (
              <div
                className={`mt-4 flex items-center justify-between rounded-lg border p-2.5 text-xs ${
                  connStatus.testing
                    ? "border-neutral-700 bg-neutral-900 text-neutral-300"
                    : connStatus.success
                    ? "border-emerald-800/60 bg-emerald-950/30 text-emerald-300"
                    : "border-red-800/60 bg-red-950/30 text-red-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  {connStatus.testing ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : connStatus.success ? (
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <AlertCircle className="h-3.5 w-3.5 text-red-400" />
                  )}
                  <span className="truncate">{connStatus.message}</span>
                </div>
                {connStatus.latency_ms != null && (
                  <span className="font-mono text-[11px] text-neutral-400 flex-shrink-0">
                    {connStatus.latency_ms}ms
                  </span>
                )}
              </div>
            )}

            {/* Footer Buttons */}
            <div className="mt-6 flex items-center justify-between pt-4 border-t border-neutral-800/80">
              <button
                type="button"
                onClick={testConnection}
                disabled={connStatus?.testing}
                className="rounded-lg border border-neutral-700/80 bg-neutral-800 px-3 py-2 text-xs font-medium text-neutral-200 hover:bg-neutral-700 transition disabled:opacity-50"
              >
                {connStatus?.testing ? "Verifying..." : "Ping Endpoint"}
              </button>
              <Dialog.Close className="rounded-lg bg-neutral-100 hover:bg-white text-neutral-950 px-4 py-2 text-xs font-semibold transition active:scale-[0.99]">
                Apply Settings
              </Dialog.Close>
            </div>
          </Dialog.Popup>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
