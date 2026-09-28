-- PROBLEM 3: Q4-2026 demand forecast (seasonal naive x growth) and safety stock for Ashanti beverages

-- 3a. Forecast = same month last year x (H1-2026 / H1-2025 growth), by region
WITH m AS (
  SELECT f.region, substr(f.order_date, 1, 7) AS ym, SUM(f.revenue) AS revenue
  FROM fact_sales f GROUP BY f.region, ym
),
g AS (
  SELECT region,
         SUM(CASE WHEN ym BETWEEN '2026-01' AND '2026-06' THEN revenue END) /
         SUM(CASE WHEN ym BETWEEN '2025-01' AND '2025-06' THEN revenue END) AS growth
  FROM m GROUP BY region
)
SELECT m.region, ROUND(g.growth, 3) AS h1_growth_factor,
       ROUND(SUM(m.revenue * g.growth), 0) AS q4_2026_forecast
FROM m JOIN g ON g.region = m.region
WHERE m.ym IN ('2025-10', '2025-11', '2025-12')
GROUP BY m.region, g.growth
ORDER BY q4_2026_forecast DESC;

-- 3b. Demand and lead-time inputs for safety stock (Ashanti beverages)
--     SS = 1.65 * SQRT( (L/30) * var_demand + (avg_demand/30)^2 * var_lead )   -> finish the maths in Excel/Python/Power BI
WITH monthly AS (
  SELECT f.sku, substr(f.order_date, 1, 7) AS ym, SUM(f.quantity) AS units
  FROM fact_sales f JOIN dim_products p ON p.sku = f.sku
  WHERE f.region = 'Ashanti' AND p.category = 'Beverages'
    AND substr(f.order_date, 1, 7) BETWEEN '2025-07' AND '2026-06'
  GROUP BY f.sku, ym
),
demand AS (
  SELECT sku, AVG(units) AS avg_monthly_units,
         AVG(units * units) - AVG(units) * AVG(units) AS var_monthly_units   -- population variance (sd = square root)
  FROM monthly GROUP BY sku
),
lead AS (
  SELECT sku,
         AVG(CASE WHEN order_date <  '2026-07-01' THEN lead_time_days END) AS lead_normal,
         AVG(CASE WHEN order_date >= '2026-07-01' THEN lead_time_days END) AS lead_now
  FROM fact_deliveries WHERE region = 'Ashanti' GROUP BY sku
)
SELECT d.sku, ROUND(d.avg_monthly_units, 0) AS avg_monthly_units, ROUND(d.var_monthly_units, 0) AS var_monthly_units,
       ROUND(l.lead_normal, 1) AS lead_days_normal, ROUND(l.lead_now, 1) AS lead_days_now,
       ROUND(d.avg_monthly_units / 30.0 * l.lead_now, 0) AS demand_during_current_lead_time
FROM demand d JOIN lead l ON l.sku = d.sku;
