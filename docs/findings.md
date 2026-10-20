# Research brief · September 2026

**Decision:** where should a fictional banking operations team focus its next complaint review?

## Evidence

| Observation | Result | Suggested follow-up |
|---|---:|---|
| Published complaints, September vs August | 16,651 vs 16,201; +450 / +2.78% | Inspect which issues and products contribute before changing staffing |
| Statement-purchase issue contribution | +156; 2,837 → 2,993 | Review the underlying issue mix and company concentration |
| Account-closing issue contribution | +119; 983 → 1,102 | Compare both products and inspect the source response categories |
| Complete-period timely response | 348,983 / 351,490 = 99.2868% | Retain the denominator and inspect the 2,507 explicit No records separately |
| September historical not-timely records | 40 | Use these as a reproducible investigation queue, not an unresolved backlog |
| Default weekly review capacity | 60 | Test alternative assumptions before using this model for real operations |

The default rule requires at least 30 complaints in both months and at least 25% growth. **No issues meet that rule** in September versus August. The project reports this result without forcing an alert. A review flag is a deterministic screening rule, not a significance test or prediction.

The capacity scenario assumes two reviewers, 20 hours each, 30 minutes per review and 75% productive time: floor(2 × 20 × 60 × 0.75 / 30) = 60. Forty records would require 20 hours of review effort under these assumptions. No actual staffing, completion or savings is inferred.

## What to investigate next

1. Compare product and company composition for statement-purchase and account-closing issues. Record whether changes persist across several complete months.
2. Manually inspect a documented sample of the explicit No records using their source identifiers and published response fields.
3. Obtain internal volumes, valid resolution timestamps and observed review effort before making customer-rate, turnaround-time or staffing claims.

## Boundaries

Snapshot: 2026-10-19. The analysis uses 24 complete calendar months; 3,253 partial-October records are excluded from comparative totals. Even complete recent months may backfill. Company volumes lack customer-base denominators. Counts do not establish causes, violations, customer harm or service performance rankings.

Reproduce using `sql/research_questions.sql`, `data/processed/latest_issue_changes.csv` and `reports/quality.json`. Definitions are in [methodology](methodology.md); the original public source is the [CFPB database](https://www.consumerfinance.gov/data-research/consumer-complaints/).
