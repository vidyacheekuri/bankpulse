# Requirements traceability

| Requirement | Human UAT scenarios | Developer evidence |
|---|---|---|
| R01 | UAT-01, UAT-02 | test_source_to_marts_reconciliation |
| R02 | UAT-03, UAT-04, UAT-05, UAT-06 | test_inclusive_dates, test_intersecting_filters, test_workspaces_filters_and_zero_capacity |
| R03 | UAT-07, UAT-08 | test_all_unknown_rate_is_unavailable, test_rate_excludes_unknown |
| R04 | UAT-09, UAT-10 | test_missing_month_and_zero_baseline |
| R05 | UAT-11, UAT-12, UAT-13 | test_flag_threshold_inclusive, test_new_and_disappearing_issues, test_source_to_marts_reconciliation |
| R06 | UAT-14 | test_queue_explicit_no_only |
| R07 | UAT-15, UAT-16, UAT-17 | test_capacity_boundaries, test_workspaces_filters_and_zero_capacity |
| R08 | UAT-18, UAT-19, UAT-20 | reports/excel_verification.json |
| R09 | UAT-21 | docs/uat_cases.csv |
| R10 | UAT-22 | test_csv_formula_injection |
| R11 | UAT-23 | test_duplicate_id_rejected |
| R12 | UAT-24 | test_workspaces_filters_and_zero_capacity |

Human acceptance is pending. Automated test success does not change the UAT status.

## Sign-off record

- Reviewer: unassigned
- Review date: not recorded
- Decision: pending human execution
- Open defects: see the defect register; no issues are invented for demonstration.
