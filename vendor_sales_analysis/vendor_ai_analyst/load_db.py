import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
CSV_FOLDER = Path(r"D:\Resume_Projects\data\database")
DB_PATH = r"D:\Resume_Projects\VendorMCP\data-deepdive-mcp\inventory.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

# ── Load each CSV into SQLite ─────────────────────────────────────────────────
csv_files = {
    "begin_inventory": "begin_inventory.csv",
    "end_inventory":   "end_inventory.csv",
    "purchase_prices": "purchase_prices.csv",
    "purchases":       "purchases.csv",
    "sales":           "sales.csv",
    "vendor_invoice":  "vendor_invoice.csv",
}

for table_name, filename in csv_files.items():
    filepath = CSV_FOLDER / filename
    if not filepath.exists():
        print(f"⚠️  Skipping {filename} — file not found")
        continue
    
    print(f"⏳ Loading {filename}...")
    chunks = pd.read_csv(filepath, chunksize=50000, low_memory=False)
    first = True
    for chunk in chunks:
        chunk.to_sql(table_name, engine, if_exists="replace" if first else "append", index=False)
        first = False
        print(f"   → {table_name}: chunk loaded")
    
    print(f"✅ {table_name} done!")

print("\n🎉 All tables loaded into inventory.db!")