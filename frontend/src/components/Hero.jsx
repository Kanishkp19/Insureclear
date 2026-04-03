import React from "react";
import StoryAnimation from "./StoryAnimation";

export default function Hero({ activeScenario }) {
  const trustBrands = [
    {
      name: "ICICI Bank",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/ICICI%20Bank%20Logo.svg"
    },
    {
      name: "HDFC Bank",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/HDFC-Bank-Logo.svg"
    },
    {
      name: "Axis Bank",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/Axis%20Bank%20logo.svg"
    },
    {
      name: "Yes Bank",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/Yes%20Bank%20SVG%20Logo.svg"
    },
    {
      name: "HDFC ERGO",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/HDFC%20ERGO%20General%20Insurance%20Company.svg"
    },
    {
      name: "Star Health",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/Star%20Health%20and%20Allied%20Insurance.svg"
    },
    {
      name: "Niva Bupa",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/Niva%20Bupa%20Logo.jpg"
    },
    {
      name: "Bajaj Allianz",
      src: "https://commons.wikimedia.org/wiki/Special:FilePath/Bajaj%20Allianz%20Insurance.svg"
    }
  ];

  return (
    <section className="hero" id="top">
      <div className="hero-lead">
        <span className="eyebrow">Powered by Universal RL & Vectorless Extraction</span>
        <h1>Upload any policy. Ask a question. Get the exact clause and best alternatives.</h1>
      </div>

      <aside className="hero-trust" aria-label="Banks and insurers">
        <span className="hero-logo-label">Works across banks and insurers</span>
        <div className="hero-trust-grid">
          {trustBrands.map((brand) => (
            <article key={brand.name} className="hero-trust-card">
              <img src={brand.src} alt={`${brand.name} logo`} loading="lazy" />
            </article>
          ))}
        </div>
      </aside>

      <div className="hero-preview">
        <StoryAnimation activeScenario={activeScenario} />
      </div>

      <div className="hero-support">
        <div className="hero-support-copy">
          <p className="hero-text">
            InsureClear replaces keyword search with an advanced Reinforcement Learning framework. 
            It converts unstructured PDFs into a Vectorless PageIndex tree, dynamically chunks text, 
            and evaluates clauses using a specialized Sigmoid-to-Softmax selector model.
          </p>

          <div className="hero-badges">
            <span>Universal RL Model</span>
            <span>Vectorless RAG</span>
            <span>Dynamic Multi-Domain</span>
            <span>LangGraph Agents</span>
          </div>
        </div>

        <div className="hero-support-side">
          <div className="hero-facts">
            <article>
              <strong>{activeScenario.quickFacts[1]?.value}</strong>
              <span>Primary evidence</span>
            </article>
            <article>
              <strong>{activeScenario.quickFacts[2]?.value}</strong>
              <span>Best recommendation</span>
            </article>
          </div>
        </div>
      </div>
    </section>
  );
}
