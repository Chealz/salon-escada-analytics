import duckdb
from pathlib import Path

con = duckdb.connect("data/processed/salon.duckdb")
for sql_file in sorted(Path("sql").glob("*.sql")):
    print(f"running {sql_file.name}")
    statements = [s.strip() for s in sql_file.read_text().split(";") if s.strip()]
    for stmt in statements:
        con.execute(stmt)

print("\n--- summary ---")
print(con.execute("SELECT count(*) AS visits FROM fct_visits").df().to_string(index=False))
print(con.execute("""
    SELECT count(*) AS clients_with_3plus_visits,
           round(avg(typical_gap_days),1) AS avg_typical_gap
    FROM mart_client_retention WHERE n_visits >= 3
""").df().to_string(index=False))
print(f"\n--- outreach list: {con.execute('SELECT count(*) FROM mart_outreach').fetchone()[0]} clients overdue ---")
print(con.execute("""
    SELECT client_id, last_stylist, n_visits, last_visit,
           days_since_last, typical_gap_days, gap_ratio, lifetime_revenue
    FROM mart_outreach LIMIT 15
""").df().to_string(index=False))
con.close()