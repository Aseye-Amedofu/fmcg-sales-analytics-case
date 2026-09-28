-- PROBLEM 2: Who is missing target, and is it persistent under-performance or a recent (supply-related) drop?
WITH actual AS (
  SELECT sales_rep_id AS rep_id, substr(order_date, 1, 7) AS ym, SUM(revenue) AS actual
  FROM fact_sales GROUP BY sales_rep_id, ym
),
tgt AS (
  SELECT rep_id, substr(month_start, 1, 7) AS ym, target_amount FROM fact_targets
),
joined AS (
  SELECT t.rep_id, t.ym, t.target_amount, COALESCE(a.actual, 0) AS actual
  FROM tgt t LEFT JOIN actual a ON a.rep_id = t.rep_id AND a.ym = t.ym
),
rep_att AS (
  SELECT rep_id,
         100.0 * SUM(CASE WHEN ym BETWEEN '2026-01' AND '2026-06' THEN actual END)
               / SUM(CASE WHEN ym BETWEEN '2026-01' AND '2026-06' THEN target_amount END) AS h1_att,
         100.0 * SUM(CASE WHEN ym BETWEEN '2026-07' AND '2026-09' THEN actual END)
               / SUM(CASE WHEN ym BETWEEN '2026-07' AND '2026-09' THEN target_amount END) AS q3_att
  FROM joined GROUP BY rep_id
)
SELECT r.rep_id, r.rep_name, r.region,
       ROUND(a.h1_att, 1) AS h1_2026_pct, ROUND(a.q3_att, 1) AS q3_2026_pct,
       RANK() OVER (ORDER BY a.q3_att DESC) AS q3_rank,
       CASE WHEN a.h1_att < 90 THEN 'Persistent under-performance'
            WHEN a.q3_att < 90 THEN 'Recent drop - check supply'
            WHEN a.q3_att >= 110 THEN 'Star performer'
            ELSE 'On track' END AS status
FROM rep_att a JOIN dim_reps r ON r.rep_id = a.rep_id
ORDER BY a.q3_att;

-- Attainment by region (Q3 2026) - self-contained version
WITH actual AS (
  SELECT sales_rep_id AS rep_id, substr(order_date, 1, 7) AS ym, SUM(revenue) AS actual
  FROM fact_sales GROUP BY sales_rep_id, ym
)
SELECT r.region,
       ROUND(100.0 * SUM(COALESCE(a.actual, 0)) / SUM(t.target_amount), 1) AS q3_attainment_pct
FROM fact_targets t
JOIN dim_reps r ON r.rep_id = t.rep_id
LEFT JOIN actual a ON a.rep_id = t.rep_id AND a.ym = substr(t.month_start, 1, 7)
WHERE substr(t.month_start, 1, 7) BETWEEN '2026-07' AND '2026-09'
GROUP BY r.region ORDER BY q3_attainment_pct;
