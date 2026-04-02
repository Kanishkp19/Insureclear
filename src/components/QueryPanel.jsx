import React from "react";
import { scenarios } from "../data/scenarios";

export default function QueryPanel({
  query,
  onQueryChange,
  onAnalyze,
  isAnalyzing,
  activeScenarioId,
  onPresetSelect,
}) {
  const charCount = query.length;

  return (
    <section className="query-panel surface-card">
      <div className="panel-head">
        <div>
          <span className="eyebrow muted">Policy analyzer</span>
          <h2>Ask like a user. Get a result like an advisor.</h2>
        </div>
        <div className={`status-chip ${isAnalyzing ? "active" : ""}`}>
          {isAnalyzing ? "Analyzing..." : "Ready"}
        </div>
      </div>

      <div className="analyzer-frame">
        <div className="textarea-meta">
          <label className="query-label" htmlFor="policy-query">
            Claim or recommendation query
          </label>
          <span>{charCount} chars</span>
        </div>

        <textarea
          id="policy-query"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Example: Hospitalized after 20 days for diabetes. Which policy should I choose?"
        />
      </div>

      <div className="action-row">
        <button className="primary-button" type="button" onClick={onAnalyze}>
          {isAnalyzing ? "Running analysis" : "Analyze result"}
        </button>
        <span className="helper-copy">
          Drop in a claim situation or a recommendation need. We will surface the clause,
          decision, and best-fit policies below.
        </span>
      </div>

      <div className="preset-grid">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            className={`preset-card ${scenario.id === activeScenarioId ? "selected" : ""}`}
            type="button"
            onClick={() => onPresetSelect(scenario.id)}
          >
            <strong>{scenario.label}</strong>
            <span>{scenario.verdict}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
