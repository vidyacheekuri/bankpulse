-- Run after: python -m bankpulse.pipeline
-- Which issue contributed most to the change between the last two complete months?
WITH recent AS (SELECT DISTINCT month FROM issue_monthly ORDER BY month DESC LIMIT 2),
endpoints AS (SELECT min(month) previous,max(month) current FROM recent)
SELECT issue,
sum(CASE WHEN month=e.previous THEN complaints ELSE 0 END) previous_count,
sum(CASE WHEN month=e.current THEN complaints ELSE 0 END) current_count,
current_count-previous_count change
FROM issue_monthly CROSS JOIN endpoints e GROUP BY issue ORDER BY change DESC;

-- Which product has the highest share of explicitly non-timely responses?
-- Unknown statuses are excluded from the denominator, not treated as timely.
SELECT product,sum(timely_no) non_timely,sum(known) known_status,
sum(timely_no)*1.0/nullif(sum(known),0) non_timely_rate
FROM monthly_product GROUP BY product;

-- Response mix is categorical. A closure category is not a resolution duration.
SELECT response,count(*) complaints FROM complaints WHERE is_complete_month
GROUP BY response ORDER BY complaints DESC;
