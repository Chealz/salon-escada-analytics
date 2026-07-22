import duckdb
con = duckdb.connect("data/processed/salon.duckdb")
print(con.execute("""
    SELECT transaction_type,
           count(*) AS line_items,
           round(sum(amount_paid), 2) AS paid,
           round(sum(price), 2) AS price_total,
           round(sum(tip), 2) AS tips
    FROM raw.transactions
    GROUP BY 1 ORDER BY paid DESC
""").df().to_string(index=False))
print(con.execute("""
    SELECT year(checkout_date) AS yr, round(sum(amount_paid), 2) AS paid
    FROM raw.transactions GROUP BY 1 ORDER BY 1
""").df().to_string(index=False))
con.close()