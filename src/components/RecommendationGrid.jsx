import React from "react";

export default function RecommendationGrid({ recommendations, userGoal }) {
  return (
    <section className="recommendations" id="recommendations">
      <div className="section-head">
        <div>
          <span className="eyebrow muted">Recommended policies</span>
          <h2>Policy suggestions ranked for the current need.</h2>
        </div>
        <p>{userGoal}</p>
      </div>

      <div className="recommendation-grid">
        {recommendations.map((policy, index) => (
          <article
            key={policy.name}
            className={`recommendation-card surface-card ${index === 0 ? "featured" : ""}`}
          >
            <div className="recommendation-top">
              <span className="rank-chip">#{index + 1}</span>
              <span className="outcome-chip">{policy.outcome}</span>
            </div>

            <h3>{policy.name}</h3>
            <div className="fit-meter">
              <div className="fit-track">
                <span style={{ width: `${policy.fit}%` }} />
              </div>
              <strong>{policy.fit}% fit</strong>
            </div>

            <p>{policy.reason}</p>

            <div className="policy-meta">
              <span>{policy.waiting}</span>
              <span>{policy.premium}</span>
            </div>

            <div className="policy-highlight">{policy.highlight}</div>
          </article>
        ))}
      </div>
    </section>
  );
}
