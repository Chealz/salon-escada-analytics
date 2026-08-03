# src/check_retention.py
import duckdb
con = duckdb.connect("data/processed/salon.duckdb")
print(con.execute("""
    SELECT n_visits, count(*) AS clients
    FROM (SELECT client_id, count(*) AS n_visits FROM fct_visits GROUP BY 1)
    GROUP BY 1 ORDER BY 1 LIMIT 12
""").df().to_string(index=False))
print(con.execute("""
    SELECT year(first_visit) AS cohort_year,
           count(*) AS new_clients,
           round(100.0 * count(*) FILTER (WHERE n_visits >= 2) / count(*), 1) AS pct_returned
    FROM mart_client_retention GROUP BY 1 ORDER BY 1
""").df().to_string(index=False))

# add to check_retention.py
print(con.execute("""
    WITH first_visits AS (
        SELECT client_id, min(visit_date) AS first_visit FROM fct_visits GROUP BY 1
    ),
    returns AS (
        SELECT f.client_id, f.first_visit,
               max(CASE WHEN v.visit_date > f.first_visit
                        AND v.visit_date <= f.first_visit + INTERVAL 90 DAY
                   THEN 1 ELSE 0 END) AS returned_90d
        FROM first_visits f JOIN fct_visits v USING (client_id)
        GROUP BY 1,2
    )
    SELECT year(first_visit) AS cohort_year,
           count(*) AS new_clients,
           round(100.0 * sum(returned_90d) / count(*), 1) AS pct_returned_90d
    FROM returns
    WHERE first_visit <= current_date - INTERVAL 90 DAY
    GROUP BY 1 ORDER BY 1
""").df().to_string(index=False))

print(con.execute("""
    SELECT item, count(*) AS n, round(avg(price),0) AS avg_price
    FROM raw.transactions
    WHERE transaction_type = 'Services'
    GROUP BY 1 ORDER BY n DESC LIMIT 30
""").df().to_string(index=False))

# 90-day cohort retention (censoring-corrected)
print(con.execute("""
    WITH first_visits AS (
        SELECT client_id, min(visit_date) AS first_visit FROM fct_visits GROUP BY 1
    ),
    returns AS (
        SELECT f.client_id, f.first_visit,
               max(CASE WHEN v.visit_date > f.first_visit
                        AND v.visit_date <= f.first_visit + INTERVAL 90 DAY
                   THEN 1 ELSE 0 END) AS returned_90d
        FROM first_visits f JOIN fct_visits v USING (client_id)
        GROUP BY 1,2
    )
    SELECT year(first_visit) AS cohort_year,
           count(*) AS new_clients,
           round(100.0 * sum(returned_90d) / count(*), 1) AS pct_returned_90d
    FROM returns
    WHERE first_visit <= current_date - INTERVAL 90 DAY
    GROUP BY 1 ORDER BY 1
""").df().to_string(index=False))

# service mix, for v2
print(con.execute("""
    SELECT item, count(*) AS n, round(avg(price),0) AS avg_price
    FROM raw.transactions
    WHERE transaction_type = 'Services'
    GROUP BY 1 ORDER BY n DESC LIMIT 30
""").df().to_string(index=False))

print(con.execute("""
    SELECT count(*) FILTER (WHERE only_visit_was_cheap) AS one_visit_cheap,
           count(*) AS one_visit_total
    FROM (
        SELECT client_id, max(service_revenue) < 20 AS only_visit_was_cheap
        FROM fct_visits GROUP BY 1 HAVING count(*) = 1
    )
""").df().to_string(index=False))

print(con.execute("SELECT * FROM mart_service_cycles").df().to_string(index=False))
print(con.execute("""
    SELECT category, item, count(*) AS n
    FROM stg_service_category GROUP BY 1,2 ORDER BY category, n DESC
""").df().to_string(index=False))
con.close()