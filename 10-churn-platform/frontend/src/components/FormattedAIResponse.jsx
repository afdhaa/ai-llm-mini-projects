import React, { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { Copy, Check, Clock, Bot, Eye, Code, FileJson, FileText } from "lucide-react";

/**
 * Intelligent helper to parse and sanitize raw AI response content.
 * Handles:
 * 1. Stringified Python list of blocks: "[{'type': 'text', 'text': '...'}]"
 * 2. Real JSON objects or JSON strings (formats with indentation)
 * 3. Standard Markdown text with line breaks & headers
 */
export function processAiContent(raw) {
  if (!raw && raw !== 0) {
    return { text: "", isJson: false, jsonObj: null };
  }

  if (typeof raw === "object") {
    return {
      text: JSON.stringify(raw, null, 2),
      isJson: true,
      jsonObj: raw,
    };
  }

  let text = String(raw).trim();

  // 1. Detect and parse Python repr string: "[{'type': 'text', 'text': '...'}]" or "{'type': 'text', ...}"
  if (
    (text.startsWith("[{'") || text.startsWith("['") || text.startsWith("{'")) &&
    (text.includes("'text':") || text.includes("'content':"))
  ) {
    try {
      const regex = /'text':\s*(['"])((?:(?!\1)[^\\]|\\.)*)\1/gs;
      const matches = [...text.matchAll(regex)];
      if (matches.length > 0) {
        const extracted = matches
          .map((m) =>
            m[2]
              .replace(/\\n/g, "\n")
              .replace(/\\t/g, "\t")
              .replace(/\\'/g, "'")
              .replace(/\\"/g, '"')
              .replace(/\\\\/g, "\\")
          )
          .join("\n\n");
        if (extracted.trim()) {
          return { text: extracted, isJson: false, jsonObj: null };
        }
      }
    } catch (e) {
      // fallback to standard processing
    }
  }

  // 2. Check if text is valid JSON
  if (
    (text.startsWith("{") && text.endsWith("}")) ||
    (text.startsWith("[") && text.endsWith("]"))
  ) {
    try {
      const parsed = JSON.parse(text);

      // Check if it's an array of AIMessage text chunks like [{"type": "text", "text": "..."}]
      if (Array.isArray(parsed)) {
        const textParts = parsed
          .filter((item) => item && (item.text || item.content))
          .map((item) => item.text || item.content);
        if (textParts.length > 0 && textParts.length === parsed.length) {
          return { text: textParts.join("\n\n"), isJson: false, jsonObj: null };
        }
      }

      // Check if single object with just "text"
      if (
        typeof parsed === "object" &&
        parsed !== null &&
        parsed.text &&
        Object.keys(parsed).length === 1
      ) {
        return { text: parsed.text, isJson: false, jsonObj: null };
      }

      return {
        text: JSON.stringify(parsed, null, 2),
        isJson: true,
        jsonObj: parsed,
      };
    } catch (e) {
      // Not JSON, continue to Markdown text
    }
  }

  return { text, isJson: false, jsonObj: null };
}

export default function FormattedAIResponse({
  content,
  latencyMs = null,
  tokenUsage = null,
  modelName = null,
  title = "AI Synthesis Output",
}) {
  const [copied, setCopied] = useState(false);
  const [viewRaw, setViewRaw] = useState(false);

  const { text: cleanText, isJson, jsonObj } = useMemo(
    () => processAiContent(content),
    [content]
  );

  const handleCopy = () => {
    if (!cleanText) return;
    navigator.clipboard.writeText(cleanText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const wordCount = cleanText ? cleanText.trim().split(/\s+/).length : 0;

  return (
    <div className="rounded-lg border border-neutral-200 bg-white shadow-sm overflow-hidden flex flex-col justify-between">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-neutral-50/80 border-b border-neutral-100">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-neutral-600" />
          <span className="text-xs font-semibold text-neutral-900 font-mono tracking-tight">
            {title}
          </span>

          {/* Format Badge (JSON vs Markdown) */}
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border ${
              isJson
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-emerald-50 text-emerald-700 border-emerald-200"
            }`}
          >
            {isJson ? (
              <>
                <FileJson className="h-3 w-3" />
                Structured JSON
              </>
            ) : (
              <>
                <FileText className="h-3 w-3" />
                Markdown
              </>
            )}
          </span>

          {modelName && (
            <span className="text-[10px] font-mono text-neutral-500 px-1.5 py-0.5 rounded bg-neutral-200/50">
              {modelName}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs">
          {latencyMs != null && (
            <span className="flex items-center gap-1 text-[11px] font-mono text-neutral-500">
              <Clock className="h-3 w-3 text-neutral-400" />
              {latencyMs}ms
            </span>
          )}

          <div className="border-l border-neutral-200 pl-2 flex items-center gap-1">
            <button
              type="button"
              onClick={() => setViewRaw(!viewRaw)}
              className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200/50 transition"
              title="Toggle raw text vs formatted view"
            >
              {viewRaw ? <Eye className="h-3 w-3" /> : <Code className="h-3 w-3" />}
              <span>{viewRaw ? "Formatted" : "Raw"}</span>
            </button>

            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200/50 transition"
            >
              {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-5 overflow-y-auto max-h-[500px]">
        {viewRaw ? (
          <pre className="p-3.5 rounded border border-neutral-200 bg-neutral-50/70 text-xs font-mono text-neutral-800 whitespace-pre-wrap leading-relaxed">
            {typeof content === "string" ? content : JSON.stringify(content, null, 2)}
          </pre>
        ) : isJson ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-neutral-500 font-mono px-1">
              <span className="flex items-center gap-1.5 text-neutral-700 font-medium text-[11px]">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block"></span>
                Formatted JSON
                {jsonObj && typeof jsonObj === "object"
                  ? ` (${Array.isArray(jsonObj) ? `${jsonObj.length} items` : `${Object.keys(jsonObj).length} keys`})`
                  : ""}
              </span>
              <span className="text-[10px] text-neutral-400">Indented 2 spaces</span>
            </div>
            <pre className="p-4 rounded-lg bg-neutral-900 text-neutral-100 text-xs font-mono overflow-x-auto leading-relaxed border border-neutral-800 shadow-inner">
              <code>{cleanText}</code>
            </pre>
          </div>
        ) : (
          <div className="prose prose-sm max-w-none text-neutral-800 text-sm leading-relaxed space-y-3 font-sans">
            <ReactMarkdown
              components={{
                h1: ({ node, ...props }) => (
                  <h1 className="text-base font-bold text-neutral-900 tracking-tight mt-4 mb-2 pb-1 border-b border-neutral-200" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-sm font-bold text-neutral-900 tracking-tight mt-3 mb-1.5" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-700 mt-2 mb-1 font-mono" {...props} />
                ),
                p: ({ node, ...props }) => (
                  <p className="text-sm text-neutral-700 leading-relaxed my-1.5" {...props} />
                ),
                strong: ({ node, ...props }) => (
                  <strong className="font-semibold text-neutral-900" {...props} />
                ),
                hr: () => (
                  <hr className="my-3 border-neutral-200" />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc list-outside pl-4 space-y-1 text-sm text-neutral-700 my-2" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal list-outside pl-4 space-y-1 text-sm text-neutral-700 my-2" {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li className="text-sm text-neutral-700 leading-relaxed" {...props} />
                ),
                blockquote: ({ node, ...props }) => (
                  <blockquote className="border-l-2 border-neutral-400 pl-3 italic text-neutral-600 my-2.5 bg-neutral-50/60 py-1 rounded-r" {...props} />
                ),
                code: ({ node, inline, ...props }) => (
                  inline ? (
                    <code className="px-1.5 py-0.5 rounded bg-neutral-100 border border-neutral-200 text-xs font-mono text-neutral-800" {...props} />
                  ) : (
                    <pre className="p-3 rounded-md bg-neutral-900 text-neutral-100 text-xs font-mono overflow-x-auto my-2" {...props} />
                  )
                ),
              }}
            >
              {cleanText || "No response generated."}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {/* Footer Info Strip */}
      <div className="px-4 py-2 bg-neutral-50/60 border-t border-neutral-100 flex items-center justify-between text-[11px] font-mono text-neutral-400">
        <span>{wordCount} words (~{Math.round(wordCount * 1.3)} tokens)</span>
        {tokenUsage && (
          <span>
            Tokens: {tokenUsage.total_tokens || 0} ({tokenUsage.prompt_tokens || 0} prompt, {tokenUsage.completion_tokens || 0} comp)
          </span>
        )}
      </div>
    </div>
  );
}
