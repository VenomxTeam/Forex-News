"""
generate_2027_events.py
Generates full 12-month economic calendar for 2027 based on 2026 macroeconomic
cycles and business day calendar mapping.
"""
import json
import csv
import calendar
from datetime import datetime, date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MONTHLY_DIR = BASE_DIR / "news" / "monthly"

NORMALIZED_FIELDS = [
    "time", "timezone", "currency", "impact", "event",
    "detail", "actual", "forecast", "previous", "day", "date", "scraped_at"
]

def is_fixed_date_holiday(day, month, title):
    t = title.lower()
    if "bank holiday" in t or "holiday" in t:
        if month == 1 and day in [1, 2]:
            return True
        if month == 12 and day in [24, 25, 26, 31]:
            return True
        if month == 7 and day == 4:
            return True
        if month == 1 and day == 26:
            return True
    return False

def map_date_to_2027(d_str, title):
    day, month, _ = map(int, d_str.split("/"))
    
    # Specific end-of-year handling for 31/12
    if month == 12 and day == 31:
        t = title.lower()
        if "unemployment claims" in t or "natural gas storage" in t:
            # Map weekly Thursday events to the 5th Thursday in Dec 2027 (Dec 30)
            return "30/12/2027", "Thu"
        else:
            # End of month / year-end releases (e.g. FOMC Meeting Minutes at 19:00 UTC,
            # CNY PMIs, AUD Private Sector Credit, Bank Holidays) stay on Dec 31 (Friday)
            return "31/12/2027", "Fri"

    if is_fixed_date_holiday(day, month, title):
        d27 = date(2027, month, day)
        if d27.weekday() == 5:
            d27 += timedelta(days=2) # Saturday -> Monday
        elif d27.weekday() == 6:
            d27 += timedelta(days=1) # Sunday -> Monday
        return d27.strftime("%d/%m/%Y"), d27.strftime("%a")

    dt26 = date(2026, month, day)
    wd = dt26.weekday()

    cal26 = calendar.monthcalendar(2026, month)
    occurrences26 = [w[wd] for w in cal26 if w[wd] != 0]
    nth = occurrences26.index(day) + 1
    is_last = (nth == len(occurrences26))

    cal27 = calendar.monthcalendar(2027, month)
    occurrences27 = [w[wd] for w in cal27 if w[wd] != 0]

    if is_last and len(occurrences27) < nth:
        new_day = occurrences27[-1]
    elif nth <= len(occurrences27):
        new_day = occurrences27[nth - 1]
    else:
        new_day = occurrences27[-1]

    d27 = date(2027, month, new_day)
    return d27.strftime("%d/%m/%Y"), d27.strftime("%a")

def generate_2027():
    print("Generating 2027 economic calendar events...")
    total_generated = 0
    
    for m in range(1, 13):
        m26_path = MONTHLY_DIR / f"2026-{m:02d}.json"
        if not m26_path.exists():
            print(f"Warning: {m26_path} missing!")
            continue
            
        with open(m26_path, "r", encoding="utf-8") as f:
            events_2026 = json.load(f)
            
        events_2027 = []
        month_name = datetime(2027, m, 1).strftime("%B")
        
        for e in events_2026:
            e27 = dict(e)
            d27, day27 = map_date_to_2027(e["date"], e["event"])
            e27["date"] = d27
            e27["day"] = day27
            e27["actual"] = "" # Future event
            e27["scraped_at"] = f"2027-{m:02d}-01T00:00:00.000000+00:00"
            e27["detail"] = f"https://www.forexfactory.com/calendar?month={month_name}#detail=2027{m:02d}"
            events_2027.append(e27)
            
        # Write monthly JSON
        json_out = MONTHLY_DIR / f"2027-{m:02d}.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(events_2027, f, indent=2)
            
        # Write monthly CSV
        csv_out = MONTHLY_DIR / f"2027-{m:02d}.csv"
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=NORMALIZED_FIELDS)
            writer.writeheader()
            writer.writerows([{k: row.get(k, "") for k in NORMALIZED_FIELDS} for row in events_2027])
            
        print(f"  Month 2027-{m:02d}: {len(events_2027)} events written.")
        total_generated += len(events_2027)
        
    print(f"Successfully generated {total_generated} events for 2027.")

if __name__ == "__main__":
    generate_2027()
