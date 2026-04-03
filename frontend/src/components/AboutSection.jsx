import React from "react";

export default function AboutSection({ activeScenario }) {
  return (
    <section className="about-shell" id="about">
      <div className="section-head about-head">
        <div>
          <span className="eyebrow muted">Architecture & Core Technology</span>
          <h2>A state-of-the-art framework for document intelligence.</h2>
        </div>
        <p>
          InsureClear combines PageIndex for structure, LangGraph for workflow routing, 
          and a custom PyTorch Reinforcement Learning selector to understand complex policies.
        </p>
      </div>

      <div className="about-grid">
        <article className="insight-card surface-card">
          <span className="eyebrow muted">Step 1: Document Ingestion</span>
          <h3>Vectorless Document Parsing</h3>
          <p>
            When a PDF is uploaded, it is converted into an exact structural tree, maintaining
            sections, headings, and hierarchy without the noise of chunk-based vector stores.
          </p>
        </article>

        <article className="insight-card surface-card">
          <span className="eyebrow muted">Step 2: Processing</span>
          <h3>LangGraph Agent Routing</h3>
          <p>
            An intelligent router analyzes your question, detects the insurance domain, rewrites
            the query for optimal extraction, and passes it to the ML backend.
          </p>
        </article>

        <article className="insight-card surface-card">
          <span className="eyebrow muted">Step 3: Extraction</span>
          <h3>Universal RL Selector</h3>
           <p>
             Our core engine grades thousands of clauses simultaneously using a custom reward 
             function, surfacing the matched evidence and scanning rival policies for better terms.
           </p>
        </article>
      </div>

      <div className="about-band surface-card">
        <div>
          <span className="eyebrow muted">Production Ready</span>
          <h3>A fully integrated frontend and backend pipeline.</h3>
        </div>
        <p>
          Upload policy PDFs to the frontend, watch the FastAPI backend process the document into an interactive tree, and receive clear, evidence-backed recommendations directly in the UI.
        </p>
      </div>
    </section>
  );
}
