import pandas as pd
from pathlib import Path

KEYWORDS = ["date", "customer", "client", "service", "provider", "employee",
            "item", "qty", "quantity", "amount", "price", "payment", "type",
            "status", "total", "tip", "tax", "transaction", "invoice", "checkout"]

f = next(Path("data/raw").glob("TransactionList*.xlsx"))
raw = pd.read_excel(f, header=None, nrows=40)

best = None
for i in range(len(raw)):
    cells = [str(x).strip().lower() for x in raw.iloc[i].tolist() if str(x) != "nan"]
    hits = sum(any(k in c for k in KEYWORDS) for c in cells)
    if hits >= 3:
        best = i
        print(f"header candidate at row {i} ({hits} keyword hits):")
        for c in raw.iloc[i].tolist():
            if str(c) != "nan":
                print(f"  {c}")
        break

if best is None:
    print("still nothing; row-by-row cell counts:")
    for i in range(len(raw)):
        n = raw.iloc[i].notna().sum()
        print(f"  row {i}: {n} non-empty cells")
else:
    df = pd.read_excel(f, header=best)
    print(f"\nrows: {len(df)}")
    for c in df.columns:
        print(f"  {c} | {df[c].dtype} | {df[c].notna().mean():.0%} filled")