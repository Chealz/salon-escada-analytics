import duckdb
from pathlib import Path

con = duckdb.connect("data/processed/salon.duckdb")

for sql_file in sorted(Path("sql").glob("*.sql")):
    print(f"running {sql_file.name}")
    con.sql(sql_file.read_text())

print("\n--- validation ---")
checks = [
    ("transactions row count sane",
     "SELECT count(*) BETWEEN 6000 AND 20000 FROM raw.transactions"),
    ("no null dates in transactions",
     "SELECT count(*) = 0 FROM raw.transactions WHERE checkout_date IS NULL"),
    ("total revenue in expected band",
     "SELECT sum(amount_paid) BETWEEN 700000 AND 2000000 FROM raw.transactions"),
    ("no null client_id in visits",
     "SELECT count(*) = 0 FROM fct_visits WHERE client_id IS NULL"),
    ("visits fewer than transaction lines",
     "SELECT (SELECT count(*) FROM fct_visits) < (SELECT count(*) FROM raw.transactions)"),
    ("outreach list non-empty and plausible",
     "SELECT count(*) BETWEEN 1 AND 200 FROM mart_outreach"),
    ("every visit categorized",
     "SELECT count(*) = 0 FROM fct_visit_category WHERE primary_category IS NULL"),
]

failed = 0
for name, sql in checks:
    ok = con.execute(sql).fetchone()[0]
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    failed += (not ok)

con.close()
if failed:
    raise SystemExit(f"\n{failed} validation check(s) FAILED - do not use this build")
print("\nall checks passed")