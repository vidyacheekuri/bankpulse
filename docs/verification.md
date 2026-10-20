# Developer verification

Verification completed 2026-10-20 against the frozen 2026-10-19 public snapshot.

## Automated checks

**37 tests passed.** The committed JUnit report is `reports/test-results.xml`; GitHub Actions independently rebuilds the SQL marts and reruns the suite on pushes and pull requests.

Coverage includes inclusive date intersections; empty selections; weighted rates and unknown statuses; zero-filled months; disappearing/new issues; contribution reconciliation; invalid capacity inputs; deterministic explicit-No queues; safe CSV strings; source hashes and partition counts; duplicate/invalid source rejection; all five Streamlit workspaces; empty-filter and zero-capacity app states; workbook relationships, cached values, pivot cache population, chart references and formula-cell protection.

The pipeline reconciles all 354,743 retained records: 351,490 complete-period plus 3,253 partial-period records. All 48 monthly product aggregates reconcile to source facts.

## Workbook checks

The authoring calculation engine passed ten explicit formula/input-change checks (see `reports/excel_verification.json`), followed by a formula-error scan. Every sheet was rendered and visually inspected. A read-only workbook parser recognized the nine worksheets, native PivotTable and 48-record pivot cache. Final ZIP/XML checks confirm internal relationships resolve, three charts retain range references, saved values match the pipeline and designated input cells remain unlocked.

**Not executed:** desktop Excel opening, recalculation, pivot refresh and slicer clicks. macOS Computer Use access remained unavailable on retry. File-level validation does not establish desktop compatibility. Human acceptance remains pending.

## Browser checks

The dashboard was inspected in the Codex in-app browser at its default 1280 × 720 viewport:

| Interaction | Observed result |
|---|---|
| Open each of five workspaces | Headings, controls and result sections rendered |
| Overview: remove checking/savings product | 183,818 credit-card records; 1,374 explicit No records |
| Restore both products | 351,490 records; 2,507 explicit No records |
| Issue explorer: default August/September comparison | 16,201 → 16,651; +450; 0 review flags |
| Review planning: set reviewers to zero | Capacity 0; selected records 40; remaining 40 |
| Restore two reviewers | Capacity 60; remaining 0 |
| Project evidence | Excel, UAT and requirements download controls present; human UAT labeled Not run |

Screenshots are in `docs/assets/`. Downloads' underlying files and export logic are tested separately; no human acceptance status is inferred from browser checks.

## Defects and acceptance

One integration defect prevented the SQL mart build because `unknown` was used as an unquoted reserved alias. It was corrected and the source-to-mart reconciliation retest passed; see `docs/defects.csv`.

The 24 human UAT scenarios intentionally remain **Not run**. Reviewers should execute the documented steps, record actual results, attach evidence and make their own acceptance decision. No stakeholder sign-off is claimed.
