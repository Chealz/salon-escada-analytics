"""Ingest Vagaro exports: strip PII, pseudonymize, load to DuckDB."""
import pandas as pd
import duckdb
import json
import re
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(exist_ok=True)

# ---------- helpers ----------

def find_header(path, keywords, max_rows=40):
    raw = pd.read_excel(path, header=None, nrows=max_rows)
    for i in range(len(raw)):
        cells = [str(x).strip().lower() for x in raw.iloc[i] if str(x) != "nan"]
        if sum(any(k in c for k in keywords) for c in cells) >= 3:
            return i
    raise ValueError(f"no header row found in {path.name}")

def money(series):
    """'$1,234.56' or '($12.00)' -> float"""
    s = series.astype(str).str.replace(r"[$,]", "", regex=True).str.strip()
    s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    return pd.to_numeric(s, errors="coerce")

def norm_name(x):
    return re.sub(r"\s+", " ", str(x).strip().lower())

class Pseudonymizer:
    def __init__(self, prefix):
        self.prefix = prefix
        self.map = {}
    def get(self, name):
        key = norm_name(name)
        if key in ("nan", "", "none"):
            return None
        if key not in self.map:
            self.map[key] = f"{self.prefix}_{len(self.map)+1:04d}"
        return self.map[key]
    def apply(self, series):
        return series.map(self.get)

clients = Pseudonymizer("client")
stylists = Pseudonymizer("stylist")

# ---------- transactions ----------

f = next(RAW.glob("TransactionList*.xlsx"))
hdr = find_header(f, ["checkout", "transaction", "customer", "service", "qty"])
tx = pd.read_excel(f, header=hdr)

tx = tx.rename(columns={
    "Checkout Date": "checkout_date",
    "Transaction ID": "transaction_id",
    "Appointment Date": "appointment_date",
    "Customer": "customer",
    "Service/Product/GC/Package/Membership/Class": "item",
    "Transaction Type": "transaction_type",
    "Sold By": "stylist",
    "Source": "source",
    "Qty": "qty",
    "Price": "price",
    "Tax": "tax",
    "Tip": "tip",
    "Disc": "discount",
    "Amt Paid": "amount_paid",
})
tx = tx[["checkout_date", "transaction_id", "appointment_date", "customer",
         "item", "transaction_type", "stylist", "source", "qty",
         "price", "tax", "tip", "discount", "amount_paid"]]

tx["client_id"] = clients.apply(tx["customer"])
tx["stylist_id"] = stylists.apply(tx["stylist"])
tx = tx.drop(columns=["customer", "stylist"])
for col in ["price", "tax", "tip", "discount", "amount_paid"]:
    tx[col] = money(tx[col])
for col in ["checkout_date", "appointment_date"]:
    tx[col] = pd.to_datetime(tx[col], errors="coerce")

    tx = tx[tx["checkout_date"].notna()]

# ---------- customers ----------

f = next(RAW.glob("Customers_*.xlsx"))
cu = pd.read_excel(f, header=5)
cu["client_id"] = clients.apply(cu["Name"])
cu = cu.rename(columns={
    "Customer Since": "customer_since",
    "Last Visit": "last_visit",
    "Gender": "gender",
    "Online Booking": "online_booking",
    "App. Booked": "appts_booked",
    "Check-Ins": "check_ins",
    "Amount Paid": "lifetime_paid",
    "No Shows/Cancel": "no_shows_cancels",
})
# PII and payment fields dropped UNREAD; free-text/derivable fields dropped too
cu = cu[["client_id", "customer_since", "last_visit", "gender",
         "online_booking", "appts_booked", "check_ins",
         "lifetime_paid", "no_shows_cancels"]]
cu["lifetime_paid"] = money(cu["lifetime_paid"])
for col in ["customer_since", "last_visit"]:
    cu[col] = pd.to_datetime(cu[col], errors="coerce")

# ---------- cancellations & no-shows ----------

f = next(RAW.glob("Cancellation*.xlsx"))
cx = pd.read_excel(f, header=5)
cx["client_id"] = clients.apply(cx["Customer"])
cx["stylist_id"] = stylists.apply(cx["Service Provider"])
cx = cx.rename(columns={
    "Appointment Date": "appointment_date",
    "Status": "status",
    "Status Changed Date": "status_changed_date",
    "Service Name": "service_name",
})
# Comments dropped: free text can contain personal details
cx = cx[["client_id", "stylist_id", "appointment_date", "status",
         "status_changed_date", "service_name"]]
for col in ["appointment_date", "status_changed_date"]:
    cx[col] = pd.to_datetime(cx[col], errors="coerce")

# ---------- services summary (no PII) ----------

f = next(RAW.glob("Services_Classes*.xlsx"))
sv = pd.read_excel(f, header=5)
sv = sv.rename(columns={
    "Services/Classes": "service_name",
    "No of Appointments/Classes": "n_appointments",
    "No of Attendees": "n_attendees",
    "Service Sale": "service_sales",
    "Service Add-on Sale": "addon_sales",
    "Cost To Business": "cost_to_business",
    "Average Sale": "avg_sale",
})
sv = sv[["service_name", "n_appointments", "n_attendees",
         "service_sales", "addon_sales", "cost_to_business", "avg_sale"]]
for col in ["service_sales", "addon_sales", "cost_to_business", "avg_sale"]:
    sv[col] = money(sv[col])

# ---------- load to DuckDB ----------

con = duckdb.connect(str(OUT / "salon.duckdb"))
con.execute("CREATE SCHEMA IF NOT EXISTS raw")
for name, df in [("transactions", tx), ("customers", cu),
                 ("cancellations", cx), ("services", sv)]:
    con.execute(f"CREATE OR REPLACE TABLE raw.{name} AS SELECT * FROM df")
    print(f"raw.{name}: {len(df)} rows, {len(df.columns)} cols")
con.close()

# mapping stays local (gitignored via id_mapping*)
with open(OUT / "id_mapping.json", "w") as m:
    json.dump({"clients": clients.map, "stylists": stylists.map}, m, indent=2)
print(f"\nclients mapped: {len(clients.map)}, stylists mapped: {len(stylists.map)}")
print("done")