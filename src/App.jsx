import React, { useMemo, useState } from "react";
import Hero from "./components/Hero";
import QueryPanel from "./components/QueryPanel";
import ResultSpotlight from "./components/ResultSpotlight";
import RecommendationGrid from "./components/RecommendationGrid";
import InsightRail from "./components/InsightRail";
import PolicyTreeExplorer from "./components/PolicyTreeExplorer";
import { scenarios, defaultQuery, resolveScenarioFromQuery } from "./data/scenarios";
import policyDocumentData from "../policy_vectorless_document.json";

export default function App() {
  const [query, setQuery] = useState(defaultQuery);
  const [activeScenarioId, setActiveScenarioId] = useState("diabetesEarly");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const activeScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === activeScenarioId) ?? scenarios[0],
    [activeScenarioId]
  );

  function handlePresetSelect(nextId) {
    const scenario = scenarios.find((item) => item.id === nextId);
    if (!scenario) return;

    setActiveScenarioId(scenario.id);
    setQuery(scenario.query);
  }

  function handleAnalyze() {
    setIsAnalyzing(true);

    window.setTimeout(() => {
      const resolved = resolveScenarioFromQuery(query);
      setActiveScenarioId(resolved.id);
      setIsAnalyzing(false);
    }, 850);
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <div className="ambient ambient-c" />

      <header className="topbar">
        <a className="brand" href="#top">
          <span className="brand-mark">IC</span>
          <span>
            <strong>InsureClear</strong>
            <small>Policy results made simple</small>
          </span>
        </a>

        <nav className="topnav">
          <a href="#analyzer">Analyzer</a>
          <a href="#policy-tree">Policy tree</a>
          <a href="#recommendations">Recommendations</a>
          <a href="#insights">Insights</a>
        </nav>

        <button className="ghost-button" type="button">
          Evidence-led UI
        </button>
      </header>

      <main>
        <section className="page-section hero-section">
          <Hero activeScenario={activeScenario} />
        </section>

        <section className="page-section analyzer-page" id="analyzer">
          <section className="analyzer-stage">
            <div className="section-head analyzer-head">
              <div>
                <span className="eyebrow muted">Main analyzer</span>
                <h2>Paste the policy question. Let the decision and recommendations follow.</h2>
              </div>
              <p>
                This is the primary action area now. The analyzer leads, the verdict appears
                right underneath, and the recommended policies continue below in one clean flow.
              </p>
            </div>

            <div className="analyzer-stack">
              <QueryPanel
                query={query}
                onQueryChange={setQuery}
                onAnalyze={handleAnalyze}
                isAnalyzing={isAnalyzing}
                activeScenarioId={activeScenarioId}
                onPresetSelect={handlePresetSelect}
              />

              <ResultSpotlight activeScenario={activeScenario} isAnalyzing={isAnalyzing} />
            </div>
          </section>
        </section>

        <PolicyTreeExplorer documentData={policyDocumentData} />

        <section className="page-section recommendations-page">
          <RecommendationGrid
            recommendations={activeScenario.recommendations}
            userGoal={activeScenario.userGoal}
          />
        </section>

        <section className="page-section insights-page">
          <InsightRail activeScenario={activeScenario} />
        </section>
      </main>
    </div>
  );
}
