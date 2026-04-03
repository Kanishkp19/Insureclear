import React from "react";

export default function ResultSpotlight({ activeScenario, isAnalyzing, analysisMeta }) {
  return (
    <section className="result-panel surface-card">
      <div className="result-head">
        <div>
          <span className="eyebrow muted">Live result</span>
          <h2>Decision output with exact evidence and explanation.</h2>
          {analysisMeta?.source === "backend" && analysisMeta?.domain ? (
            <p className="result-meta-copy">Backend domain detected: {analysisMeta.domain}</p>
          ) : null}
        </div>
        <div className={`score-badge ${activeScenario.verdictTone}`}>
          <strong>{activeScenario.score}</strong>
          <span>Result score</span>
        </div>
      </div>

      <div className={`loading-bar ${isAnalyzing ? "active" : ""}`}>
        <span />
      </div>

      <div className="result-summary-bar">
        <article className={`verdict-card ${activeScenario.verdictTone}`}>
          <span className="mini-label">Decision</span>
          <h3>{activeScenario.verdict}</h3>
          <p>{activeScenario.points}</p>
        </article>

        <article className="result-hero-copy">
          <span className="mini-label">Decision summary</span>
          <p>{activeScenario.summary}</p>
        </article>
      </div>

      <div className="result-grid">

        <article className="detail-card">
          <span className="mini-label">Matched clause</span>
          <p>{activeScenario.clause}</p>
        </article>

        <article className="detail-card">
          <span className="mini-label">Simple explanation</span>
          <p>{activeScenario.explanation}</p>
        </article>

        <article className="detail-card">
          <span className="mini-label">Counterfactual</span>
          <p>{activeScenario.counterfactual}</p>
        </article>
      </div>
    </section>
  );
}
