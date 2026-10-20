# Data dictionary
One row in `complaints.parquet` is one published complaint, identified by `complaint_id`.

| Field | Type | Meaning |
|---|---|---|
| complaint_id | Text | Original unique identifier, preserved as text |
| received | Date | UTC calendar date CFPB received the complaint |
| sent | Nullable date | UTC calendar date sent to company; not a resolution date |
| product / sub_product | Text | Original consumer-selected categories |
| issue / sub_issue | Text | Original issue categories; optional values may be Unknown |
| company | Text | Company identified in the public record |
| state | Text | Published state; missing retained as Unknown |
| channel | Text | How the complaint was submitted |
| response | Text | Published company response category |
| timely | Yes / No / Unknown | Published timeliness indicator |
| month | Date | First calendar day of received month |
| is_complete_month | Boolean | Received before the first day of the as-of month |
| is_timely | 0 / 1 | Timely equals Yes |
| is_known | 0 / 1 | Timely equals Yes or No |
| is_not_timely | 0 / 1 | Timely equals No |

`monthly_product`: month × product, 48 rows, counts of complaints/Yes/known/No/unknown. `issue_monthly`: month × product × issue. `company_summary`: company × product, record-weighted rate. None contains customer-base denominators, dollar losses, reimbursement, or resolution duration.
