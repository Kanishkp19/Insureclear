import React from "react";

export default function StoryAnimation({ activeScenario }) {
  return (
    <div className="story-scene">
      <div className="story-header">
        <div>
          <div className="story-label">How it feels</div>
          <p className="story-caption">
            A simple three-step story: policy confusion, structured analysis, then a clear decision
            and recommendation.
          </p>
        </div>
      </div>

      <div className="story-flow-grid">
        <article className="story-step-card">
          <span className="story-step-number">01</span>
          <h3>Someone opens a policy and gets lost in the wording.</h3>
          <p>
            Long exclusions, waiting periods, and coverage conditions make it hard to know what
            really applies.
          </p>
        </article>

        <article className="story-step-card story-step-card-accent">
          <span className="story-step-number">02</span>
          <h3>InsureClear turns the document into structured evidence.</h3>
          <p>
            We map the policy into clauses, pull the matching section, and prepare a clean
            decision-ready summary.
          </p>
        </article>

        <article className="story-step-card">
          <span className="story-step-number">03</span>
          <h3>The user sees a recommendation they can understand.</h3>
          <p>
            Verdict, matched clause, explanation, and the best-fit policy appear in one readable
            flow.
          </p>
        </article>
      </div>

      <div className="story-result-strip">
        <div className="story-result-copy">
          <span className="story-bottom-label">Current example</span>
          <h3>{activeScenario.verdict}</h3>
          <p>{activeScenario.explanation}</p>
        </div>
        <div className="story-result-metrics">
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
