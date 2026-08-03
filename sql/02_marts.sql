-- Per-client visit history with gaps between consecutive visits
CREATE OR REPLACE VIEW stg_visit_gaps AS
SELECT
    client_id,
    visit_date,
    lag(visit_date) OVER w                              AS prev_visit,
    date_diff('day', lag(visit_date) OVER w, visit_date) AS gap_days
FROM fct_visits
WINDOW w AS (PARTITION BY client_id ORDER BY visit_date);

-- One row per client: their rhythm and current status
CREATE OR REPLACE TABLE mart_client_retention AS
SELECT
    v.client_id,
    count(*)                                    AS n_visits,
    min(v.visit_date)                           AS first_visit,
    max(v.visit_date)                           AS last_visit,
    date_diff('day', max(v.visit_date), current_date) AS days_since_last,
    median(g.gap_days)                          AS typical_gap_days,
    sum(v.service_revenue)                      AS lifetime_revenue,
    arg_max(v.stylist_id, v.visit_date)         AS last_stylist
FROM fct_visits v
LEFT JOIN stg_visit_gaps g USING (client_id, visit_date)
GROUP BY 1;

-- The weekly outreach list: regulars gone quiet
CREATE OR REPLACE TABLE mart_outreach AS
SELECT
    client_id,
    last_stylist,
    n_visits,
    last_visit,
    days_since_last,
    typical_gap_days,
    round(days_since_last / typical_gap_days, 1) AS gap_ratio,
    round(lifetime_revenue, 0)                   AS lifetime_revenue
FROM mart_client_retention
WHERE n_visits >= 3                        -- enough history to know their rhythm
  AND typical_gap_days BETWEEN 7 AND 120   -- regulars, not annual drop-ins
  AND days_since_last > 1.5 * typical_gap_days   -- overdue
  AND days_since_last < 365                -- not long-gone (different conversation)
ORDER BY lifetime_revenue DESC;