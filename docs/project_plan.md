# Project Plan and JD Mapping

## Product statement

Build a reusable customer-retention analytics product for a telecommunications provider. The
product should turn a raw customer snapshot into governed data, business KPIs and a short
evidence-based report with minimal manual work.

## Capability mapping

| Role expectation | Repository evidence |
|---|---|
| Work with stakeholders | Gold measures and a plain-language stakeholder brief |
| Build with Databricks | Declarative Automation Bundle and four-task serverless workflow |
| Automate pipelines and reports | Scheduled job, local CLI, run manifest and CI artifact |
| Develop reusable data models | Bronze/Silver/Gold tables and tall segment metric model |
| Use Python and SQL | Tested Python package, PySpark notebooks and dashboard SQL |
| Apply AI appropriately | Optional `ai_query` only after aggregation and governance |
| Ensure data quality | Explicit contract, quarantine table and minimum pass-rate gate |
| Communicate actionable insight | Revenue-at-risk ranking and testable retention questions |

## Delivery stages

1. Establish reproducible local transformations and tests.
2. Implement Databricks Bronze, Silver and Gold notebook tasks.
3. Add deterministic reporting and an optional aggregate-only AI summary.
4. Add CI, architecture documentation and dashboard queries.
5. Validate against the complete IBM sample dataset and publish the fork.

## Deliberate limits

- The IBM data is a static educational snapshot, not real Superloop customer data.
- Churn associations do not prove which intervention will cause retention.
- No model performance or commercial impact is claimed without a real evaluation.
- Databricks deployment instructions are provided, but a live workspace run requires the
  user's own workspace, permissions and compute budget.
