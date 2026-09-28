"""Load the CLEAN csv files into a local SQLite database (wagcol_demo.db).
Run: python sql/00_load_to_sqlite.py   -> then open the .db in DB Browser for SQLite (or run the .sql files with sqlite3)
For MySQL / PostgreSQL / SQL Server: use the same CSVs with the import wizard (or LOAD DATA / COPY / BULK INSERT)."""
import sqlite3, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "wagcol_demo.db")
for f in sorted((ROOT / "data" / "clean").glob("*.csv")):
    if f.stem == "data_quality_log": continue
    pd.read_csv(f).to_sql(f.stem, con, if_exists="replace", index=False); print("loaded", f.stem)
con.execute("CREATE INDEX IF NOT EXISTS ix_sales_date ON fact_sales(order_date)")
con.commit(); con.close()
