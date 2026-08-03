"""Profile raw Vagaro exports: structure only, never data values."""
import pandas as pd
from pathlib import Path

for f in sorted(Path("data/raw").glob("*.xlsx")):
    if f.name.startswith("~$"):
        continue
    print(f"\n=== {f.name} ===")
    for skip in range(0, 15):
        try:
            df = pd.read_excel(f, header=skip, nrows=5)
        except Exception as e:
            print(f"  read failed: {e}")
            break
        unnamed = sum(str(c).startswith("Unnamed") for c in df.columns)
        if unnamed <= len(df.columns) * 0.2:
            full = pd.read_excel(f, header=skip)
            print(f"header at skip={skip}, rows: {len(full)}")
            for c in full.columns:
                print(f"  {c} | {full[c].dtype} | {full[c].notna().mean():.0%} filled")
            break
    else:
        print("  no clean header in first 15 rows")