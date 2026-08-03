"""Reportable findings for Salon Escada. Source of truth for the findings memo."""
import duckdb

con = duckdb.connect("data/processed/salon.duckdb")

print("=== 1. Revenue overview ===")
print(con.execute("""
    SELECT year(checkout_date) AS yr,
           round(sum(amount_paid) FILTER (WHERE transaction_type IN ('Services','Service Add-on')), 0) AS service_revenue,
           round(sum(amount_paid), 0) AS total_paid
    FROM raw.transactions GROUP BY 1 ORDER BY 1
""").df().to_string(index=False))

print("\n=== 2. First-visit conversion (90-day, censoring-corrected) ===")
print(con.execute("""
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
    SELECT year(first_visit) AS cohort_year, count(*) AS new_clients,
           round(100.0 * sum(returned_90d) / count(*), 1) AS pct_returned_90d
    FROM returns
    WHERE first_visit <= current_date - INTERVAL 90 DAY
    GROUP BY 1 ORDER BY 1
""").df().to_string(index=False))

print("\n=== 3. Return cycle by service category ===")
print(con.execute("""
    SELECT primary_category, visits, median_days_to_next, pct_returned_within_year
    FROM mart_service_cycles WHERE visits >= 40 ORDER BY visits DESC
""").df().to_string(index=False))

print("\n=== 4. Unconverted consultations ===")
print(con.execute("""
    SELECT count(*) AS one_visit_clients,
           count(*) FILTER (WHERE max_rev < 20) AS never_bought_service
    FROM (SELECT client_id, count(*) AS n, max(service_revenue) AS max_rev
          FROM fct_visits GROUP BY 1 HAVING count(*) = 1)
""").df().to_string(index=False))

print("\n=== 5. Overdue regulars (outreach list summary) ===")
print(con.execute("""
    SELECT count(*) AS clients_overdue,
           round(sum(lifetime_revenue), 0) AS lifetime_value_at_risk
    FROM mart_outreach
""").df().to_string(index=False))

con.close()