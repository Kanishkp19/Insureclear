import React from "react";

export default function ResultSpotlight({ activeScenario, isAnalyzing }) {
  return (
    <section className="result-panel surface-card">
      <div className="result-head">
        <div>
          <span className="eyebrow muted">Live result</span>
          <h2>{activeScenario.summary}</h2>
        </div>
        <div className={`score-badge ${activeScenario.verdictTone}`}>
          <strong>{activeScenario.score}</strong>
          <span>Result score</span>
        </div>
      </div>

      <div className={`loading-bar ${isAnalyzing ? "active" : ""}`}>
        <span />
      </div>

      <div className="result-grid">
        <article className={`verdict-card ${activeScenario.verdictTone}`}>
          <span className="mini-label">Decision</span>
          <h3>{activeScenario.verdict}</h3>
          <p>{activeScenario.points}</p>
        </article>

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
