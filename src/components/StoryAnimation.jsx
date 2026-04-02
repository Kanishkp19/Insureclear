import React from "react";

export default function StoryAnimation({ activeScenario }) {
  return (
    <div className="story-scene">
      <div className="story-label">5 second story loop</div>

      <div className="story-bubble question-bubble">
        <strong>Too much policy language.</strong>
        <span>What is actually covered?</span>
      </div>

      <div className="story-bubble answer-bubble">
        <strong>{activeScenario.verdict}</strong>
        <span>{activeScenario.quickFacts[2]?.value}</span>
      </div>

      <div className="story-desk">
        <div className="paper paper-a" />
        <div className="paper paper-b" />
        <div className="paper paper-c" />
        <div className="laptop">
          <div className="laptop-screen">
            <div className="mini-result-chip">{activeScenario.confidence}</div>
            <div className="mini-bars">
              <span />
              <span />
              <span />
            </div>
            <div className="mini-reco-card">
              <strong>{activeScenario.quickFacts[2]?.value}</strong>
              <small>Recommended policy</small>
            </div>
          </div>
        </div>
      </div>

      <div className="figure figure-reader">
        <div className="figure-head">
          <span className="eye left" />
          <span className="eye right" />
          <span className="mouth" />
        </div>
        <div className="figure-body" />
        <div className="figure-arm arm-left" />
        <div className="figure-arm arm-right" />
        <div className="figure-leg leg-left" />
        <div className="figure-leg leg-right" />
      </div>

      <div className="figure figure-friend">
        <div className="figure-head">
          <span className="eye left" />
          <span className="eye right" />
          <span className="mouth smile" />
        </div>
        <div className="figure-body friend-shirt" />
        <div className="figure-arm arm-left lift" />
        <div className="figure-arm arm-right" />
        <div className="figure-leg leg-left" />
        <div className="figure-leg leg-right" />
        <div className="friend-tablet">
          <span />
        </div>
      </div>

      <div className="preview-window card-float story-overlay">
        <div className="preview-top">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>

        <div className="preview-pill">{activeScenario.confidence}</div>
        <h2>{activeScenario.verdict}</h2>
        <p>{activeScenario.summary}</p>

        <div className="preview-stats">
          {activeScenario.quickFacts.map((fact) => (
            <article key={fact.label}>
              <strong>{fact.value}</strong>
              <span>{fact.label}</span>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
