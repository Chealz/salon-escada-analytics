import duckdb
con = duckdb.connect("data/processed/salon.duckdb")
print(con.execute("""
    SELECT
      count(*) AS rows,
      min(checkout_date) AS first_tx,
      max(checkout_date) AS last_tx,
      count(*) FILTER (WHERE checkout_date IS NULL) AS null_dates,
      round(sum(amount_paid), 2) AS total_paid
    FROM raw.transactions
""").df().to_string(index=False))
print(con.execute("""
    SELECT stylist_id, count(*) AS line_items
    FROM raw.transactions GROUP BY 1 ORDER BY 2 DESC
""").df().to_string(index=False))
con.close()