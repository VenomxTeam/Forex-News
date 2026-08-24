import json
import glob
from datetime import datetime, timedelta
from pathlib import Path

def convert_monthly_files():
    monthly_files = sorted(glob.glob('scraper/news/monthly/*.json'))
    
    for path in monthly_files:
        # Check if 2026-07.json (already UTC)
        if '2026-07.json' in path:
            print(f"Skipping {path} (already in UTC)")
            continue
            
        print(f"Converting {path} from Asia/Kolkata (IST) to UTC...")
        with open(path, 'r', encoding='utf-8') as f:
            events = json.load(f)
            
        converted_count = 0
        for e in events:
            time_str = e.get('time', '').strip()
            date_str = e.get('date', '').strip()
            
            if not time_str or time_str.lower() in ['all day', 'tentative', '']:
                continue
                
            try:
                dt_ist = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                dt_utc = dt_ist - timedelta(hours=5, minutes=30)
                
                e['date'] = dt_utc.strftime("%d/%m/%Y")
                e['time'] = dt_utc.strftime("%H:%M")
                e['day'] = dt_utc.strftime("%a")
                e['timezone'] = 'UTC'
                converted_count += 1
            except Exception as ex:
                print(f"Error converting event in {path}: {e.get('event')} {date_str} {time_str}: {ex}")
                
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2)
            
        print(f"Successfully converted {converted_count} events in {path} to UTC.")

if __name__ == "__main__":
    convert_monthly_files()
