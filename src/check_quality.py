"""One-time audit: name-collision risk in pseudonymization."""
import duckdb, json

con = duckdb.connect("data/processed/salon.duckdb")

print("=== top visit counts: are these plausible regulars? ===")
print(con.execute("""
    SELECT client_id, count(*) AS visits,
           min(visit_date) AS first, max(visit_date) AS last,
           round(count(*) / (date_diff('day', min(visit_date), max(visit_date)) / 365.25), 1) AS visits_per_year
    FROM fct_visits GROUP BY 1 ORDER BY visits DESC LIMIT 10
""").df().to_string(index=False))

with open("data/processed/id_mapping.json") as f:
    m = json.load(f)
print(f"\nmapped clients: {len(m['clients'])}")
print(f"customer file rows: ", con.execute("SELECT count(*) FROM raw.customers").fetchone()[0])
print("gap = clients present in one source but not the other (spelling variants, txn-only walk-ins)")

con.close()