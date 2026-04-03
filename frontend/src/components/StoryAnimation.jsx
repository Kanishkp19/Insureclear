import React from "react";

export default function StoryAnimation({ activeScenario }) {
  return (
    <div className="story-scene">
      <div className="story-header">
        <div>
          <div className="story-label">How it feels</div>
          <p className="story-caption">
            A simple three-step story: policy confusion, structured analysis, then a clear decision
            and recommendation.
          </p>
        </div>
      </div>

      <div className="story-flow-grid">
        <article className="story-step-card">
          <span className="story-step-number">01</span>
          <h3>Someone opens a policy and gets lost in the wording.</h3>
          <p>
            Long exclusions, waiting periods, and coverage conditions make it hard to know what
            really applies.
          </p>
        </article>

        <article className="story-step-card story-step-card-accent">
          <span className="story-step-number">02</span>
          <h3>InsureClear turns the document into structured evidence.</h3>
          <p>
            We map the policy into clauses, pull the matching section, and prepare a clean
            decision-ready summary.
          </p>
        </article>

        <article className="story-step-card">
          <span className="story-step-number">03</span>
          <h3>The user sees a recommendation they can understand.</h3>
          <p>
            Verdict, matched clause, explanation, and the best-fit policy appear in one readable
            flow.
          </p>
        </article>
      </div>

      <div className="story-backend-console">
        <div className="console-header">
          <span className="dot dot-red"></span>
          <span className="dot dot-yellow"></span>
          <span className="dot dot-green"></span>
          <span className="console-title">Backend Extraction Pipeline</span>
        </div>
        <div className="console-body">
          <div className="log-line">
            <span className="log-time">[18:02:44]</span>
            <span className="log-info">INFO: Uploaded "tata_aig_home_protect.pdf"</span>
          </div>
          <div className="log-line">
            <span className="log-time">[18:02:45]</span>
            <span className="log-warn">WARN: Dense wording detected. Initiating PageIndex parsing...</span>
          </div>
          <div className="log-line">
            <span className="log-time">[18:02:47]</span>
            <span className="log-info">INFO: Vectorless Tree Generated (1,240 nodes)</span>
          </div>
          <div className="log-line">
            <span className="log-time">[18:02:48]</span>
            <span className="log-magenta">RL_SELECT: Scanning clauses for "diabetes hospitalization coverage"</span>
          </div>
          <div className="log-line log-success">
             <span className="log-time">[18:02:49]</span>
             <span className="log-green">✓ MATCH FOUND: Clause 5.2.a - "Waiting period: 30 days"</span>
          </div>
        </div>
      </div>
    </div>
  );
}
