-- Grain: month x product. A complete 24-month grid prevents missing categories
-- from silently shifting the month-over-month comparison.
CREATE OR REPLACE TABLE monthly_product AS
WITH grid AS (
 SELECT m.month,p.product FROM
 (SELECT DISTINCT month FROM complaints WHERE is_complete_month) m CROSS JOIN
 (SELECT DISTINCT product FROM complaints) p
), counts AS (
 SELECT month,product,count(*) complaints,sum(is_timely) timely_yes,
 sum(is_known) known,sum(is_not_timely) timely_no
 FROM complaints WHERE is_complete_month GROUP BY ALL
)
SELECT g.month,g.product,coalesce(c.complaints,0) complaints,
coalesce(c.timely_yes,0) timely_yes,coalesce(c.known,0) known,
coalesce(c.timely_no,0) timely_no,
coalesce(c.complaints-c.known,0) AS "unknown"
FROM grid g LEFT JOIN counts c USING(month,product) ORDER BY g.month,g.product;

CREATE OR REPLACE TABLE issue_monthly AS
SELECT month,product,issue,count(*) complaints,sum(is_timely) timely_yes,
sum(is_known) known,sum(is_not_timely) timely_no
FROM complaints WHERE is_complete_month GROUP BY ALL ORDER BY month,product,issue;

CREATE OR REPLACE TABLE company_summary AS
SELECT company,product,count(*) complaints,sum(is_timely) timely_yes,
sum(is_known) known,sum(is_not_timely) timely_no,
sum(is_timely)*1.0/nullif(sum(is_known),0) timely_rate
FROM complaints WHERE is_complete_month GROUP BY ALL ORDER BY complaints DESC,company,product;
