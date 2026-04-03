import React from "react";

export default function AboutSection({ activeScenario }) {
  return (
    <section className="about-shell" id="about">
      <div className="section-head about-head">
        <div>
          <span className="eyebrow muted">About InsureClear</span>
          <h2>A results-first product for making policy language usable.</h2>
        </div>
        <p>
          InsureClear is designed to turn dense insurance wording into readable decisions,
          grounded clauses, and clear policy recommendations.
        </p>
      </div>

      <div className="about-grid">
        <article className="insight-card surface-card">
          <span className="eyebrow muted">What it does</span>
          <h3>Reads policy structure like a system, not a document wall.</h3>
          <p>
            We ingest PDFs, split them into sections and clauses, tag what matters, then retrieve
            the exact evidence needed for a claim-like question.
          </p>
        </article>

        <article className="insight-card surface-card">
          <span className="eyebrow muted">Why it matters</span>
          <h3>Users should see a verdict they can understand.</h3>
          <p>
            Instead of vague summaries, the interface centers the matched clause, the decision,
            the explanation, and the best-fit policy for the user context.
          </p>
        </article>

        <article className="insight-card surface-card">
          <span className="eyebrow muted">Output style</span>
          <h3>Readable across teams, languages, and handoff moments.</h3>
          <p>
            The current experience already supports {activeScenario.languages.join(", ")} and is
            designed to expand into voice and multilingual output without changing the core flow.
          </p>
        </article>
      </div>

      <div className="about-band surface-card">
        <div>
          <span className="eyebrow muted">Current product flow</span>
          <h3>PDF upload to clause-backed recommendation.</h3>
        </div>
        <p>
          Upload policy PDFs, analyze the claim scenario, inspect the tree and summary, and return
          an evidence-backed recommendation instead of leaving the user inside policy jargon.
        </p>
      </div>
    </section>
  );
}
