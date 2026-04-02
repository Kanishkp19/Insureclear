import React from "react";

export default function InsightRail({ activeScenario }) {
  return (
    <section className="insight-rail" id="insights">
      <article className="insight-card surface-card">
        <span className="eyebrow muted">Trap detector</span>
        <h3>Catch policy surprises before the user does.</h3>
        <p>{activeScenario.trap}</p>
      </article>

      <article className="insight-card surface-card">
        <span className="eyebrow muted">Output modes</span>
        <h3>Keep explanations accessible.</h3>
        <p>
          Available in {activeScenario.languages.join(", ")} with room for voice input and
          spoken output in the same interface.
        </p>
      </article>

      <article className="insight-card surface-card">
        <span className="eyebrow muted">Why it feels simple</span>
        <h3>No process wall. Just outcomes.</h3>
        <p>
          The interface keeps the user focused on recommendation quality, claim confidence,
          and the exact clause that drove the answer.
        </p>
      </article>
    </section>
  );
}
