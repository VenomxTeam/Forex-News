import json
from datetime import datetime, timezone

with open('scraper/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

events = data['events']

# Find Aug 12 events specifically
aug12 = [e for e in events if '2026-08-12' in e.get('time','')]
print(f"August 12, 2026 events: {len(aug12)}")
for e in aug12:
    print(f"  [{e.get('impact','').upper()[:3]}] {e['currency']} - {e['title']}")
    print(f"       Prev='{e.get('previous','')}' Forecast='{e.get('forecast','')}' Actual='{e.get('actual','')}'")

print()

# Check recent events - Aug 1 to Aug 18 - have actual values?
print("=== Recent Events (Aug 1-18) ===")
high_recent = [e for e in events 
               if '2026-08' in e.get('time','') 
               and e.get('impact','') in ['red','orange']
               and e.get('time','') < '2026-08-18T00:00:00Z']
print(f"High/Med impact events Aug 1-18: {len(high_recent)}")
has_actual = [e for e in high_recent if e.get('actual','').strip()]
print(f"Have actual value: {len(has_actual)}")
print(f"Missing actual: {len(high_recent) - len(has_actual)}")
print()

# Show ones missing actual (past events that should have it)
missing = [e for e in high_recent if not e.get('actual','').strip() and 'holiday' not in e['title'].lower()]
print(f"Missing actual (non-holiday, past, high/med impact): {len(missing)}")
for e in missing[:10]:
    print(f"  {e['time'][:10]} [{e.get('impact','')[:3]}] {e['currency']} - {e['title']}")
    print(f"    Prev='{e.get('previous','')}' Forecast='{e.get('forecast','')}'")
