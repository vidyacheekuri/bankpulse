# Measurement and data method

The case study is a frozen public CFPB snapshot. The source lock records retrieval time, filters, monthly API counts and SHA-256 fingerprints. Data are partitioned by received month to stay within export size limits. Throttling and Retry-After handling respect the service's rate limits. Cached partitions must match their hashes; to acquire a new snapshot, use a fresh raw directory and explicitly review the changed lock and outputs.

## Population and time
- Two exact products: Credit card; Checking or savings account.
- Latest 24 complete calendar months before the supplied as-of month; partial current month retained separately.
- ISO timestamps are converted to UTC calendar dates before comparisons. The public API's exported inclusive date bounds are checked for every partition; no row may cross its partition boundaries.
- Complaint IDs must be unique. Unknown states and optional categories become `Unknown`; they are not dropped.
- Narratives, ZIP codes, tags and public-response text are not included in the distributed extract. Source field names and selected raw values are preserved in the compressed snapshot.
- Publication timing means even complete calendar months can be incomplete observations of eventual published complaints. The snapshot date is part of every interpretation.

## Measures
| Measure | Definition |
|---|---|
| Published complaints | Count of unique source complaint IDs under the filters |
| Known timeliness | Records where the published field is Yes or No |
| Timely response rate | Count Yes / count known; no known records = unavailable |
| Unknown timeliness | Total less known; displayed independently |
| Monthly change | Current count minus previous calendar month's count |
| Monthly percentage change | Change / prior count; prior zero = unavailable |
| Three-month average | Mean of three displayed consecutive monthly counts; first two months unavailable |
| Issue review flag | Current and prior counts >= selected minimum, and percentage increase >= selected threshold |
| Review queue | Selected historical records with explicit No timeliness; newest date then ID |
| Weekly capacity | Floor(reviewers × hours per reviewer × 60 × productive fraction / minutes per review) |
| Remaining scenario records | Max(0, selected queue size − weekly capacity) |

Flags are transparent screening rules, not significance tests. The issue waterfall includes a residual Other issues category so all contributions reconcile. Declining and disappeared issues remain in the comparison. Arbitrary day filters may produce partial boundary months; the overview labels that limitation and the issue comparison always uses full months.

## Excel population and refresh
Monthly Source contains all 48 month/product aggregates from the complete 24-month population. Detail contains the newest 500 records from that complete population, sorted by received date descending then ID ascending. It demonstrates lookup and conditional-count skills; it is not a representative sample and never supplies the full-population headline counts. The workbook should be regenerated after pipeline refresh, or matching source tables updated and all formulas/pivots refreshed. Read the workbook guide for implemented native features and verification limits.

## Sources
- [CFPB database and publication caveats](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- [Field reference](https://cfpb.github.io/api/ccdb/fields.html)
- [Official API specification](https://github.com/cfpb/ccdb5-api/blob/main/swagger-config.yaml)
