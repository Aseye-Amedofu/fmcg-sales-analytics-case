-- PROBLEM 1: Which region/category caused the Q3-2026 decline, and is supply the cause?
-- Dialect: SQLite (notes for SQL Server / MySQL / PostgreSQL at the bottom)

-- 1a. Monthly revenue by region
SELECT strftime('%Y-%m', order_date) AS ym, region, ROUND(SUM(revenue), 0) AS revenue
FROM fact_sales
GROUP BY ym, region
ORDER BY ym, region;

-- 1b. Q3-2026 vs Q3-2025 by region and category, compared with the H1 growth trend
WITH s AS (
  SELECT f.region, p.category, substr(f.order_date, 1, 7) AS ym, f.revenue
  FROM fact_sales f JOIN dim_products p ON p.sku = f.sku
),
agg AS (
  SELECT region, category,
         SUM(CASE WHEN ym BETWEEN '2026-07' AND '2026-09' THEN revenue END) AS q3_26,
         SUM(CASE WHEN ym BETWEEN '2025-07' AND '2025-09' THEN revenue END) AS q3_25,
         SUM(CASE WHEN ym BETWEEN '2026-01' AND '2026-06' THEN revenue END) AS h1_26,
         SUM(CASE WHEN ym BETWEEN '2025-01' AND '2025-06' THEN revenue END) AS h1_25
  FROM s GROUP BY region, category
)
SELECT region, category,
       ROUND(100.0 * (q3_26 / q3_25 - 1), 1) AS q3_yoy_pct,
       ROUND(100.0 * (h1_26 / h1_25 - 1), 1) AS h1_yoy_pct,
       ROUND(100.0 * (q3_26 / q3_25 - h1_26 / h1_25), 1) AS growth_gap_pts
FROM agg
ORDER BY growth_gap_pts ASC;      -- the worst gap is at the top

-- 1c. Supply performance in Q3-2026: is the same group hurt?
SELECT d.region, p.category,
       ROUND(AVG(d.lead_time_days), 1) AS avg_lead_days,
       ROUND(AVG(d.stockout_days), 1)  AS avg_stockout_days,
       ROUND(AVG(d.fill_rate), 2)      AS avg_fill_rate
FROM fact_deliveries d JOIN dim_products p ON p.sku = d.sku
WHERE d.order_date >= '2026-07-01'
GROUP BY d.region, p.category
ORDER BY avg_stockout_days DESC;

-- 1d. Month-on-month change using a window function (LAG)
WITH m AS (
  SELECT strftime('%Y-%m', f.order_date) AS ym, SUM(f.revenue) AS revenue
  FROM fact_sales f JOIN dim_products p ON p.sku = f.sku
  WHERE f.region = 'Ashanti' AND p.category = 'Beverages'
  GROUP BY ym
)
SELECT ym, ROUND(revenue, 0) AS revenue,
       ROUND(100.0 * (revenue / LAG(revenue) OVER (ORDER BY ym) - 1), 1) AS mom_pct,
       ROUND(100.0 * (revenue / LAG(revenue, 12) OVER (ORDER BY ym) - 1), 1) AS yoy_pct
FROM m ORDER BY ym;

-- Dialect notes: SQL Server -> FORMAT(order_date,'yyyy-MM') / LEFT(CONVERT(varchar,order_date,23),7);
-- MySQL -> DATE_FORMAT(order_date,'%Y-%m'); PostgreSQL -> TO_CHAR(order_date,'YYYY-MM').
