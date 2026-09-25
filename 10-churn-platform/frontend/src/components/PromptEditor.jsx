import React, { useState } from "react";
import { Sliders, RotateCcw, ChevronDown, ChevronUp, Copy, Check } from "lucide-react";

export default function PromptEditor({
  value,
  onChange,
  onReset,
  defaultPrompt = "",
  variables = [],
  title = "Prompt Directive (Editable)",
  subtitle = "Customize the prompt sent to the LLM before running inference.",
}) {
  const [isOpen, setIsOpen] = useState(true);
  const [copied, setCopied] = useState(false);

  const handleInsertVariable = (varName) => {
    const textToInsert = `{${varName}}`;
    onChange(value ? `${value} ${textToInsert}` : textToInsert);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-neutral-200 bg-white shadow-sm overflow-hidden transition">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-neutral-50/80 border-b border-neutral-100">
        <div className="flex items-center gap-2">
          <Sliders className="h-3.5 w-3.5 text-neutral-500" />
          <span className="text-xs font-semibold text-neutral-900 font-mono tracking-tight">
            {title}
          </span>
          <span className="text-[10px] font-mono text-neutral-500 px-1.5 py-0.5 rounded bg-neutral-200/60">
            {value.length} chars (~{Math.round(value.length / 4)} tokens)
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-neutral-500 hover:text-neutral-800 hover:bg-neutral-200/50 transition"
              title="Reset prompt to system default"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset Default</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-neutral-500 hover:text-neutral-800 hover:bg-neutral-200/50 transition"
          >
            {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded text-neutral-400 hover:text-neutral-700 hover:bg-neutral-200/50 transition"
          >
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="p-4 space-y-3">
          {subtitle && <p className="text-xs text-neutral-500 leading-relaxed">{subtitle}</p>}

          {/* Textarea */}
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={7}
            placeholder="Enter custom prompt directives..."
            className="w-full rounded-md border border-neutral-300 bg-neutral-50/50 p-3 text-xs font-mono text-neutral-800 placeholder-neutral-400 focus:bg-white focus:border-neutral-500 focus:outline-none leading-relaxed transition resize-y"
          />

          {/* Variable Chips */}
          {variables.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[11px] font-mono text-neutral-400 mr-1">Insert placeholders:</span>
              {variables.map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => handleInsertVariable(v)}
                  className="px-2 py-0.5 rounded text-[11px] font-mono bg-neutral-100 hover:bg-neutral-200 text-neutral-700 border border-neutral-200 transition"
                  title={`Insert {${v}} placeholder`}
                >
                  +{`{${v}}`}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
