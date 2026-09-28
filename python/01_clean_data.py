"""STEP 1 - Clean the raw CSVs. Run: python python/01_clean_data.py
Reads data/raw/*.csv, writes data/clean/*.csv and data/clean/data_quality_log.csv"""
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"; CLEAN.mkdir(exist_ok=True)
log = []
def note(table, issue, n, action): log.append({"table": table, "issue": issue, "rows_affected": int(n), "action": action})

# ---------- reusable helpers ----------
def parse_dates(s, fmts=("%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%d-%b-%y")):
    """Mixed date formats -> datetime. Try each format on what is still unparsed."""
    s = s.astype("string").str.strip(); out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for f in fmts:
        todo = out.isna() & s.notna()
        out[todo] = pd.to_datetime(s[todo], format=f, errors="coerce")
    return out

def clean_region(s):
    x = s.astype("string").str.strip().str.lower()
    m = {"accra": "Greater Accra", "ashanti": "Ashanti", "western": "Western", "eastern": "Eastern", "northern": "Northern", "volta": "Volta"}
    out = pd.Series(pd.NA, index=s.index, dtype="string")
    for k, v in m.items(): out[x.str.contains(k, na=False)] = v
    return out

def clean_channel(s):
    x = s.astype("string").str.lower().str.replace(" ", "", regex=False)
    m = {"supermarket": "Supermarket", "retail": "Retail Shop", "kiosk": "Kiosk", "wholesale": "Wholesale"}
    out = pd.Series(pd.NA, index=s.index, dtype="string")
    for k, v in m.items(): out[x.str.contains(k, na=False)] = v
    return out

def to_number(s):
    """'GHS 18.50' / '12 ctn' / '5%' / '25,400' -> float"""
    return pd.to_numeric(s.astype("string").str.replace(r"[^0-9.\-]", "", regex=True).replace("", pd.NA), errors="coerce").astype("float64")

# ---------- products ----------
p = pd.read_csv(RAW / "products_raw.csv")
p["sku"] = p.sku.str.strip().str.upper(); p["category"] = p.category.str.strip().str.title()
p["list_price"] = to_number(p.list_price)
note("products", "sku case/whitespace, category case, price stored as text", 12, "standardised")
p.to_csv(CLEAN / "dim_products.csv", index=False)

# ---------- customers ----------
c = pd.read_csv(RAW / "customers_raw.csv", dtype=str)
c["customer_id"] = c.customer_id.str.strip().str.upper(); c["outlet_name"] = c.outlet_name.str.strip().str.title()
c["region"] = clean_region(c.region); c["channel"] = clean_channel(c.channel)
note("customers", "region/channel spelling variants, name case & spaces", len(c), "mapped to standard values")
c.to_csv(CLEAN / "dim_customers.csv", index=False)

# ---------- reps ----------
r = pd.read_csv(RAW / "sales_reps_raw.csv", dtype=str)
r["rep_name"] = r.rep_name.str.strip().str.title(); r["region"] = clean_region(r.region); r["hire_date"] = parse_dates(r.hire_date)
note("sales_reps", "name case, region variants, mixed date formats", len(r), "standardised")
r.to_csv(CLEAN / "dim_reps.csv", index=False)

# ---------- sales transactions ----------
s = pd.read_csv(RAW / "sales_transactions_raw.csv", dtype=str)
n0 = len(s)
dup = s.duplicated().sum(); s = s.drop_duplicates(); note("sales", "exact duplicate rows", dup, "dropped")
s["order_date"] = parse_dates(s.order_date)
bad = s.order_date.isna().sum(); s = s.dropna(subset=["order_date"]); note("sales", "missing/invalid order_date ('N/A')", bad, "dropped (cannot be placed in time)")
s["customer_id"] = s.customer_id.str.strip().str.upper(); s["sku"] = s.sku.str.strip().str.upper()
s["region"] = clean_region(s.outlet_region); s["channel"] = clean_channel(s.channel); s = s.drop(columns="outlet_region")
note("sales", "region/channel spelling variants", len(s), "mapped to standard values")

s["quantity_raw"] = s.quantity
s["quantity"] = to_number(s.quantity)
neg = (s.quantity < 0).sum(); s["quantity"] = s.quantity.abs(); note("sales", "negative quantity (assumed sign entry error)", neg, "converted to positive")
# outliers: > 10x the median for the same SKU & channel are treated as keying errors (extra zeros)
med = s.groupby(["sku", "channel"]).quantity.transform("median")
out = s.quantity > 10 * med; s["qty_flag"] = ""; s.loc[out, "qty_flag"] = "outlier_fixed"
s.loc[out, "quantity"] = med[out]; note("sales", "quantity > 10x median for SKU/channel (typing errors)", out.sum(), "replaced with median, flagged")
miss = s.quantity.isna(); s.loc[miss, "quantity"] = med[miss]; s.loc[miss, "qty_flag"] = "imputed"
note("sales", "missing quantity", miss.sum(), "imputed with SKU/channel median, flagged")

s["unit_price"] = to_number(s.unit_price)
s["ym"] = s.order_date.dt.to_period("M")
mprice = s.groupby(["sku", "ym"]).unit_price.transform("median")
pm = s.unit_price.isna(); s.loc[pm, "unit_price"] = mprice[pm]; note("sales", "missing unit_price", pm.sum(), "filled with same-SKU, same-month median price")
s["discount_pct"] = to_number(s.discount_pct)
dm = s.discount_pct.isna(); s["discount_pct"] = s.discount_pct.fillna(0); note("sales", "missing discount_pct", dm.sum(), "assumed 0")
cmap = c.set_index("customer_id").rep_id
rm = s.sales_rep_id.isna(); s.loc[rm, "sales_rep_id"] = s.loc[rm, "customer_id"].map(cmap)
note("sales", "missing sales_rep_id", rm.sum(), "looked up from customer master")
s["revenue"] = (s.quantity * s.unit_price * (1 - s.discount_pct / 100)).round(2)
s = s.drop(columns=["ym", "quantity_raw"]).sort_values(["order_date", "order_id"])
s["order_date"] = s.order_date.dt.strftime("%Y-%m-%d")
s.to_csv(CLEAN / "fact_sales.csv", index=False)

# ---------- targets ----------
t = pd.read_csv(RAW / "sales_targets_raw.csv", dtype=str)
t["month_start"] = parse_dates(t.month, fmts=("%b-%Y", "%Y-%m")).dt.strftime("%Y-%m-01")
t["target_amount"] = to_number(t.target_amount); t = t.drop(columns="month")
t = t.sort_values(["rep_id", "month_start"]); m = t.target_amount.isna()
t["target_amount"] = t.groupby("rep_id").target_amount.transform(lambda x: x.interpolate(limit_direction="both"))
note("targets", "blank target_amount / month in 2 text formats", m.sum(), "interpolated between neighbouring months; months parsed")
t.to_csv(CLEAN / "fact_targets.csv", index=False)

# ---------- deliveries ----------
d = pd.read_csv(RAW / "deliveries_raw.csv", dtype=str)
dup = d.duplicated().sum(); d = d.drop_duplicates(); note("deliveries", "duplicate rows", dup, "dropped")
d["sku"] = d.sku.str.strip().str.upper(); d["region"] = clean_region(d.region)
d["order_date"] = parse_dates(d.order_date); d["delivery_date"] = parse_dates(d.delivery_date)
for col in ["qty_ordered", "qty_delivered", "stockout_days"]:
    na = d[col].isin(["N/A", "n/a", ""]).sum(); d[col] = to_number(d[col])
    if na: note("deliveries", f"'N/A' in {col}", na, "set to null (excluded from averages, not guessed)")
d["lead_time_days"] = (d.delivery_date - d.order_date).dt.days
d["fill_rate"] = (d.qty_delivered / d.qty_ordered).round(3)
for col in ["order_date", "delivery_date"]: d[col] = d[col].dt.strftime("%Y-%m-%d")
d.to_csv(CLEAN / "fact_deliveries.csv", index=False)

pd.DataFrame(log).to_csv(CLEAN / "data_quality_log.csv", index=False)
print(pd.DataFrame(log).to_string(index=False)); print(f"\nsales rows: {n0} raw -> {len(s)} clean")
