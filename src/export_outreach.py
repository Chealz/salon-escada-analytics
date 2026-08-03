"""Attach real names to the outreach list. LOCAL USE ONLY.

Output goes to data/processed/ which is gitignored. Never share or
commit the output file. This is the owner-facing deliverable.
"""
import duckdb
import json
import pandas as pd
from datetime import date

con = duckdb.connect("data/processed/salon.duckdb")
outreach = con.execute("""
    SELECT client_id, last_stylist, n_visits, last_visit,
           days_since_last, typical_gap_days, gap_ratio, lifetime_revenue
    FROM mart_outreach
    ORDER BY lifetime_revenue DESC
""").df()
con.close()

with open("data/processed/id_mapping.json") as f:
    mapping = json.load(f)

# invert: client_0001 -> name (stored lowercase; title-case for readability)
id_to_client = {v: k.title() for k, v in mapping["clients"].items()}
id_to_stylist = {v: k.title() for k, v in mapping["stylists"].items()}

outreach.insert(0, "client_name", outreach["client_id"].map(id_to_client))
outreach["stylist_name"] = outreach["last_stylist"].map(id_to_stylist)

out = outreach[["client_name", "stylist_name", "n_visits", "last_visit",
                "days_since_last", "typical_gap_days", "lifetime_revenue"]].rename(columns={
    "client_name": "Client",
    "stylist_name": "Their stylist",
    "n_visits": "Total visits",
    "last_visit": "Last visit",
    "days_since_last": "Days since",
    "typical_gap_days": "Usually comes every (days)",
    "lifetime_revenue": "Lifetime spend ($)",
})

path = f"data/processed/outreach_list_{date.today()}.xlsx"
out.to_excel(path, index=False)
print(f"wrote {len(out)} clients to {path}")
print("\nREMINDER: this file contains real names. Do not share, upload, or commit.")