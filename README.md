# Salon Escada Client Analytics: Technical Proposal

**Author:** Charles Asiedu
**Client:** Salon Escada (multi-stylist hair salon, Seattle, WA)
**Status:** Proposal · July 2026

---

## 1. Objective

Deliver a decision-support analytics layer on top of the salon's existing Vagaro booking system. The engagement replaces intuition with evidence across four business areas (client retention, schedule utilization, revenue efficiency, and staffing) and produces recommendations whose outcomes are measured.

This is an analytics engagement, not a software product: Vagaro remains the system of record; this project consumes its exports.

## 2. Data Sources

| Source | Contents | Grain |
|---|---|---|
| Vagaro appointments exports (Excel) | Date/time, service(s), stylist, status (completed / cancelled / no-show), duration | One row per appointment-service |
| Vagaro customer exports (Excel) | Client ID, first-visit date, contact fields (dropped at ingest) | One row per client |
| Vagaro sales exports (Excel) | Ticket totals, service vs. add-on line items, payment date | One row per line item |

Target history: 24+ months to support cohort and seasonality analysis. Actual columns will be confirmed against real exports at kickoff; Vagaro's export schemas vary by report; the ten obtained reports also include retention, rebooking, new vs. returning, services, and cancellation summaries used for validation.

## 3. Architecture

```
Vagaro Excel exports (.xlsx)
      │  (manual export by owner, ~monthly refresh)
      ▼
Ingest & anonymization (Python)
  - PII stripped/pseudonymized at load: names → client_id,
    stylists → stylist_id; contact info never persisted
      ▼
DuckDB database
  - raw schema      (as-loaded, typed)
  - staging schema  (cleaned, deduplicated, conformed)
  - marts schema    (analysis-ready: fct_appointments,
                     dim_clients, dim_stylists, fct_revenue)
      ▼
SQL transformations + data quality checks
  - null/duplicate checks, valid status values,
    referential integrity, row-count deltas per load
      ▼
Owner dashboard (Looker Studio)         Written deliverables
  - marts pushed to Google Sheets         - findings memo
  - private share to owner's account      - recommendations
  - phone-friendly, zero-license          - outcome tracking

Public companion (Tableau Public)
  - fully synthetic data mirroring the marts schema
  - rebuilds 2-3 key views for portfolio evidence
```

**Stack:** Python (pandas), DuckDB, SQL, Looker Studio (owner dashboard), Tableau Public (synthetic-data companion for the public portfolio).

**Why DuckDB:** columnar, zero-config, clean ingestion of tabular files, and keeps all analytical logic in SQL, which is the skill this project is meant to demonstrate.

## 4. Analytical Scope

### 4.1 Retention & churn (priority 1)
- **Cohort retention curves:** % of each first-visit-month cohort returning within 30/60/90 days; trended across cohorts.
- **Personal rebooking cycles:** per-client median inter-visit gap; churn-risk flag at >1.5× personal cycle (superior to a flat inactivity cutoff).
- **Weekly outreach list:** flagged clients ranked by historical value.
- **Revenue attrition:** trailing-12-month revenue of churned vs. active clients.

### 4.2 Revenue decomposition
- Revenue per service-hour by service type (price ÷ booked duration).
- Growth decomposition: volume vs. price vs. service-mix contribution by period.
- Revenue concentration: share held by top 10/20 clients; Pareto curve.
- Add-on attachment rate over time.
- Client lifetime value by acquisition cohort.

### 4.3 Utilization & demand
- Utilization heatmap: booked ÷ available hours by weekday × hour × stylist.
- Seasonality profile: monthly volume decomposition across available history.
- Booking lead-time distribution; share of same-week bookings.
- Simple demand forecast (seasonal-naive or Holt-Winters) projecting 4-6 weeks of expected bookings.

### 4.4 Stylist analytics (owner-only view)
- Per-stylist new-client retention rate.
- Rebook-at-checkout rate (next appointment created same day as visit).
- Request rate: % of appointments where the stylist was specifically requested.
- Revenue per booked hour and service mix by stylist.
- Redirection analysis: when a requested stylist is unavailable, does the client book another stylist or lapse?

### 4.5 Cancellations & no-shows
- No-show/cancellation rates by weekday, time slot, lead time, and client tenure (first-time vs. established).
- Estimated revenue lost to no-shows; policy simulation (e.g., deposit on first-time weekend bookings).

## 5. Deliverables

1. **Reproducible pipeline**: ingest, anonymize, transform (SQL), validate; runnable end-to-end on a fresh export.
2. **Owner dashboard (Looker Studio)**: retention, utilization, revenue, and stylist views; weekly outreach list front and center; shared privately to the owner's Google account.
3. **Findings memo**: 3 to 5 evidence-backed findings in plain language, each paired with a recommended action.
4. **Outcome log**: which recommendations the owner acted on and measurable results (e.g., appointments recovered from outreach), collected 4-8 weeks post-delivery.
5. **Public repo**: code, schema, README with architecture diagram and methodology; synthetic sample data only.

## 6. Privacy & Data Handling

- PII (names, phones, emails) is dropped or pseudonymized at ingest and never stored in the analytical database.
- Raw exports live outside the repo tree; `.gitignore` excludes all data paths from the first commit (no data ever enters Git history).
- Public artifacts (repo, screenshots, portfolio) use synthetic or anonymized data exclusively; stylists appear as Stylist A/B/C.
- Per-stylist performance metrics are restricted to an owner-only dashboard view and are never published.
- Owner may request full data deletion at any time; salon is named publicly only with written permission.

## 7. Milestones

| Week | Milestone |
|---|---|
| 0 | Requirements session with owner; confirm export availability |
| 1 | Ingest + anonymization + raw/staging schemas on first real export |
| 2 | Marts, data-quality checks, retention & utilization analyses |
| 3 | Dashboard v1; revenue and stylist analyses |
| 4 | Findings memo; walkthrough with owner; recommendations agreed |
| 5-12 | Light-touch: refreshed outreach lists, outcome tracking, README polish |

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Vagaro exports lack fields (e.g., requested-vs-assigned stylist) | Confirm schema in week 0; scope 4.4 items to available fields |
| Short or gappy history limits cohort analysis | Degrade gracefully to shorter windows; state limitations in memo |
| Scope creep | Retention + utilization ship first; all else is stretch |
| Owner disengagement post-delivery | Outreach list designed as a weekly habit with near-zero effort; outcome check-in scheduled at delivery |

## 9. Known Limitations

These constraints are documented up front and will be restated in the findings memo where they affect conclusions.

- **Aggregated exports.** Several Vagaro reports (retention, rebooking, new vs. returning) are pre-summarized rather than row-level. Where Vagaro's aggregation rules are opaque, this project's own metrics are computed from the transaction-level data and the Vagaro summaries are used as cross-checks, not sources of truth.
- **History window.** Data covers January 2022 to present, roughly 4.5 years. This supports seasonality analysis across three-plus full annual cycles, but longer-run trends (multi-year client lifecycles) are right-censored: recent cohorts have had less time to return, and retention for them is reported only for windows that have fully elapsed.
- **No true availability data.** Utilization is measured against booked hours and stated schedules, not a system record of open chair time. Dead-zone estimates are therefore approximate, and any schedule recommendations are directional.
- **Churn is inferred, not observed.** A client who stops booking may have moved, switched salons, or changed habits; the data cannot distinguish these. Churn flags identify clients worth contacting, not confirmed losses.
- **Requested-vs-assigned stylist may be incomplete.** If the exports do not reliably capture whether a stylist was specifically requested, the request-rate and redirection analyses will be scoped down or omitted, and this will be stated in the memo.
- **Attribution of outcomes is soft.** If outreach is followed by recovered bookings, causation is plausible but not proven; no control group exists in a single-salon engagement. Outcome claims will be phrased accordingly.
- **Single business.** Findings describe Salon Escada and should not be generalized to other salons.

## 10. Success Criteria

- Owner uses at least one output (outreach list or scheduling change) within 4 weeks of delivery.
- At least one recommendation produces a measurable outcome (recovered bookings, filled slots, or policy change).
- Pipeline re-runs cleanly on a fresh monthly export without code changes.
