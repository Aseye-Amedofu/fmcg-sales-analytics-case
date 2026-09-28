"""STEP 2 - Solve the three business problems with pandas. Run: python python/02_analysis.py
Needs data/clean/*.csv (run 01_clean_data.py first). Writes tables + charts to outputs/."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C, OUT = ROOT / "data" / "clean", ROOT / "outputs"; OUT.mkdir(exist_ok=True)
sales = pd.read_csv(C / "fact_sales.csv", parse_dates=["order_date"])
prod = pd.read_csv(C / "dim_products.csv"); reps = pd.read_csv(C / "dim_reps.csv")
targets = pd.read_csv(C / "fact_targets.csv", parse_dates=["month_start"])
deliv = pd.read_csv(C / "fact_deliveries.csv", parse_dates=["order_date", "delivery_date"])
sales = sales.merge(prod[["sku", "category", "unit_cost"]], on="sku")
sales["ym"] = sales.order_date.dt.to_period("M"); deliv["ym"] = deliv.order_date.dt.to_period("M")
deliv = deliv.merge(prod[["sku", "category"]], on="sku")
Q3_26 = [pd.Period(x, "M") for x in ("2026-07", "2026-08", "2026-09")]
Q3_25 = [p - 12 for p in Q3_26]
H1_26 = pd.period_range("2026-01", "2026-06", freq="M"); H1_25 = pd.period_range("2025-01", "2025-06", freq="M")

# =====================================================================
# PROBLEM 1 - Which region/category drove the Q3 2026 sales decline, and why?
# =====================================================================
q3 = sales[sales.ym.isin(Q3_26)].groupby("region").revenue.sum()
q3ly = sales[sales.ym.isin(Q3_25)].groupby("region").revenue.sum()
h1g = sales[sales.ym.isin(H1_26)].groupby("region").revenue.sum() / sales[sales.ym.isin(H1_25)].groupby("region").revenue.sum()
p1 = pd.DataFrame({"q3_2026": q3, "q3_2025": q3ly}); p1["yoy_%"] = ((p1.q3_2026 / p1.q3_2025 - 1) * 100).round(1)
p1["h1_yoy_%"] = ((h1g - 1) * 100).round(1); p1["growth_gap_pts"] = (p1["yoy_%"] - p1["h1_yoy_%"]).round(1)
p1.round(0).to_csv(OUT / "p1_region_yoy.csv"); print("\n[P1] Region YoY (Q3 2026 vs Q3 2025) vs H1 trend\n", p1.round(1))

a = sales[sales.region == "Ashanti"]
cat = pd.DataFrame({"q3_2026": a[a.ym.isin(Q3_26)].groupby("category").revenue.sum(), "q3_2025": a[a.ym.isin(Q3_25)].groupby("category").revenue.sum()})
cat["yoy_%"] = ((cat.q3_2026 / cat.q3_2025 - 1) * 100).round(1); cat.round(0).to_csv(OUT / "p1_ashanti_category_yoy.csv")
print("\n[P1] Ashanti by category\n", cat.round(1))

dq3 = deliv[deliv.ym.isin(Q3_26)].copy(); dq3["group"] = np.where((dq3.region == "Ashanti") & (dq3.category == "Beverages"), "Ashanti Beverages", "All other")
sup = dq3.groupby("group").agg(avg_lead_days=("lead_time_days", "mean"), avg_stockout_days=("stockout_days", "mean"), avg_fill_rate=("fill_rate", "mean")).round(2)
sup.to_csv(OUT / "p1_supply_comparison.csv"); print("\n[P1] Supply performance Q3 2026\n", sup)

# estimated lost revenue = what H1 growth trend predicts minus actual
def forecast_month(df, month, growth): return df[df.ym == month - 12].revenue.sum() * growth
ab = sales[(sales.region == "Ashanti") & (sales.category == "Beverages")]
g = ab[ab.ym.isin(H1_26)].revenue.sum() / ab[ab.ym.isin(H1_25)].revenue.sum()
exp = sum(forecast_month(ab, m, g) for m in Q3_26); act = ab[ab.ym.isin(Q3_26)].revenue.sum()
print(f"\n[P1] Ashanti Beverages Q3 2026: expected GHS {exp:,.0f} | actual GHS {act:,.0f} | estimated lost sales GHS {exp-act:,.0f} ({(1-act/exp)*100:.0f}%)")

idx = sales[sales.category == "Beverages"].assign(grp=lambda x: np.where(x.region == "Ashanti", "Ashanti", "Other regions")).groupby(["ym", "grp"]).revenue.sum().unstack()
idx = idx / idx.iloc[:6].mean() * 100
idx = idx.rolling(3).mean()          # monthly values are noisy -> 3-month rolling average
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
idx.plot(ax=ax[0], marker="o"); ax[0].axvline(pd.Period("2026-07", "M"), color="grey", ls="--"); ax[0].set_title("Beverage revenue index, 3-month rolling (H1 2025 = 100)"); ax[0].set_xlabel("")
sup[["avg_lead_days", "avg_stockout_days"]].plot.bar(ax=ax[1], rot=0); ax[1].set_title("Q3 2026: delivery lead time & stock-out days"); ax[1].set_xlabel("")
plt.tight_layout(); plt.savefig(OUT / "p1_ashanti_beverages.png", dpi=130); plt.close()

# =====================================================================
# PROBLEM 2 - Which sales reps are missing target, and is it performance or supply?
# =====================================================================
rev = sales.groupby(["sales_rep_id", sales.order_date.dt.to_period("M").dt.to_timestamp()]).revenue.sum().rename("actual").reset_index()
rev.columns = ["rep_id", "month_start", "actual"]
att = targets.merge(rev, on=["rep_id", "month_start"], how="left").fillna({"actual": 0})
att["ym"] = att.month_start.dt.to_period("M")
def attain(months): x = att[att.ym.isin(months)].groupby("rep_id")[["actual", "target_amount"]].sum(); return (x.actual / x.target_amount * 100).round(1)
res = reps[["rep_id", "rep_name", "region"]].set_index("rep_id")
res["h1_2026_%"], res["q3_2026_%"] = attain(H1_26), attain(Q3_26)
def classify(r):
    if r["h1_2026_%"] < 90: return "Persistent under-performance"
    if r["q3_2026_%"] < 90: return "Recent drop - check supply"
    if r["q3_2026_%"] >= 110: return "Star performer"
    return "On track"
res["status"] = res.apply(classify, axis=1); res = res.sort_values("q3_2026_%")
res.to_csv(OUT / "p2_rep_attainment.csv"); print("\n[P2] Rep attainment\n", res.to_string())
col = {"Persistent under-performance": "#c0392b", "Recent drop - check supply": "#e67e22", "Star performer": "#27ae60", "On track": "#7f8c8d"}
fig, ax = plt.subplots(figsize=(9, 5)); ax.barh(res.rep_name, res["q3_2026_%"], color=res.status.map(col))
ax.axvline(100, color="black", ls="--"); ax.set_title("Q3 2026 target attainment by rep (%)")
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=v) for v in col.values()], labels=list(col), fontsize=8, loc="lower right")
plt.tight_layout(); plt.savefig(OUT / "p2_rep_attainment.png", dpi=130); plt.close()

# =====================================================================
# PROBLEM 3 - Forecast Q4 2026 demand and set safety stock so stock-outs don't repeat
# =====================================================================
mon = sales.groupby(["region", "category", "ym"]).revenue.sum().reset_index()
rows = []
for (rg, ct), df in mon.groupby(["region", "category"]):
    g = df[df.ym.isin(H1_26)].revenue.sum() / df[df.ym.isin(H1_25)].revenue.sum()     # YoY growth from H1
    for m in list(Q3_26) + [pd.Period(x, "M") for x in ("2026-10", "2026-11", "2026-12")]:
        base = df[df.ym == m - 12].revenue.sum()
        rows.append((rg, ct, str(m), round(base * g), round(df[df.ym == m].revenue.sum()) if m in Q3_26 else np.nan))
fc = pd.DataFrame(rows, columns=["region", "category", "month", "forecast", "actual"])
bt = fc.dropna(subset=["actual"]); bt = bt[~((bt.region == "Ashanti") & (bt.category == "Beverages"))]
mape = (abs(bt.actual - bt.forecast) / bt.actual).mean() * 100
print(f"\n[P3] Back-test (Jul-Sep 2026, excl. supply-hit group): MAPE = {mape:.1f}%")
q4 = fc[fc.month >= "2026-10"].groupby("region").forecast.sum(); q4.to_csv(OUT / "p3_q4_forecast_by_region.csv"); print("[P3] Q4 2026 revenue forecast (GHS)\n", q4)
fc.to_csv(OUT / "p3_forecast_detail.csv", index=False)

# safety stock (Ashanti beverages): SS = z * sqrt( (L/30)*sd_m^2 + (d_m/30)^2 * sd_L^2 ), z=1.65 (95% service)
Z = 1.65; units = sales.groupby(["region", "sku", "ym"]).quantity.sum().reset_index()
u = units[(units.region == "Ashanti") & units.sku.isin(prod[prod.category == "Beverages"].sku) & (units.ym >= pd.Period("2025-07", "M")) & (units.ym <= pd.Period("2026-06", "M"))]
ss = u.groupby("sku").quantity.agg(avg_monthly_units="mean", sd_monthly_units="std").round(1)
lt_norm = deliv[(deliv.region == "Ashanti") & (deliv.ym < pd.Period("2026-07", "M")) & deliv.sku.isin(ss.index)].groupby("sku").lead_time_days.agg(["mean", "std"])
lt_bad = deliv[(deliv.region == "Ashanti") & (deliv.ym >= pd.Period("2026-07", "M")) & deliv.sku.isin(ss.index)].groupby("sku").lead_time_days.agg(["mean", "std"])
def safety(L, sdL, d, sd): return Z * np.sqrt((L / 30) * sd**2 + (d / 30) ** 2 * sdL**2)
ss["lead_days_normal"] = lt_norm["mean"].round(1); ss["lead_days_now"] = lt_bad["mean"].round(1)
ss["safety_stock_normal"] = safety(lt_norm["mean"], lt_norm["std"], ss.avg_monthly_units, ss.sd_monthly_units).round(0)
ss["safety_stock_now"] = safety(lt_bad["mean"], lt_bad["std"], ss.avg_monthly_units, ss.sd_monthly_units).round(0)
ss["reorder_point_now"] = (ss.avg_monthly_units / 30 * lt_bad["mean"] + ss.safety_stock_now).round(0)
ss.to_csv(OUT / "p3_ashanti_safety_stock.csv"); print("\n[P3] Ashanti beverage safety stock (units)\n", ss)

fig, ax = plt.subplots(figsize=(9, 4)); tot = fc.groupby("month")[["forecast", "actual"]].sum()
tot.plot(ax=ax, marker="o"); ax.set_title("Forecast vs actual revenue (GHS) - Jul-Dec 2026"); plt.tight_layout(); plt.savefig(OUT / "p3_forecast.png", dpi=130)
