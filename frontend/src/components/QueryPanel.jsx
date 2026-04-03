import React from "react";

export default function QueryPanel({
  query,
  onQueryChange,
  onAnalyze,
  isAnalyzing,
  onUpload,
  isUploading,
  sessionId,
  uploadedFileName,
  nodeCount,
  analysisMeta,
}) {
  const charCount = query.length;

  return (
    <section className="query-panel surface-card">
      <div className="panel-head">
        <div>
          <span className="eyebrow muted">Policy analyzer</span>
          <h2>Submit a claim-like question and generate an evidence-backed decision.</h2>
        </div>
        <div className={`status-chip ${isAnalyzing ? "active" : ""}`}>
          {isAnalyzing ? "Analyzing..." : "Ready"}
        </div>
      </div>

      <div className="upload-strip">
        <div className="upload-copy">
          <span className="query-label">Policy PDF</span>
          <strong>{uploadedFileName || "No file uploaded yet"}</strong>
          <span>
            {sessionId
              ? `Session active | ${nodeCount || 0} nodes processed`
              : "Upload a PDF to query the backend policy pipeline"}
          </span>
        </div>

        <label className="secondary-button upload-button">
          {isUploading ? "Uploading..." : "Upload PDF"}
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={(event) => onUpload?.(event.target.files?.[0])}
            hidden
          />
        </label>
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
          placeholder="Ask a claim question or request a policy recommendation from the uploaded document."
        />
      </div>

      <div className="action-row">
        <button className="primary-button" type="button" onClick={onAnalyze}>
          {isAnalyzing ? "Running analysis" : "Analyze result"}
        </button>
        <span className="helper-copy">
          Use natural language. We convert the query into matched clauses, a decision summary,
          and policy recommendations below.
        </span>
      </div>

      {analysisMeta?.error ? <p className="backend-notice">{analysisMeta.error}</p> : null}
      {analysisMeta?.refinedQuestion ? (
        <p className="backend-notice">
          Refined question: <strong>{analysisMeta.refinedQuestion}</strong>
        </p>
      ) : null}
    </section>
  );
}
