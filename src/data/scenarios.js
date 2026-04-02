export const scenarios = [
  {
    id: "diabetesEarly",
    label: "Early diabetes claim",
    query: "Hospitalized after 20 days for diabetes. Which policy is best and will this claim be approved?",
    userGoal: "Find the safest policy for diabetes-related hospitalization with minimal early waiting risk.",
    verdict: "Rejected",
    verdictTone: "rejected",
    score: 34,
    points: "-20 pts",
    confidence: "92% confidence",
    summary:
      "The current claim should be rejected because the hospitalization happened before the diabetes waiting period ended.",
    clause:
      'Clause 5.2.a: "Any hospitalization due to diabetes within 30 days of policy commencement is not payable."',
    explanation:
      "This means the treatment may be covered later, but not this early in the policy lifecycle.",
    counterfactual:
      "If hospitalization happened after 35 days, this same claim would likely move to Accepted.",
    trap:
      "Trap detected: the base plan looks broad, but the diabetes clause quietly blocks claims during the first 30 days.",
    languages: ["English", "Hindi", "Tamil", "Spanish"],
    recommendations: [
      {
        name: "Care Shield Advance",
        fit: 96,
        outcome: "Recommended",
        reason: "Best fit for chronic-condition claims because the waiting period is shortest among the compared plans.",
        premium: "Premium band: Medium",
        waiting: "Waiting period: 30 days",
        highlight: "Most likely to approve after day 30"
      },
      {
        name: "Family Shield Plus",
        fit: 82,
        outcome: "Consider",
        reason: "Broad benefits but longer stabilization rules make early-stage claims riskier.",
        premium: "Premium band: Medium-High",
        waiting: "Waiting period: 45 days",
        highlight: "Better for families than single-condition screening"
      },
      {
        name: "Health Secure Gold",
        fit: 71,
        outcome: "Lower fit",
        reason: "Looks generous on hospitalization, but several chronic-condition sub-rules reduce claim certainty.",
        premium: "Premium band: Low",
        waiting: "Waiting period: 60 days",
        highlight: "Highest risk of early claim denial"
      }
    ],
    quickFacts: [
      { label: "Decision", value: "Rejected" },
      { label: "Matched clause", value: "Waiting period" },
      { label: "Best recommendation", value: "Care Shield Advance" }
    ]
  },
  {
    id: "maternityPartial",
    label: "Maternity payout",
    query: "Planning maternity care within 1 year. Which policy should be recommended and how much is likely payable?",
    userGoal: "Recommend a policy for near-term maternity planning with low waiting time and strong payout limits.",
    verdict: "Partial",
    verdictTone: "partial",
    score: 67,
    points: "+10 pts",
    confidence: "88% confidence",
    summary:
      "The claim is partially payable because waiting period conditions are satisfied, but the maternity benefit has a payout cap.",
    clause:
      'Clause 4.1: "Maternity expenses are covered after 9 months from inception, subject to the benefit limit stated in the schedule."',
    explanation:
      "The user can receive benefits, but only up to the maternity sub-limit defined by the chosen plan.",
    counterfactual:
      "If the selected policy had a higher maternity cap, the same claim would shift closer to full approval.",
    trap:
      "Trap detected: coverage exists, but the low sub-limit can make a fully covered-looking claim feel underpaid.",
    languages: ["English", "Hindi", "Arabic", "Tamil"],
    recommendations: [
      {
        name: "NestCare Premium",
        fit: 95,
        outcome: "Recommended",
        reason: "Best near-term maternity option with a 9-month waiting period and the strongest payout cap.",
        premium: "Premium band: Medium-High",
        waiting: "Waiting period: 9 months",
        highlight: "Best balance of eligibility and payout size"
      },
      {
        name: "Family Bloom Secure",
        fit: 79,
        outcome: "Consider",
        reason: "Affordable maternity add-on, but the sub-limit is noticeably tighter.",
        premium: "Premium band: Medium",
        waiting: "Waiting period: 9 months",
        highlight: "Good value, lower final reimbursement"
      },
      {
        name: "Starter Women Care",
        fit: 58,
        outcome: "Lower fit",
        reason: "Longer add-on restrictions and lower cap make this weaker for a one-year planning window.",
        premium: "Premium band: Low",
        waiting: "Waiting period: 12 months",
        highlight: "Misses the ideal timeline"
      }
    ],
    quickFacts: [
      { label: "Decision", value: "Partial" },
      { label: "Matched clause", value: "Benefit cap" },
      { label: "Best recommendation", value: "NestCare Premium" }
    ]
  },
  {
    id: "diabetesLate",
    label: "Post-waiting approval",
    query: "Hospitalized after 45 days for diabetes. Which policy should be recommended now?",
    userGoal: "Recommend the strongest policy now that the initial diabetes waiting period has passed.",
    verdict: "Accepted",
    verdictTone: "accepted",
    score: 91,
    points: "+25 pts",
    confidence: "94% confidence",
    summary:
      "The claim is likely accepted because the user crosses the key waiting threshold and no stronger exclusion is triggered.",
    clause:
      'Clause 5.2.b: "After the initial waiting period, hospitalization benefits for diabetes-related treatment shall be payable as per policy limits."',
    explanation:
      "Now the focus shifts from eligibility to payout quality, room rent limits, and claim smoothness across policies.",
    counterfactual:
      "If the claim were filed before day 30, the same case would likely fall back to Rejected.",
    trap:
      "No major trap triggered, but lower-tier plans still hide room-rent and sub-limit issues that affect reimbursement.",
    languages: ["English", "Hindi", "Spanish", "Arabic"],
    recommendations: [
      {
        name: "Care Shield Advance",
        fit: 97,
        outcome: "Recommended",
        reason: "Best claim-readiness score after waiting completion, with cleaner chronic-care payout rules.",
        premium: "Premium band: Medium",
        waiting: "Waiting period: Completed",
        highlight: "Highest approval confidence"
      },
      {
        name: "Health Secure Gold",
        fit: 84,
        outcome: "Consider",
        reason: "Now viable after the waiting window, though payout rules remain less generous.",
        premium: "Premium band: Low",
        waiting: "Waiting period: Completed",
        highlight: "Budget option with moderate payout quality"
      },
      {
        name: "Family Shield Plus",
        fit: 76,
        outcome: "Lower fit",
        reason: "Good family structure, but weaker for focused chronic-condition optimization.",
        premium: "Premium band: Medium-High",
        waiting: "Waiting period: Completed",
        highlight: "Broader plan, less condition-focused value"
      }
    ],
    quickFacts: [
      { label: "Decision", value: "Accepted" },
      { label: "Matched clause", value: "Coverage rule" },
      { label: "Best recommendation", value: "Care Shield Advance" }
    ]
  }
];

export const defaultQuery = scenarios[0].query;

export function resolveScenarioFromQuery(query) {
  const normalized = query.toLowerCase();

  if (normalized.includes("maternity") || normalized.includes("pregnan")) {
    return scenarios[1];
  }

  if (
    normalized.includes("45 days") ||
    normalized.includes("after 45") ||
    normalized.includes("after 35") ||
    normalized.includes("post waiting")
  ) {
    return scenarios[2];
  }

  return scenarios[0];
}
