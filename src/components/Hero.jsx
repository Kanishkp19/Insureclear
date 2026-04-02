import React from "react";
import StoryAnimation from "./StoryAnimation";

export default function Hero({ activeScenario }) {
  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <span className="eyebrow">Results-first insurance AI</span>
        <h1>See the verdict, the clause, and the best policy to recommend.</h1>
        <p className="hero-text">
          InsureClear is designed to feel simple from the first screen. Drop in a claim-like
          question, get the decision instantly, and surface policy recommendations with clear
          reasoning instead of dense policy jargon.
        </p>

        <div className="hero-badges">
          <span>Clause-backed</span>
          <span>Simple language</span>
          <span>Policy recommendations</span>
          <span>Voice-ready</span>
        </div>
      </div>

      <div className="hero-preview">
        <StoryAnimation activeScenario={activeScenario} />
      </div>
    </section>
  );
}
