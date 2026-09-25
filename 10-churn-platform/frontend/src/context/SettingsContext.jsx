import React, { createContext, useContext, useState, useEffect } from "react";

const STORAGE_KEY = "churn_platform_ai_config";

export const PRESETS = {
  zai: {
    label: "Z.ai Coding Plan (GLM-5.3-Flash)",
    provider: "custom",
    base_url: "https://api.z.ai/api/coding/paas/v4",
    model: "GLM-5.3-Flash",
    requires_key: true,
  },
  openai: {
    label: "OpenAI (GPT-4o-mini)",
    provider: "openai",
    base_url: "https://api.openai.com/v1",
    model: "gpt-4o-mini",
    requires_key: true,
  },
  gemini: {
    label: "Google Gemini (Gemini 2.5 Flash)",
    provider: "gemini",
    base_url: "",
    model: "gemini-2.5-flash",
    requires_key: true,
  },
  anthropic: {
    label: "Anthropic (Claude 3.5 Haiku)",
    provider: "anthropic",
    base_url: "https://api.anthropic.com/v1",
    model: "claude-3-5-haiku-latest",
    requires_key: true,
  },
  ollama: {
    label: "Ollama Local (Llama 3.1)",
    provider: "custom",
    base_url: "http://localhost:11434/v1",
    model: "llama3.1",
    requires_key: false,
  },
};

const DEFAULT_CONFIG = {
  provider: "custom",
  base_url: "https://api.z.ai/api/coding/paas/v4",
  api_key: "5a1dbf146a9141228bcd15ab7e3756a9.1IwRrZgc84gV58EM",
  model: "GLM-5.3-Flash",
  temperature: 0.0,
};

const SettingsContext = createContext(null);

export function SettingsProvider({ children }) {
  const [config, setConfig] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : DEFAULT_CONFIG;
    } catch {
      return DEFAULT_CONFIG;
    }
  });

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [connStatus, setConnStatus] = useState(null); // { testing, success, message, latency_ms }

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    } catch (e) {
      console.error("Failed saving AI config to localStorage:", e);
    }
  }, [config]);

  const updateConfig = (updates) => {
    setConfig((prev) => ({ ...prev, ...updates }));
    setConnStatus(null);
  };

  const applyPreset = (presetKey) => {
    const p = PRESETS[presetKey];
    if (!p) return;
    setConfig((prev) => ({
      ...prev,
      provider: p.provider,
      base_url: p.base_url,
      model: p.model,
    }));
    setConnStatus(null);
  };

  const getHeaders = () => ({
    "x-ai-provider": config.provider || "custom",
    "x-ai-base-url": config.base_url || "",
    "x-ai-api-key": config.api_key || "",
    "x-ai-model": config.model || "GLM-5.3-Flash",
    "x-ai-temperature": String(config.temperature ?? 0.0),
  });

  const testConnection = async () => {
    setConnStatus({ testing: true });
    try {
      const res = await fetch("/api/settings/test-connection", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getHeaders(),
        },
        body: JSON.stringify(config),
      });
      const data = await res.json();
      setConnStatus({
        testing: false,
        success: data.success,
        message: data.message || (data.success ? "Connection successful" : "Failed"),
        latency_ms: data.latency_ms,
      });
      return data;
    } catch (err) {
      setConnStatus({
        testing: false,
        success: false,
        message: `Network error: ${err.message}`,
        latency_ms: null,
      });
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        config,
        updateConfig,
        applyPreset,
        getHeaders,
        isModalOpen,
        setIsModalOpen,
        connStatus,
        testConnection,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
