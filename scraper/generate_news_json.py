import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Currency to Country Mapping
CURRENCY_TO_COUNTRY = {
    "USD": ("United States", "us"),
    "EUR": ("Eurozone", "eu"),
    "GBP": ("United Kingdom", "gb"),
    "JPY": ("Japan", "jp"),
    "AUD": ("Australia", "au"),
    "CAD": ("Canada", "ca"),
    "NZD": ("New Zealand", "nz"),
    "CHF": ("Switzerland", "ch"),
    "CNY": ("China", "cn")
}

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text).strip('_')
    return text

def parse_to_utc_iso(date_str, time_str, tz_str):
    # e.g. date_str: "29/06/2026", time_str: "18:00" or "8:30am"
    if not date_str or not time_str:
        return ""
    
    # Clean time string
    time_str = time_str.strip().lower()
    if time_str in ["all day", "tentative"] or not any(c.isdigit() for c in time_str):
        time_str = "00:00"
    
    # Handle AM/PM formats
    is_pm = "pm" in time_str
    is_am = "am" in time_str
    time_str = time_str.replace("am", "").replace("pm", "").strip()
    
    try:
        # Parse date components
        day, month, year = map(int, date_str.split("/"))
        
        # Parse time components
        if ":" in time_str:
            parts = time_str.split(":")
            hour = int(parts[0]) if parts[0].isdigit() else 0
            minute = int(parts[1]) if parts[1].isdigit() else 0
        elif time_str.isdigit():
            hour = int(time_str)
            minute = 0
        else:
            hour = 0
            minute = 0
            
        if is_pm and hour < 12:
            hour += 12
        if is_am and hour == 12:
            hour = 0
            
        # Load the ZoneInfo for the given timezone string
        try:
            tz = ZoneInfo(tz_str)
        except Exception:
            # Fallback to UTC
            tz = timezone.utc
            
        dt_local = datetime(year, month, day, hour, minute, tzinfo=tz)
        dt_utc = dt_local.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(f"Error parsing date-time ({date_str} {time_str}): {e}")
        return ""

def _merge_with_existing_news(target_file: Path, scraped_events: list[dict]) -> list[dict]:
    """Preserve non-scraped months (historical + 2027) and live actuals across incremental scrapes."""
    if not target_file.exists():
        return scraped_events

    try:
        with open(target_file, "r", encoding="utf-8-sig") as f:
            existing_payload = json.load(f)
        existing_events = existing_payload.get("events", [])
    except Exception as e:
        print(f"Warning: could not read existing {target_file.name} for merge: {e}")
        return scraped_events

    scraped_months = {
        e["time"][:7]
        for e in scraped_events
        if isinstance(e.get("time"), str) and len(e["time"]) >= 7
    }

    existing_by_id = {e.get("id"): e for e in existing_events if e.get("id")}
    existing_by_exact_time = {
        (e.get("currency", "").upper(), e.get("title", "").strip().lower(), e.get("time", "")[:16]): e
        for e in existing_events
        if e.get("time")
    }
    existing_by_day = {}
    ambiguous_day_keys = set()
    for e in existing_events:
        if not e.get("time"):
            continue
        day_key = (e.get("currency", "").upper(), e.get("title", "").strip().lower(), e.get("time", "")[:10])
        if day_key in existing_by_day:
            ambiguous_day_keys.add(day_key)
        else:
            existing_by_day[day_key] = e

    merged_events = []
    seen_ids = set()

    # Preserve all events from months not included in the latest scrape (e.g. history + 2027)
    for ev in existing_events:
        ev_month = ev.get("time", "")[:7]
        if ev_month not in scraped_months:
            ev_id = ev.get("id")
            if ev_id:
                seen_ids.add(ev_id)
            merged_events.append(ev)

    # Refresh scraped months while retaining already-synced live actuals/forecasts if FF scrape left them blank
    for ev in scraped_events:
        day_key = (ev.get("currency", "").upper(), ev.get("title", "").strip().lower(), ev.get("time", "")[:10])
        match = (
            existing_by_id.get(ev.get("id"))
            or existing_by_exact_time.get(
                (ev.get("currency", "").upper(), ev.get("title", "").strip().lower(), ev.get("time", "")[:16])
            )
            or (existing_by_day.get(day_key) if day_key not in ambiguous_day_keys else None)
        )
        if match:
            for field in ("actual", "forecast", "previous"):
                if not ev.get(field) and match.get(field):
                    ev[field] = match[field]

        candidate_id = ev.get("id") or "event"
        final_id = candidate_id
        idx = 1
        while final_id in seen_ids:
            final_id = f"{candidate_id}_{idx}"
            idx += 1
        ev["id"] = final_id
        seen_ids.add(final_id)
        merged_events.append(ev)

    return merged_events


def main():
    script_dir = Path(__file__).resolve().parent
    print(f"Processing scraped data from {script_dir / 'news' / 'monthly'}...")
    
    # Scan the output monthly folder for generated monthly files
    output_dir = script_dir / "news" / "monthly"
    if not output_dir.exists():
        print(f"Output directory {output_dir} does not exist.")
        return
        
    events = []
    
    # Read and merge all monthly JSON files
    for file_path in sorted(output_dir.glob("*.json")):
        print(f"Parsing monthly file: {file_path.name}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                month_events = json.load(f)
                events.extend(month_events)
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            
    print(f"Loaded {len(events)} raw events.")
    
    # Filter for high, medium, low impact and map fields
    all_impact_events = []
    seen_ids = set()
    for item in events:
        impact = item.get("impact", "").lower()
        if impact not in ["red", "orange", "yellow", "ora", "yel", "low", "gray", "grey", "none"]:
            continue
            
        currency = item.get("currency", "").upper()
        country, flag = CURRENCY_TO_COUNTRY.get(currency, ("Unknown Country", "un"))
        title = item.get("event", "").strip()
        
        # Generate time in UTC ISO format
        # Map common timezone abbreviations to IANA timezone names
        TZ_MAP = {
            "UTC": "UTC",
            "EST": "America/New_York",
            "EDT": "America/New_York",
            "BST": "Europe/London",
            "GMT": "GMT",
            "IST": "Asia/Kolkata"
        }
        tz_from_data = item.get("timezone", "UTC")
        # If the tz_from_data is already a valid IANA zone (like "Asia/Kolkata"), use it. Otherwise map it.
        if "/" in tz_from_data:
            tz_iana = tz_from_data
        else:
            tz_iana = TZ_MAP.get(tz_from_data, "UTC")
        time_utc = parse_to_utc_iso(item.get("date"), item.get("time"), tz_iana)
        
        # Handle special case: API Weekly is often shifted by a day improperly due to FF UTC bug
        if "API Weekly" in title and time_utc:
            # Shift back by 1 day
            dt = datetime.strptime(time_utc, "%Y-%m-%dT%H:%M:%SZ")
            dt = dt - timedelta(days=1)
            time_utc = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            # Update the date str to match the new day
            item["date"] = dt.strftime("%d/%m/%Y")
            item["day"] = dt.strftime("%a")
            
        if not time_utc and item.get("date"):
            try:
                d, m, y = map(int, item.get("date").split("/"))
                time_utc = f"{y:04d}-{m:02d}-{d:02d}T00:00:00Z"
            except Exception:
                pass

        if not time_utc:
            print(f"Skipping unparseable event date: {item.get('event')} on {item.get('date')}")
            continue
            
        date_slug = time_utc.split("T")[0].replace("-", "")
        base_id = f"{currency.lower()}_{slugify(title)}_{date_slug}"
        if base_id not in seen_ids:
            event_id = base_id
        else:
            time_slug = time_utc.split("T")[1].replace(":", "")[:4] if "T" in time_utc else ""
            candidate_id = f"{base_id}_{time_slug}" if time_slug and time_slug != "0000" else base_id
            idx = 1
            while candidate_id in seen_ids:
                candidate_id = f"{base_id}_{idx}"
                idx += 1
            event_id = candidate_id
        seen_ids.add(event_id)
        
        mapped_event = {
            "id": event_id,
            "currency": currency,
            "country": country,
            "flag": flag,
            "title": title,
            "impact": impact,
            "time": time_utc,
            "forecast": item.get("forecast", "").strip(),
            "previous": item.get("previous", "").strip(),
            "actual": item.get("actual", "").strip(),
            "description": "",
            "category": "Economic"
        }
        all_impact_events.append(mapped_event)
        
    target_file = script_dir / "news.json"
    if not all_impact_events and target_file.exists():
        print("No new scraped events parsed; keeping existing news.json intact.")
        return

    merged_events = _merge_with_existing_news(target_file, all_impact_events)
    merged_events.sort(key=lambda x: x.get("time", ""))
    print(f"Filtered to {len(all_impact_events)} newly scraped events ({len(merged_events)} total after merge).")

    # Prepare the news.json payload
    news_payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "events": merged_events
    }

    # Write updated news.json
    print(f"Writing updated news.json to {target_file}...")
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(news_payload, f, indent=2)
    print("news.json written successfully.")

    # Automatically enrich events with continuous data and live actual releases
    try:
        from enrich_events import enrich_news_dataset
        enrich_news_dataset(str(target_file), str(target_file))
    except Exception as e:
        print(f"Automatic enrichment hook note: {e}")

if __name__ == "__main__":
    main()
