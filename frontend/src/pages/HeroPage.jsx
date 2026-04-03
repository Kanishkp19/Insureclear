import React from "react";
import Hero from "../components/Hero";

export default function HeroPage({ activeScenario }) {
  return (
    <section className="page-section hero-section">
      <Hero activeScenario={activeScenario} />
    </section>
  );
}
