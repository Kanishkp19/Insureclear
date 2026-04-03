import React, { useEffect, useMemo, useState } from "react";
import HeroPage from "./pages/HeroPage";
import AnalysisPage from "./pages/AnalysisPage";
import TreePage from "./pages/TreePage";
import AboutPage from "./pages/AboutPage";
import { scenarios, defaultQuery, resolveScenarioFromQuery } from "./data/scenarios";
import policyDocumentData from "../policy_vectorless_document.json";
import { queryPolicy, uploadPDF, fetchPolicyTree } from "./utils/api";

const PAGE_LABELS = {
  home: "Home",
  analysis: "Analysis",
  tree: "Policy Tree",
  about: "About",
};

function getPageFromHash() {
  const hash = window.location.hash.replace(/^#\/?/, "");

  if (hash === "analysis") return "analysis";
  if (hash === "policy-tree" || hash === "tree") return "tree";
  if (hash === "about") return "about";

  return "home";
}

function normalizeVerdictTone(value, fallback) {
  const verdict = String(value || "").toLowerCase();

  if (verdict.includes("cover") || verdict.includes("accept")) return "accepted";
  if (verdict.includes("partial")) return "partial";
  if (verdict.includes("reject") || verdict.includes("exclude") || verdict.includes("deny")) {
    return "rejected";
  }

  return fallback;
}

function normalizeVerdictLabel(value, fallback) {
  if (!value) return fallback;

  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function mergeScenarioWithBackend(baseScenario, backendResponse) {
  if (!backendResponse) return baseScenario;

  const primaryClause = backendResponse.selected_clauses?.[0] ?? null;
  const nextVerdict = normalizeVerdictLabel(primaryClause?.verdict, baseScenario.verdict);
  const nextTone = normalizeVerdictTone(primaryClause?.verdict, baseScenario.verdictTone);

  // Parse real comparisons from backend
  let realRecommendations = [...baseScenario.recommendations];
  if (backendResponse.policy_comparisons && backendResponse.policy_comparisons.length > 0) {
    realRecommendations = backendResponse.policy_comparisons.map((comp, idx) => {
      // Create a nice human-readable name from filename
      let prettyName = comp.doc_id
        .replace(/_tree/g, "")
        .replace(/-/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
        
      if (prettyName.length > 25) {
        prettyName = prettyName.substring(0, 25) + "...";
      }

      // Assign an outcome tone based purely on relative rank
      let outc = "Lower fit";
      if (idx === 0) outc = "Recommended";
      else if (idx === 1) outc = "Consider";

      // Take a snippet of the found text
      let textSnippet = comp.text || "No specific clause matched.";
      if (textSnippet.length > 120) textSnippet = textSnippet.substring(0, 120) + "...";

      return {
        name: prettyName,
        fit: 0,
        outcome: outc,
        reason: textSnippet,
        premium: "Auto-detected from clauses",
        waiting: "Verified",
        highlight: "Extracted directly from policy DB"
      };
    });
  }

  return {
    ...baseScenario,
    verdict: nextVerdict,
    verdictTone: nextTone,
    confidence: "",
    summary: backendResponse.explanation || baseScenario.summary,
    clause: primaryClause?.text || baseScenario.clause,
    explanation: backendResponse.explanation || baseScenario.explanation,
    recommendations: realRecommendations,
    quickFacts: [
      { label: "Decision", value: nextVerdict },
      {
        label: "Matched clause",
        value: primaryClause?.keyword || baseScenario.quickFacts[1]?.value,
      },
      {
        label: "Best recommendation",
        value: realRecommendations[0]?.name || baseScenario.quickFacts[2]?.value,
      },
    ],
  };
}

export default function App() {
  const [query, setQuery] = useState(defaultQuery);
  const [activeScenarioId, setActiveScenarioId] = useState("diabetesEarly");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [page, setPage] = useState(() => getPageFromHash());
  const [sessionId, setSessionId] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [nodeCount, setNodeCount] = useState(0);
  const [treeData, setTreeData] = useState(policyDocumentData);
  const [backendResponse, setBackendResponse] = useState(null);
  const [analysisMeta, setAnalysisMeta] = useState({
    source: "demo",
    domain: null,
    refinedQuestion: "",
    error: "",
  });

  useEffect(() => {
    const handleHashChange = () => setPage(getPageFromHash());

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    async function loadTree() {
      try {
        const data = await fetchPolicyTree(sessionId);
        if (data && data.tree_data) {
          setTreeData(data.tree_data);
        }
      } catch (error) {
        console.error("Failed to load dynamic tree", error);
        // keep old treeData as fallback
      }
    }
    loadTree();
  }, [sessionId]);

  const baseScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === activeScenarioId) ?? scenarios[0],
    [activeScenarioId]
  );

  const activeScenario = useMemo(
    () => mergeScenarioWithBackend(baseScenario, backendResponse),
    [baseScenario, backendResponse]
  );

  async function handleAnalyze() {
    const resolved = resolveScenarioFromQuery(query);
    setActiveScenarioId(resolved.id);
    setIsAnalyzing(true);

    try {
      const data = await queryPolicy(query, sessionId);
      setBackendResponse(data);
      setAnalysisMeta({
        source: "backend",
        domain: data.domain || null,
        refinedQuestion: data.refined_question || "",
        error: "",
      });
    } catch (error) {
      setBackendResponse(null);
      setAnalysisMeta({
        source: "demo",
        domain: null,
        refinedQuestion: "",
        error: "Backend not reachable. Showing the current UI demo scenario instead.",
      });
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleUpload(file) {
    if (!file) return;

    setIsUploading(true);
    setUploadedFileName(file.name);

    try {
      const data = await uploadPDF(file, sessionId);
      setSessionId(data.session_id);
      setNodeCount(data.node_count || 0);
      setAnalysisMeta((current) => ({
        ...current,
        source: "backend",
        error: "",
      }));
    } catch (error) {
      setAnalysisMeta((current) => ({
        ...current,
        error: "Upload could not reach the backend yet. You can still use the demo query flow.",
      }));
    } finally {
      setIsUploading(false);
    }
  }

  function renderPage() {
    if (page === "analysis") {
      return (
        <AnalysisPage
          query={query}
          onQueryChange={setQuery}
          onAnalyze={handleAnalyze}
          isAnalyzing={isAnalyzing}
          onUpload={handleUpload}
          isUploading={isUploading}
          sessionId={sessionId}
          uploadedFileName={uploadedFileName}
          nodeCount={nodeCount}
          activeScenario={activeScenario}
          analysisMeta={analysisMeta}
        />
      );
    }

    if (page === "tree") {
      return <TreePage documentData={treeData} />;
    }

    if (page === "about") {
      return <AboutPage activeScenario={activeScenario} />;
    }

    return <HeroPage activeScenario={activeScenario} />;
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <div className="ambient ambient-c" />

      <header className="topbar">
        <a className="brand" href="#/">
          <span className="brand-mark">IC</span>
          <span>
            <strong>InsureClear</strong>
            <small>{PAGE_LABELS[page]}</small>
          </span>
        </a>

        <nav className="topnav">
          <a className={page === "home" ? "active" : ""} href="#/">
            Hero
          </a>
          <a className={page === "analysis" ? "active" : ""} href="#/analysis">
            Analysis
          </a>
          <a className={page === "tree" ? "active" : ""} href="#/tree">
            Policy tree
          </a>
          <a className={page === "about" ? "active" : ""} href="#/about">
            About
          </a>
        </nav>
      </header>

      <main>{renderPage()}</main>
    </div>
  );
}
