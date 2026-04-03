import React from "react";
import QueryPanel from "../components/QueryPanel";
import ResultSpotlight from "../components/ResultSpotlight";
import RecommendationGrid from "../components/RecommendationGrid";

export default function AnalysisPage({
  query,
  onQueryChange,
  onAnalyze,
  isAnalyzing,
  onUpload,
  isUploading,
  sessionId,
  uploadedFileName,
  nodeCount,
  activeScenario,
  analysisMeta,
}) {
  return (
    <section className="page-section analyzer-page" id="analysis">
      <section className="analyzer-stage">
        <div className="section-head analyzer-head">
          <div>
            <span className="eyebrow muted">Analysis and recommendations</span>
            <h2>Upload a policy, run the query, and compare the recommendation in one place.</h2>
          </div>
          <p>
            This page combines document upload, query analysis, clause-backed output, and policy
            ranking in a single workflow.
          </p>
        </div>

        <div className="analyzer-stack">
          <QueryPanel
            query={query}
            onQueryChange={onQueryChange}
            onAnalyze={onAnalyze}
            isAnalyzing={isAnalyzing}
            onUpload={onUpload}
            isUploading={isUploading}
            sessionId={sessionId}
            uploadedFileName={uploadedFileName}
            nodeCount={nodeCount}
            analysisMeta={analysisMeta}
          />

          <ResultSpotlight
            activeScenario={activeScenario}
            isAnalyzing={isAnalyzing}
            analysisMeta={analysisMeta}
          />
        </div>

        <div className="analysis-recommendations">
          <RecommendationGrid
            recommendations={activeScenario.recommendations}
            userGoal={activeScenario.userGoal}
          />
        </div>
      </section>
    </section>
  );
}
