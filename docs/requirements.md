# BankPulse business requirements

## Decision and audience
BankPulse supports a fictional banking operations team's monthly investigation meeting. Public CFPB records supply the observations; the personas, workflow and capacity assumptions are designed for this portfolio case study. No interviews or employer engagement are claimed.

| Persona | Decision | Information needed |
|---|---|---|
| Operations manager | Which product/issue needs investigation? | Complete-month volume, contribution to change, small-baseline context |
| Business analyst | Can a reported figure be reproduced? | Definitions, source date, filters, exports, Excel/SQL reconciliation |
| Quality reviewer | Which records were explicitly not timely? | Published status, company, issue, received date, stable identifier |
| Team lead | How much review work fits in a week? | Clearly labeled review-time and capacity assumptions |

## Process
```mermaid
flowchart LR
 A[Retrieve public snapshot] --> B[Validate identifiers and dates]
 B --> C[Review complete-month trends]
 C --> D[Investigate issue changes]
 D --> E[Inspect source response statuses]
 E --> F[Export historical review queue]
 F --> G[Model review capacity]
 G --> H[Human reviewer executes acceptance scripts]
 H --> I[Record defects and sign-off decision]
```

## Prioritized user stories and acceptance criteria
| ID | Priority | User story | Acceptance criterion | Delivered location |
|---|---|---|---|---|
| R01 | Must | As an analyst, I need a defined source population. | 24 complete months; current partial month reported separately; two named products; snapshot date visible. | Pipeline, Overview |
| R02 | Must | As a manager, I need consistent drilldowns. | Product/company/state/date filters intersect; empty product selection produces zero records, not all records. | Overview, Response quality |
| R03 | Must | As a reviewer, I need an accurate timeliness measure. | Yes/(Yes+No); unknown count visible; zero denominator displays n.a.; weighted record totals. | KPI functions, Excel Analysis |
| R04 | Must | As an analyst, I need honest trends. | Missing filtered months remain zero; three-month mean requires three months; zero prior count yields unavailable percentage. | Overview |
| R05 | Must | As a manager, I need explainable growth flags. | Both endpoint counts meet the minimum; growth meets threshold; new/disappearing issues retained; contributions reconcile. | Issue explorer |
| R06 | Must | As a reviewer, I need a traceable queue. | Only explicit No statuses; deterministic order; no inferred unresolved/severity labels. | Review planning |
| R07 | Must | As a team lead, I need adjustable capacity. | Floor(staff × weekly hours × 60 × utilization / minutes); remaining never negative; zero capacity supported. | Review planning, Excel Capacity |
| R08 | Must | As an analyst, I need working Excel analysis. | Formulas, typed dates, conditional formatting, validations, source reconciliation and editable scenario controls. | Excel workbook |
| R09 | Must | As an acceptance reviewer, I need testable requirements. | Every requirement maps to test scenarios; expected/actual/status/evidence fields; developer validation distinguished from human UAT. | UAT register and evidence |
| R10 | Must | As an analyst, I need reproducible exports. | CSV rows reflect selected filters, identifiers stay text, formula-like source strings are escaped. | Downloads |
| R11 | Must | As a maintainer, I need an auditable refresh. | Partition counts and source hashes verified; contract failures stop build; offline build works. | Ingest/pipeline, CI |
| R12 | Should | As a reviewer, I need clear navigation and accessible charts. | Workspaces, units, captions, empty states and readable controls verified in browser. | Dashboard |

## Scope boundaries
This is a published-complaint analysis, not a bank's internal ticketing system. It does not expose account details, assign real employees, predict customer harm, establish regulatory violations, calculate customer complaint incidence, or infer days to resolution. The detail workbook contains a labeled 500-record extract; full-population monthly totals come from the complete filtered dataset. Recent source months can backfill. Company counts are not adjusted for customer base or market share.

## Acceptance and release
Developer checks must pass, workbook totals must reconcile, and core browser interactions must work before publication. The separate human UAT register initially has every case marked Not run. A human reviewer records actual results, evidence, defects and a sign-off decision after executing it. Publishing the portfolio is not stakeholder acceptance.
