"""Generate the synthetic FMCG demo dataset (raw + deliberately dirty).
Run:  python python/00_generate_demo_data.py
All data is fictional and for training use only."""
import numpy as np, pandas as pd, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"; RAW.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(2026); random.seed(2026)

REGIONS = ["Greater Accra", "Ashanti", "Western", "Eastern", "Northern", "Volta"]
REGION_W = [0.24, 0.22, 0.16, 0.14, 0.12, 0.12]
CHANNELS = ["Supermarket", "Retail Shop", "Kiosk", "Wholesale"]
CH_W = [0.15, 0.40, 0.35, 0.10]
CH_FACTOR = {"Supermarket": 1.5, "Retail Shop": 1.0, "Kiosk": 0.5, "Wholesale": 2.5}
CH_QTY = {"Supermarket": (16, 3), "Retail Shop": (8, 2), "Kiosk": (4, 1), "Wholesale": (45, 8)}   # (mean, sd) units per line

PRODUCTS = [
 ("SKU001", "Pure Spring Water 500ml (12-pack)", "Beverages", 18.0, 12.5, 12),
 ("SKU002", "Tropical Juice 1L (6-pack)", "Beverages", 42.0, 30.0, 6),
 ("SKU003", "Malt Drink 330ml (24-pack)", "Beverages", 96.0, 70.0, 24),
 ("SKU004", "Energy Drink 250ml (24-pack)", "Beverages", 110.0, 80.0, 24),
 ("SKU005", "Laundry Detergent 1kg", "Household", 28.0, 19.0, 1),
 ("SKU006", "Bath Soap (12-pack)", "Household", 36.0, 24.0, 12),
 ("SKU007", "Toothpaste 100g (12-pack)", "Household", 54.0, 38.0, 12),
 ("SKU008", "Tomato Paste 400g (12-tin)", "Food", 66.0, 48.0, 12),
 ("SKU009", "Cooking Oil 1L (12-pack)", "Food", 168.0, 135.0, 12),
 ("SKU010", "Rice 5kg", "Food", 88.0, 68.0, 1),
 ("SKU011", "Cream Biscuits (24-pack)", "Food", 60.0, 42.0, 24),
 ("SKU012", "Instant Noodles (40-pack)", "Food", 72.0, 52.0, 40),
]
SKU_W = np.array([1.3, 1.0, 0.8, 0.7, 0.9, 0.8, 0.7, 0.9, 0.6, 0.8, 0.8, 0.9]); SKU_W /= SKU_W.sum()
prod = pd.DataFrame(PRODUCTS, columns=["sku", "product_name", "category", "list_price", "unit_cost", "pack_size"])
CAT = dict(zip(prod.sku, prod.category)); PRICE = dict(zip(prod.sku, prod.list_price))

SEASON = {1: .92, 2: .95, 3: 1.0, 4: 1.08, 5: 1.0, 6: .97, 7: .98, 8: 1.0, 9: 1.02, 10: 1.05, 11: 1.12, 12: 1.30}
MONTHS = pd.period_range("2025-01", "2026-09", freq="M")
SHOCK_START = pd.Period("2026-07", freq="M")

NAMES = ["Kwame Mensah","Ama Serwaa","Kofi Boateng","Akosua Owusu","Yaw Darko","Abena Frimpong",
         "Kwesi Appiah","Efua Quaye","Nii Lamptey","Esi Ansah","Mohammed Alhassan","Fatima Iddrisu",
         "Selorm Agbenyo","Mawuli Tetteh","Edem Kporha","Kojo Antwi","Adjoa Bonsu","Issah Mumuni"]
FACT = {"R03": 1.25, "R08": 1.20, "R14": 0.78, "R16": 0.72, "R12": 0.80}
reps = []
for i, r in enumerate(REGIONS):
    for j in range(3):
        rid = f"R{i*3+j+1:02d}"
        reps.append((rid, NAMES[i*3+j], r, FACT.get(rid, round(float(rng.normal(1.0, 0.06)), 2))))
reps = pd.DataFrame(reps, columns=["rep_id", "rep_name", "region", "factor"])
reps["hire_date"] = pd.to_datetime("2019-01-01") + pd.to_timedelta(rng.integers(0, 1800, len(reps)), unit="D")

pre = ["Adwoa's", "Nana's", "Golden", "Royal", "Unity", "Blessed", "Sunrise", "City", "Family", "Grace", "Star", "Trust"]
suf = ["Mini Mart", "Provisions", "Supermarket", "Store", "Wholesale", "Kiosk", "Enterprise", "Depot"]
cust = []
for k in range(300):
    reg = rng.choice(REGIONS, p=REGION_W); ch = rng.choice(CHANNELS, p=CH_W)
    cust.append((f"C{k+1:03d}", f"{random.choice(pre)} {random.choice(suf)} {k+1}", reg, ch))
cust = pd.DataFrame(cust, columns=["customer_id", "outlet_name", "region", "channel"])
# balanced channel mix inside every region (keeps regional comparisons fair)
MIX = ["Supermarket"]*3 + ["Retail Shop"]*8 + ["Kiosk"]*7 + ["Wholesale"]*2
for r_ in REGIONS:
    ix = cust.index[cust.region == r_]
    cust.loc[ix, "channel"] = [MIX[n_ % 20] for n_ in range(len(ix))]
cust["rep_id"] = None
for r in REGIONS:
    idx = cust.index[cust.region == r]; ids = reps[reps.region == r].rep_id.tolist()
    cust.loc[idx, "rep_id"] = [ids[n % 3] for n in range(len(idx))]
cust = cust.merge(reps[["rep_id", "factor"]], on="rep_id")

rows = []
for gi, m in enumerate(MONTHS):
    growth = 1 + 0.01 * gi; season = SEASON[m.month]
    for c in cust.itertuples():
        lam = 4.0 * CH_FACTOR[c.channel] * c.factor * season * growth
        for _ in range(rng.poisson(lam)):
            sku = rng.choice(prod.sku, p=SKU_W)
            mu, sd = CH_QTY[c.channel]; qty = max(1, int(round(rng.normal(mu, sd))))
            price = round(PRICE[sku] * (1 + 0.006 * gi), 2)
            disc = int(rng.choice([0, 0, 0, 5, 10]))
            day = int(rng.integers(1, m.days_in_month + 1))
            shock = (c.region == "Ashanti" and CAT[sku] == "Beverages" and m >= SHOCK_START and rng.random() < 0.32)
            rows.append((m.to_timestamp() + pd.Timedelta(days=day-1), c.customer_id, c.region, c.channel, sku, qty, price, disc, c.rep_id, shock))
tx = pd.DataFrame(rows, columns=["order_date", "customer_id", "region", "channel", "sku", "quantity", "unit_price", "discount_pct", "sales_rep_id", "lost_to_stockout"])
tx["rev"] = tx.quantity * tx.unit_price * (1 - tx.discount_pct / 100)
tx["ym"] = tx.order_date.dt.to_period("M")

full = tx.groupby(["sales_rep_id", "ym"]).rev.sum().unstack(fill_value=0)   # shock-free revenue per rep-month
fac = reps.set_index("rep_id").factor
tg_rows = []
for rid in reps.rep_id:
    for m in MONTHS:   # target = "normal" performance for a rep of average strength, +/-10% noise
        tg_rows.append((rid, m, round(float(full.loc[rid, m]) / fac[rid] * rng.uniform(0.9, 1.1), -1)))
targets = pd.DataFrame(tg_rows, columns=["rep_id", "month", "target_amount"])

live = tx[~tx.lost_to_stockout].copy()

d_rows = []; did = 0
sku_units = tx.groupby(["region", "sku", "ym"]).quantity.sum()
for m in MONTHS:
    for r in REGIONS:
        for sku in prod.sku:
            did += 1
            units = int(sku_units.get((r, sku, m), 0) * 1.05) or 10
            bad = (r == "Ashanti" and CAT[sku] == "Beverages" and m >= SHOCK_START)
            order_dt = m.to_timestamp() + pd.Timedelta(days=int(rng.integers(0, 9)))
            lead = int(np.clip(rng.normal(11, 2.5), 6, 18)) if bad else int(np.clip(rng.normal(3, 1), 1, 6))
            fill = rng.uniform(0.55, 0.80) if bad else rng.uniform(0.95, 1.0)
            so = int(rng.integers(6, 15)) if bad else int(rng.poisson(0.7))
            d_rows.append((f"D{did:05d}", sku, r, order_dt, order_dt + pd.Timedelta(days=lead), units, int(units * fill), so))
dl = pd.DataFrame(d_rows, columns=["delivery_id", "sku", "region", "order_date", "delivery_date", "qty_ordered", "qty_delivered", "stockout_days"])

# ================= make it dirty =================
def dfmt(s):
    out = []
    for d in s:
        f = rng.choice(4, p=[.55, .25, .10, .10])
        out.append([d.strftime("%Y-%m-%d"), d.strftime("%d/%m/%Y"), d.strftime("%b %d, %Y"), d.strftime("%d-%b-%y")][f])
    return out
RV = {"Greater Accra": ["greater accra", "GREATER ACCRA", "Gt. Accra", "Accra"], "Ashanti": ["ASHANTI", "ashanti region", "Ashanti "],
      "Western": ["western", "Western Region"], "Eastern": ["EASTERN", "Eastern Region"], "Northern": ["northern", "Northern Region "], "Volta": ["volta", "Volta Region"]}
CV = {"Supermarket": ["supermarket", "Super Market"], "Retail Shop": ["retail", "Retail shop", "RETAIL"], "Kiosk": ["kiosk", "KIOSK"], "Wholesale": ["wholesale", "Whole sale"]}
def vary(series, table, p=0.25):
    return [random.choice(table[v]) if (random.random() < p) else v for v in series]

s = live.drop(columns=["lost_to_stockout", "rev", "ym"]).reset_index(drop=True)
n = len(s)
s.insert(0, "order_id", [f"SO-{i+1:06d}" for i in range(n)])
s["order_date"] = dfmt(s.order_date)
s.loc[rng.choice(n, 12, replace=False), "order_date"] = "N/A"
s["region"] = vary(s.region, RV); s["channel"] = vary(s.channel, CV)
s["sku"] = [random.choice([x.lower(), x + " "]) if random.random() < .10 else x for x in s.sku]
s["customer_id"] = [f" {x.lower()} " if random.random() < .05 else x for x in s.customer_id]
s["quantity"] = s.quantity.astype(object)
i = rng.choice(n, int(.04 * n), replace=False); s.loc[i, "quantity"] = np.nan
i = rng.choice(n, int(.02 * n), replace=False); s.loc[i, "quantity"] = [f"{q} ctn" if pd.notna(q) else q for q in s.loc[i, "quantity"]]
i = rng.choice(n, int(.01 * n), replace=False); s.loc[i, "quantity"] = [-q if isinstance(q, (int, np.integer)) else q for q in s.loc[i, "quantity"]]
i = rng.choice(n, 12, replace=False); s.loc[i, "quantity"] = [q * 100 if isinstance(q, (int, np.integer)) and q > 0 else q for q in s.loc[i, "quantity"]]
s["unit_price"] = s.unit_price.astype(object)
i = rng.choice(n, int(.06 * n), replace=False); s.loc[i, "unit_price"] = [f"GHS {p:.2f}" for p in s.loc[i, "unit_price"]]
i = rng.choice(n, int(.03 * n), replace=False); s.loc[i, "unit_price"] = np.nan
s["discount_pct"] = s.discount_pct.astype(object)
i = rng.choice(n, int(.10 * n), replace=False); s.loc[i, "discount_pct"] = [f"{d}%" for d in s.loc[i, "discount_pct"]]
i = rng.choice(n, int(.03 * n), replace=False); s.loc[i, "discount_pct"] = np.nan
s.loc[rng.choice(n, int(.02 * n), replace=False), "sales_rep_id"] = np.nan
dups = s.sample(int(.02 * n), random_state=1)
s = pd.concat([s, dups]).sample(frac=1, random_state=3).reset_index(drop=True)
s = s.rename(columns={"region": "outlet_region"})
s.to_csv(RAW / "sales_transactions_raw.csv", index=False)

p = prod.copy()
p["sku"] = [x.lower() if k in (2, 7) else (x + " " if k == 5 else x) for k, x in enumerate(p.sku)]
p["category"] = [c.lower() if k % 4 == 1 else (c.upper() if k % 5 == 2 else c) for k, c in enumerate(p.category)]
p["list_price"] = [f"GHS {x:.2f}" if k in (0, 4, 9) else x for k, x in enumerate(p.list_price)]
p.to_csv(RAW / "products_raw.csv", index=False)

c = cust[["customer_id", "outlet_name", "region", "channel", "rep_id"]].copy()
c["outlet_name"] = [x.upper() if k % 9 == 0 else f"  {x}  " if k % 11 == 0 else x for k, x in enumerate(c.outlet_name)]
c["region"] = vary(c.region, RV, .3); c["channel"] = vary(c.channel, CV, .3)
c.to_csv(RAW / "customers_raw.csv", index=False)

r = reps[["rep_id", "rep_name", "region", "hire_date"]].copy()
r["rep_name"] = [x.upper() if k % 4 == 0 else f" {x.lower()}" if k % 5 == 0 else x for k, x in enumerate(r.rep_name)]
r["region"] = vary(r.region, RV, .3); r["hire_date"] = dfmt(r.hire_date)
r.to_csv(RAW / "sales_reps_raw.csv", index=False)

t = targets.copy()
t["month"] = [m.strftime("%b-%Y") if random.random() < .8 else m.strftime("%Y-%m") for m in t.month]
t["target_amount"] = [f"{x:,.0f}" for x in t.target_amount]
t.loc[rng.choice(len(t), 6, replace=False), "target_amount"] = ""
t.to_csv(RAW / "sales_targets_raw.csv", index=False)

d = dl.copy(); nd = len(d)
d["region"] = vary(d.region, RV, .2)
d["order_date"] = dfmt(pd.to_datetime(dl.order_date)); d["delivery_date"] = dfmt(pd.to_datetime(dl.delivery_date))
d["qty_delivered"] = d.qty_delivered.astype(object); d["stockout_days"] = d.stockout_days.astype(object)
d.loc[rng.choice(nd, 25, replace=False), "qty_delivered"] = "N/A"
d.loc[rng.choice(nd, 25, replace=False), "stockout_days"] = "N/A"
d = pd.concat([d, d.sample(8, random_state=2)]).sample(frac=1, random_state=4)
d.to_csv(RAW / "deliveries_raw.csv", index=False)

print({f.name: len(pd.read_csv(f)) for f in sorted(RAW.glob("*.csv"))})
