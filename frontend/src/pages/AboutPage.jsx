import React from "react";
import AboutSection from "../components/AboutSection";

export default function AboutPage({ activeScenario }) {
  return (
    <section className="page-section about-page">
      <AboutSection activeScenario={activeScenario} />
    </section>
  );
}
