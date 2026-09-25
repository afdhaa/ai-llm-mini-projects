export async function apiRequest(endpoint, method = "GET", body = null, headers = {}) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const res = await fetch(endpoint, options);
  const data = await res.json();
  if (!res.ok && !data.success) {
    throw new Error(data.error || `HTTP error ${res.status}`);
  }
  return data;
}

export const churnApi = {
  // Common / Customer profiles
  getCustomers: (headers) => apiRequest("/api/customers", "GET", null, headers),

  // Dynamic Targets & Dataset Management
  getTargets: (headers) => apiRequest("/api/targets", "GET", null, headers),
  upsertTarget: (payload, headers) => apiRequest("/api/targets", "POST", payload, headers),
  deleteTarget: (customerName, headers) => apiRequest(`/api/targets/${encodeURIComponent(customerName)}`, "DELETE", null, headers),

  getTrainingData: (headers) => apiRequest("/api/training", "GET", null, headers),
  addTrainingRow: (payload, headers) => apiRequest("/api/training", "POST", payload, headers),
  deleteTrainingRow: (customerName, headers) => apiRequest(`/api/training/${encodeURIComponent(customerName)}`, "DELETE", null, headers),
  retrainModel: (headers) => apiRequest("/api/training/retrain", "POST", null, headers),
  resetDataToDefaults: (headers) => apiRequest("/api/data/reset", "POST", null, headers),

  // Tier 01: Pure ML (Single & Batch)
  predictTier01: (payload, headers) => apiRequest("/api/tier01/predict", "POST", payload, headers),
  predictBatchTier01: (headers) => apiRequest("/api/tier01/batch", "GET", null, headers),
  getDatasetTier01: (headers) => apiRequest("/api/tier01/dataset", "GET", null, headers),

  // Tier 02: Pure Foundation LLM
  evaluateTier02: (payload, headers) => apiRequest("/api/tier02/evaluate", "POST", payload, headers),

  // Tier 03: Hybrid ML + LLM
  briefingTier03: (payload, headers) => apiRequest("/api/tier03/briefing", "POST", payload, headers),

  // Tier 04: Autonomous Agent
  chatTier04: (payload, headers) => apiRequest("/api/tier04/chat", "POST", payload, headers),

  // Tier 05: Structured Outputs
  structuredTier05: (payload, headers) => apiRequest("/api/tier05/structured", "POST", payload, headers),

  // Tier 06: Guarded Agent
  guardedTier06: (payload, headers) => apiRequest("/api/tier06/guarded", "POST", payload, headers),

  // Tier 07: Evals & Benchmarking
  getEvalsDatasetTier07: (headers) => apiRequest("/api/tier07/dataset", "GET", null, headers),
  benchmarkTier07: (payload, headers) => apiRequest("/api/tier07/benchmark", "POST", payload, headers),

  // Tier 08: Contextual RAG (Single & Portfolio Matrix)
  ragTier08: (payload, headers) => apiRequest("/api/tier08/rag", "POST", payload, headers),
  getMatrixTier08: (headers) => apiRequest("/api/tier08/matrix", "GET", null, headers),

  // Tier 09: LangGraph Multi-Agent & HITL (Single, Action, Portfolio)
  evaluateTier09: (payload, headers) => apiRequest("/api/tier09/evaluate", "POST", payload, headers),
  actionTier09: (payload, headers) => apiRequest("/api/tier09/action", "POST", payload, headers),
  getAuditTier09: (headers) => apiRequest("/api/tier09/audit", "GET", null, headers),
  getPortfolioTier09: (headers) => apiRequest("/api/tier09/portfolio", "GET", null, headers),
};
