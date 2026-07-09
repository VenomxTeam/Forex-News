import json
import os
import re
import subprocess
from datetime import datetime, timezone
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
    if time_str in ["all day", "tentative"]:
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
            hour = int(parts[0])
            minute = int(parts[1])
        else:
            hour = int(time_str)
            minute = 0
            
        if is_pm and hour < 12:
            hour += 12
        if is_am and hour == 12:
            hour = 0
            
        # Load the ZoneInfo for the given timezone string
        try:
            tz = ZoneInfo(tz_str)
        except Exception:
            # Fallback to Asia/Kolkata or UTC
            tz = ZoneInfo("Asia/Kolkata")
            
        dt_local = datetime(year, month, day, hour, minute, tzinfo=tz)
        dt_utc = dt_local.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(f"Error parsing date-time ({date_str} {time_str}): {e}")
        return ""

def main():
    print("Processing existing scraped data from scraper/news/monthly...")
    
    # Scan the output monthly folder for generated monthly files
    output_dir = Path("news/last_run")
    if not output_dir.exists():
        print(f"Output directory {output_dir} does not exist.")
        return
        
    events = []
    
    # Read and merge all monthly JSON files
    for file_path in output_dir.glob("*.json"):
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
    for item in events:
        impact = item.get("impact", "").lower()
        if impact not in ["red", "orange", "yellow", "ora", "yel", "low", "gray", "grey", "none"]:
            continue
            
        currency = item.get("currency", "").upper()
        country, flag = CURRENCY_TO_COUNTRY.get(currency, ("Unknown Country", "un"))
        title = item.get("event", "").strip()
        
        # Generate time in UTC ISO format
        time_utc = parse_to_utc_iso(item.get("date"), item.get("time"), item.get("timezone", "Asia/Kolkata"))
        if not time_utc:
            # Fallback format: use day timestamp
            time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            
        date_slug = time_utc.split("T")[0].replace("-", "")
        event_id = f"{currency.lower()}_{slugify(title)}_{date_slug}"
        
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
        
    print(f"Filtered to {len(all_impact_events)} valid events.")
    
    # Prepare the news.json payload
    news_payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "events": all_impact_events
    }
    
    # Compare with existing news.json to implement the commit-reducing optimization
    target_file = Path("news.json")
    if target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                
            # Compare events list (ignoring updated_at)
            old_events = old_data.get("events", [])
            
            if json.dumps(old_events, sort_keys=True) == json.dumps(all_impact_events, sort_keys=True):
                print("No changes detected in events. Skipping news.json update to prevent unnecessary commits.")
                return
        except Exception as e:
            print(f"Error comparing old news.json: {e}")
            
    # Write updated news.json
    print("Changes detected. Writing updated news.json...")
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(news_payload, f, indent=2)
    print("news.json written successfully.")

if __name__ == "__main__":
    main()
