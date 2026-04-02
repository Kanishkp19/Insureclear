import React, { useMemo, useState } from "react";
import Hero from "./components/Hero";
import QueryPanel from "./components/QueryPanel";
import ResultSpotlight from "./components/ResultSpotlight";
import RecommendationGrid from "./components/RecommendationGrid";
import InsightRail from "./components/InsightRail";
import { scenarios, defaultQuery, resolveScenarioFromQuery } from "./data/scenarios";

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
          <a href="#recommendations">Recommendations</a>
          <a href="#insights">Insights</a>
        </nav>

        <button className="ghost-button" type="button">
          Live demo
        </button>
      </header>

      <main>
        <Hero activeScenario={activeScenario} />

        <section className="workspace" id="analyzer">
          <QueryPanel
            query={query}
            onQueryChange={setQuery}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
            activeScenarioId={activeScenarioId}
            onPresetSelect={handlePresetSelect}
          />

          <ResultSpotlight activeScenario={activeScenario} isAnalyzing={isAnalyzing} />
        </section>

        <RecommendationGrid
          recommendations={activeScenario.recommendations}
          userGoal={activeScenario.userGoal}
        />

        <InsightRail activeScenario={activeScenario} />
      </main>
    </div>
  );
}
