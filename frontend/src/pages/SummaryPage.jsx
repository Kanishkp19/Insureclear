import React, { useState } from "react";
import { summarizePolicy } from "../utils/api";

export default function SummaryPage({ sessionId, uploadedFileName }) {
  const [status, setStatus]   = useState("idle"); // idle | loading | done | error
  const [result, setResult]   = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSummarize() {
    if (!sessionId) return;
    setStatus("loading");
    setResult(null);
    setErrorMsg("");
    try {
      const data = await summarizePolicy(sessionId);
      setResult(data);
      setStatus("done");
    } catch (err) {
      setErrorMsg(err.message || "Something went wrong.");
      setStatus("error");
    }
  }

  const noDoc = !sessionId;

  return (
    <div className="summary-page">
      {/* ── Header ── */}
      <div className="summary-header">
        <h1 className="summary-title">Policy Summary</h1>
        <p className="summary-subtitle">
          Get a plain-English breakdown of every clause in your uploaded policy —
          instantly powered by Grok AI.
        </p>

        {uploadedFileName && (
          <div className="summary-file-tag">
            <span className="summary-file-icon">📄</span>
            {uploadedFileName}
          </div>
        )}

        <button
          className={`summary-btn${noDoc ? " disabled" : ""}${status === "loading" ? " loading" : ""}`}
          onClick={handleSummarize}
          disabled={noDoc || status === "loading"}
        >
          {status === "loading" ? (
            <span className="summary-spinner-label">
              <span className="summary-spinner" />
              Summarising clauses…
            </span>
          ) : noDoc ? (
            "Upload a policy first"
          ) : (
            "✦ Summarise Policy"
          )}
        </button>

        {status === "error" && (
          <p className="summary-error">❌ {errorMsg}</p>
        )}
      </div>

      {/* ── Results ── */}
      {status === "done" && result && (
        <div className="summary-results">
          <div className="summary-meta">
            <span className="summary-policy-name">{result.policy_title}</span>
            <span className="summary-clause-count">
              {result.total_clauses} clause{result.total_clauses !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="summary-clauses">
            {result.clauses.map((clause, i) => (
              <div className="summary-clause-card" key={i}>
                <div className="clause-number">§ {i + 1}</div>
                <div className="clause-body">
                  <h3 className="clause-name">{clause.clause_name}</h3>
                  <p className="clause-plain">{clause.plain_english}</p>

                  {clause.watch_out_for && clause.watch_out_for.length > 0 && (
                    <div className="clause-watchouts">
                      <div className="watchout-label">⚠ Watch out for</div>
                      <ul className="watchout-list">
                        {clause.watch_out_for.map((w, j) => (
                          <li key={j}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Idle empty state ── */}
      {status === "idle" && (
        <div className="summary-empty">
          <div className="summary-empty-icon">🧾</div>
          <p>Upload a policy PDF from the Analysis page, then come back here to generate your summary.</p>
        </div>
      )}
    </div>
  );
}
