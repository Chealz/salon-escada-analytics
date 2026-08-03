-- Service revenue lines only (products/refunds/fees handled separately)
CREATE OR REPLACE VIEW stg_service_lines AS
SELECT
    client_id,
    stylist_id,
    coalesce(appointment_date, checkout_date) AS visit_date,
    checkout_date,
    item,
    transaction_type,
    source,
    price,
    tip,
    discount,
    amount_paid
FROM raw.transactions
WHERE transaction_type IN ('Services', 'Service Add-on')
  AND client_id IS NOT NULL;

-- One row per client-visit: a client's service lines on the same date = one visit
CREATE OR REPLACE TABLE fct_visits AS
SELECT
    client_id,
    CAST(visit_date AS DATE)            AS visit_date,
    -- the stylist who did the most (by revenue) that day gets credit
    arg_max(stylist_id, price)          AS stylist_id,
    count(*)                            AS n_services,
    sum(price)                          AS service_revenue,
    sum(tip)                            AS tips,
    sum(amount_paid)                    AS total_paid,
    max(source)                         AS source
FROM stg_service_lines
GROUP BY 1, 2;