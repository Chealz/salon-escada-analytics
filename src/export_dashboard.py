"""Export mart tables for the Looker Studio dashboard (via Google Sheets).

All tabs are pseudonymous EXCEPT the outreach tab, which carries real
names because it is the owner's action list. The Sheet must be shared
with the owner's account only, never made link-public.
"""
import duckdb
import json
import pandas as pd
from pathlib import Path

OUT = Path("data/processed/dashboard")
OUT.mkdir(exist_ok=True)

con = duckdb.connect("data/processed/salon.duckdb")

exports = {
    "monthly_revenue": """
        SELECT date_trunc('month', visit_date) AS month,
               count(*) AS visits,
               round(sum(service_revenue), 0) AS service_revenue,
               round(sum(tips), 0) AS tips
        FROM fct_visits GROUP BY 1 ORDER BY 1
    """,
    "cohort_retention": """
        WITH first_visits AS (
            SELECT client_id, min(visit_date) AS first_visit FROM fct_visits GROUP BY 1
        ),
        returns AS (
            SELECT f.client_id, f.first_visit,
                   max(CASE WHEN v.visit_date > f.first_visit
                            AND v.visit_date <= f.first_visit + INTERVAL 90 DAY
                       THEN 1 ELSE 0 END) AS returned_90d
            FROM first_visits f JOIN fct_visits v USING (client_id) GROUP BY 1, 2
        )
        SELECT date_trunc('quarter', first_visit) AS cohort_quarter,
               count(*) AS new_clients,
               round(100.0 * sum(returned_90d) / count(*), 1) AS pct_returned_90d
        FROM returns
        WHERE first_visit <= current_date - INTERVAL 90 DAY
        GROUP BY 1 ORDER BY 1
    """,
    "service_cycles": "SELECT * FROM mart_service_cycles",
    "category_mix_monthly": """
        SELECT date_trunc('month', visit_date) AS month, primary_category,
               count(*) AS visits, round(sum(revenue), 0) AS revenue
        FROM fct_visit_category GROUP BY 1, 2 ORDER BY 1, 2
    """,
}

for name, sql in exports.items():
    df = con.execute(sql).df()
    df.to_csv(OUT / f"{name}.csv", index=False)
    print(f"{name}: {len(df)} rows")

# outreach tab: real names, owner's eyes only
outreach = con.execute("""
    SELECT client_id, last_stylist, n_visits, last_visit,
           days_since_last, typical_gap_days, round(lifetime_revenue, 0) AS lifetime_revenue
    FROM mart_outreach ORDER BY lifetime_revenue DESC
""").df()
con.close()

with open("data/processed/id_mapping.json") as f:
    m = json.load(f)
outreach.insert(0, "client", outreach.pop("client_id").map({v: k.title() for k, v in m["clients"].items()}))
outreach["stylist"] = outreach.pop("last_stylist").map({v: k.title() for k, v in m["stylists"].items()})
outreach.to_csv(OUT / "outreach.csv", index=False)
print(f"outreach: {len(outreach)} rows (CONTAINS REAL NAMES)")