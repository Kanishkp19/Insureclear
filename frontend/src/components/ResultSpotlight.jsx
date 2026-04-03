import React from "react";

// ─── Clause Text Parser ────────────────────────────────────────────────────────
// Splits raw insurance policy text into readable segments: headings, bullets, paras.
function parseClauseText(rawText) {
  if (!rawText || typeof rawText !== "string") return [];

  const lines = rawText
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    // Split on roman numerals at start: "i.", "ii.", "iii.", "iv.", "v."
    .replace(/(?<!\w)(i{1,3}v?|vi{0,3}|ix|x)\.\s+/gi, (m) => "\n" + m)
    // Split on numbered points: "1.", "2.", "2.1", "3.4.1"
    .replace(/(?<!\d)(\d{1,2}(?:\.\d{1,2}){0,2}\.)\s+/g, (m) => "\n" + m)
    // Split on dash bullets: " - item"
    .replace(/\s+-\s+/g, "\n- ")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  return lines.map((line) => {
    // ALL-CAPS headings (≥4 caps words or a pure all-caps phrase)
    if (/^[A-Z][A-Z\s\-]{4,60}$/.test(line)) {
      return { type: "heading", text: line };
    }
    // Numbered clause: "1.", "2.1.", "3.4.1"
    if (/^\d{1,2}(?:\.\d{1,2}){0,2}\./.test(line)) {
      return { type: "numbered", text: line };
    }
    // Roman numeral sub-item: "i.", "ii.", "iii." …
    if (/^(i{1,3}v?|vi{0,3}|ix|x)\./i.test(line)) {
      return { type: "roman", text: line };
    }
    // Dash bullet
    if (/^-\s/.test(line)) {
      return { type: "bullet", text: line.replace(/^-\s/, "") };
    }
    return { type: "para", text: line };
  });
}

// ─── Clause Renderer ──────────────────────────────────────────────────────────
function ClauseText({ text }) {
  const segments = parseClauseText(text);

  if (!segments.length) return <p className="clause-empty">No clause text available.</p>;

  return (
    <div className="clause-body">
      {segments.map((seg, i) => {
        if (seg.type === "heading") {
          return (
            <p key={i} className="clause-heading">
              {seg.text}
            </p>
          );
        }
        if (seg.type === "numbered") {
          return (
            <div key={i} className="clause-numbered">
              <span className="clause-num-icon">§</span>
              <span>{seg.text}</span>
            </div>
          );
        }
        if (seg.type === "roman") {
          return (
            <div key={i} className="clause-roman">
              <span className="clause-bullet-dot">›</span>
              <span>{seg.text}</span>
            </div>
          );
        }
        if (seg.type === "bullet") {
          return (
            <div key={i} className="clause-bullet">
              <span className="clause-bullet-dot">•</span>
              <span>{seg.text}</span>
            </div>
          );
        }
        return (
          <p key={i} className="clause-para">
            {seg.text}
          </p>
        );
      })}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ResultSpotlight({ activeScenario, isAnalyzing, analysisMeta }) {
  return (
    <section className="result-panel surface-card">
      <div className="result-head">
        <div>
          <span className="eyebrow muted">Live result analysis</span>
          <h2>Policy verdict and matched evidence.</h2>
          {analysisMeta?.source === "backend" && analysisMeta?.domain ? (
            <p className="result-meta-copy">Backend domain detected: {analysisMeta.domain}</p>
          ) : null}
        </div>
      </div>

      <div className={`loading-bar ${isAnalyzing ? "active" : ""}`}>
        <span />
      </div>

      <div className="result-summary-bar">
        <div className={`analysis-animator ${isAnalyzing ? "processing" : "idle"}`}>
          <div className="animator-core">
            <div className="core-ring core-ring-1"></div>
            <div className="core-ring core-ring-2"></div>
            <div className="core-orb">
               <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18zm0 0v-4.5m0-9V3m6.364 15.364l-3.182-3.182m-6.364-6.364L5.636 5.636m15.364 6.364h-4.5m-9 0H3m15.364-6.364l-3.182 3.182M5.636 18.364l3.182-3.182" />
               </svg>
            </div>
          </div>
        </div>

        <article className="result-hero-copy">
          <span className="mini-label">Decision summary</span>
          <p>{activeScenario.summary}</p>
        </article>
      </div>

      <div className="result-main-grid">
        <section className="result-details surface-card">
          <div className="clause-card-header">
             <div className="clause-header-info">
               <span className="mini-label">Matched Evidence</span>
               <h3>Clause Match Summary</h3>
             </div>
           </div>

          <div className="clause-card">
            <ClauseText text={activeScenario.clause} />
          </div>
        </section>

        <aside className="result-sidebar">
          <article className="aside-card surface-card">
            <span className="mini-label">Simple explanation</span>
            <p className="aside-text">{activeScenario.explanation}</p>
          </article>

          <article className="aside-card surface-card">
            <span className="mini-label">Scenario Logic</span>
            <p className="aside-text">{activeScenario.counterfactual || "No scenario alternative detected."}</p>
          </article>

          <div className="trap-alert-box">
             <span className="mini-label">System Note</span>
             <p>{activeScenario.trap || "Result verified against database."}</p>
          </div>
        </aside>
      </div>
    </section>
  );
}
