# FMCG Case Study

A self-contained, synthetic data analytics case built to practice for the Statistics/Data Analyst role advertised by an FMCG. It gives you messy FMCG-style sales data, three realistic business problems, and a working toolchain in Python, SQL and Power BI, the tools named in the advert.

> **Disclaimer: All data is fictional and randomly generated (Courtesy: Claude AI). It is NOT the company's data and does not describe its actual products, customers or performance. Names of outlets and sales reps are invented. Use it for practice and portfolio purposes only.

---

## Contents

1. [Purpose](#1-purpose)
2. [The scenario and the three problems](#2-the-scenario-and-the-three-problems)
3. [Folder structure](#3-folder-structure)
4. [Data at a glance](#4-data-at-a-glance)
5. [Requirements](#5-requirements)
6. [Quick start](#6-quick-start)
7. [What each script does](#7-what-each-script-does)
8. [Power BI set-up (summary)](#8-power-bi-set-up-summary)
9. [Suggested way to work through the FMCG_CaseStudy](#9-suggested-way-to-work-through-the-FMCG_CaseStudy)
10. [Regenerating or modifying the data](#10-regenerating-or-modifying-the-data)
11. [Troubleshooting](#11-troubleshooting)
12. [Skills practiced](#12-skills-practised)
13. [Limitations](#13-limitations)

For detailed methods, expected findings and the Power BI report layout, see **`GUIDE.docx`**. This README covers the FMCG_CaseStudy itself: what is in it, how to run it, and how to fix problems.

---

## 1. Purpose

- Practice the full analyst workflow: **clean, analyse, model, visualize, recommend**.
- Show the same problem solved three ways (Python, SQL, Power BI) so you can talk about trade-offs in an interview.


## 2. The scenario and the three problems

You are the Statistics/Data Analyst at a fictional FMCG distributor in Ghana. It sells 12 products (beverages, household, food) through supermarkets, retail shops, kiosks and wholesalers across six regions, served by 18 sales reps. Data covers **January 2025 to September 2026**.

| # | Problem | Business question |

| 1 | Q3 2026 sales slowdown | Where exactly is the problem, how big is it, and what is causing it? |
| 2 | Sales rep target attainment | Who is missing target, and is it a performance issue or something else? |
| 3 | Q4 2026 demand and stock planning | What should we expect in Q4, and how much safety stock is needed so the problem in #1 does not repeat? |

Answers, expected numbers and write-ups are not here, so you can attempt the problems first.

## 3. Folder structure


FMCGCaseStudy/
├── README.md                    this file
├── data/
│   ├── raw/                     6 messy CSVs: START HERE
│   │   ├── sales_transactions_raw.csv
│   │   ├── products_raw.csv
│   │   ├── customers_raw.csv
│   │   ├── sales_reps_raw.csv
│   │   ├── sales_targets_raw.csv
│   │   └── deliveries_raw.csv
│   └── clean/                   produced by 01_clean_data.py (also included as a reference)
│       ├── fact_sales.csv
│       ├── fact_targets.csv
│       ├── fact_deliveries.csv
│       ├── dim_products.csv
│       ├── dim_customers.csv
│       ├── dim_reps.csv
│       └── data_quality_log.csv
├── python/
│   ├── 00_generate_demo_data.py regenerates the raw data
│   ├── 01_clean_data.py         raw -> clean
│   └── 02_analysis.py           solves the three problems, writes outputs/
├── sql/
│   ├── 00_load_to_sqlite.py     builds FMCG_demo.db from the clean CSVs
│   ├── 01_problem1_sales_decline.sql
│   ├── 02_problem2_rep_performance.sql
│   └── 03_problem3_forecast_and_safety_stock.sql
├── powerbi/
│   └── dax_measures.dax         calendar table, dim_region and all measures
└── outputs/                     result tables and charts from 02_analysis.py
```

Files created when you run things: `FMCG_demo.db` (in the FMCG_CaseStudy's root folder) and refreshed files in `data/clean/` and `outputs/`.

## 4. Data at a glance

| File (raw) | Grain | Rows |
|---|---|---|
| `sales_transactions_raw.csv` | one order line | 29,935 |
| `products_raw.csv` | one SKU | 12 |
| `customers_raw.csv` | one outlet | 300 |
| `sales_reps_raw.csv` | one sales rep | 18 |
| `sales_targets_raw.csv` | rep × month | 378 |
| `deliveries_raw.csv` | region × SKU × month | 1,520 |

After cleaning: **29,337** sales rows (duplicates and invalid dates removed) and **1,512** delivery rows. Every cleaning decision is recorded in `data/clean/data_quality_log.csv`.

**Column names in the sales file:** `order_id, order_date, customer_id, outlet_region, channel, sku, quantity, unit_price, discount_pct, sales_rep_id`. In the clean file, `outlet_region` becomes `region`, and `revenue` is added (`quantity × unit_price × (1 − discount_pct/100)`) along with a `qty_flag` column marking imputed or corrected quantities.

**Currency:** Ghana cedis (GHS). Prices, targets and revenue are illustrative.

**Data quality:** the raw files contain deliberate, realistic errors for you to find and fix (formats, spellings, text-as-number values, duplicates, missing values and outliers). The list of what was planted is in the guide.

## 5. Requirements

| Tool | Version | Used for |
|---|---|---|
| Python | 3.10 or newer (tested on 3.12) | cleaning, analysis, charts |
| pandas, numpy, matplotlib | recent versions (tested with pandas 3.0, numpy 2.4, matplotlib 3.10) | `pip install pandas numpy matplotlib` |
| SQL engine | SQLite 3.25+ (needed for window functions) or any SQL database | the `.sql` files |
| DB Browser for SQLite | optional, free | running queries with a visual interface |
| Power BI Desktop | current release (free, Windows only) | dashboards and DAX |
| Excel | optional | inspecting the raw files |

No internet connection is needed once the tools are installed.

## 6. Quick start

Open a terminal in the FMCG_CaseStudy's folder (the one that contains `python/`, `sql/` and `data/`), then:

```bash
# 1. install dependencies (once)
pip install pandas numpy matplotlib

# 2. clean the raw data  ->  data/clean/*.csv and data_quality_log.csv
python python/01_clean_data.py

# 3. solve the three problems  ->  prints results, writes outputs/
python python/02_analysis.py

# 4. build the SQL database  ->  FMCG_demo.db
python sql/00_load_to_sqlite.py
```

Then open `FMCG_demo.db` in DB Browser for SQLite (*Execute SQL* tab), and paste in the queries from `sql/`. For Power BI, follow section 8 and the guide.

**Run order matters:** `02_analysis.py` and `00_load_to_sqlite.py` need the files that `01_clean_data.py` creates.

> **Tip:** to practise the cleaning yourself, try writing your own cleaning code first (or use Power Query), then compare your result with `data/clean/` and the log.

## 7. What each script does

| Script | Input | Output | Notes |
|---|---|---|---|
| `00_generate_demo_data.py` | none | `data/raw/*.csv` | Fixed random seed, so it always produces the same data. |
| `01_clean_data.py` | `data/raw/*.csv` | `data/clean/*.csv`, `data_quality_log.csv` | Prints a summary of every fix and the before/after row counts. |
| `02_analysis.py` | `data/clean/*.csv` | `outputs/` (CSV tables and PNG charts) | Prints the results for all three problems. Overwrites earlier outputs. |
| `00_load_to_sqlite.py` | `data/clean/*.csv` | `FMCG_demo.db` | Replaces existing tables on each run. |

**Output files (in `outputs/`):**

| File | Problem |
|---|---|
| `p1_region_yoy.csv`, `p1_ashanti_category_yoy.csv`, `p1_supply_comparison.csv`, `p1_ashanti_beverages.png` | 1 |
| `p2_rep_attainment.csv`, `p2_rep_attainment.png` | 2 |
| `p3_forecast_detail.csv`, `p3_q4_forecast_by_region.csv`, `p3_ashanti_safety_stock.csv`, `p3_forecast.png` | 3 |

## 8. Power BI set-up (summary)

1. **Get Data → Text/CSV:** load the six files in `data/clean/` (not the log). Set date and numeric types.
2. **Create tables** from `powerbi/dax_measures.dax`: `Calendar` (mark as date table) and `dim_region`.
3. **Relationships (one-to-many, single direction):**
   - `Calendar[Date]` → `fact_sales[order_date]`, `fact_targets[month_start]`, `fact_deliveries[order_date]`
   - `dim_products[sku]` → `fact_sales[sku]`, `fact_deliveries[sku]`
   - `dim_reps[rep_id]` → `fact_sales[sales_rep_id]`, `fact_targets[rep_id]`
   - `dim_region[region]` → `fact_sales[region]`, `fact_deliveries[region]`
   - Do not link `dim_region` to `dim_reps` (avoids ambiguous paths).
4. **Add the measures** from the DAX file to a table called `_Measures`.
5. **Build three report pages:** Sales Health, Rep Performance, Outlook & Stock. Visual-by-visual instructions are in the guide.

A finished `.pbix` file is not included; building it is part of the exercise.

## 9. Suggested way to work through the FMCG_CaseStudy

1. **Inspect the raw files** in Excel and list every data problem you can find (15 to 20 minutes).
2. **Clean the data** yourself, then compare with `01_clean_data.py`, the clean files and the log.
3. **Attempt each problem** in your preferred tool before opening the guide.
4. **Repeat the analysis** in the other two tools and check the numbers agree.
5. **Build the Power BI report** and write a one-page summary for a non-technical manager.
6. **Practise explaining** your method aloud, including the assumptions you made and the limits of the forecast.

## 10. Regenerating or modifying the data

- To recreate the raw files exactly as supplied: `python python/00_generate_demo_data.py`. The seed is fixed inside the script.
- To create a different dataset, change the seed (`default_rng(2026)` and `random.seed(2026)`) or the parameters near the top of the script (regions, products, seasonality, channel mix, growth rate).
- The scenario events (the supply disruption starting in July 2026 and the differences in rep strength) are set in the generator. Edit them to build your own variations, then rerun `01_clean_data.py` and `02_analysis.py`.
- If you regenerate the data, the numbers quoted in the guide will change.

## 11. Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `ModuleNotFoundError: pandas` (or numpy, matplotlib) | Run `pip install pandas numpy matplotlib`. On some systems use `python -m pip install ...` or `pip3`. |
| `FileNotFoundError` for `data/clean/...` | Run `01_clean_data.py` first, and run scripts from inside the FMCG_CaseStudy's folder. |
| SQL error mentioning `LAG`, `RANK` or `OVER` | Your SQLite is older than 3.25. Update DB Browser for SQLite or use another SQL engine. |
| SQL date functions (`strftime`, `substr`) not recognised | The queries are written for SQLite. For SQL Server use `FORMAT`/`LEFT`, for MySQL `DATE_FORMAT`, and for PostgreSQL `TO_CHAR`. |
| Power BI dates load as text | In Power Query, select the column, then *Transform → Data Type → Date*. |
| Power BI says a relationship is ambiguous or inactive | Check that each relationship is one-to-many and single direction, and that `dim_region` is not linked to `dim_reps`. |
| Time-intelligence measures (`Revenue PY`, YoY) return blanks | Confirm `Calendar` is marked as the date table and that `Calendar[Date]` is on the axis instead of a column from the fact table. |
| Charts not created | `matplotlib` is missing, or `outputs/` is read-only. Reinstall and check folder permissions. |
| Numbers differ slightly from the guide | You probably regenerated the data with a different seed or changed parameters. |

## 12. Skills practised

- **Data cleaning:** date parsing, standardising text categories, type conversion, de-duplication, outlier handling, imputation with justification, data-quality logging.
- **Python:** pandas transformations, grouping and joins, growth and attainment calculations, simple forecasting and back-testing, matplotlib charts.
- **SQL:** joins, CTEs, conditional aggregation, window functions (`LAG`, `RANK`), date handling.
- **Power BI:** data modelling, Power Query, DAX time intelligence, conditional formatting, slicers, KPI cards.
- **Statistics for business:** year-on-year and trend comparison, target attainment, forecast error (MAPE), safety stock and service levels.
- **Communication:** turning findings into recommendations and structuring an interview answer (STAR).

## 13. Limitations

- The data is simulated, so real-world data will be messier and less tidy in its patterns.
- The forecasting method is deliberately simple (same month last year × growth). It is meant for teaching and back-testing, not for production use.
- Monthly figures are noisy by design; quarterly or rolling averages give clearer signals.
- Product prices, costs, targets and safety-stock parameters are illustrative.
- Only the SQLite dialect is tested. Other database engines may need small syntax changes.

---

*Prepared as interview and portfolio practice for the FMCG Statistics/Data Analyst position.*
