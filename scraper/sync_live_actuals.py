#!/usr/bin/env python3
"""
Sync Live Actual Releases from TradingView Calendar directly into news.json.
Provides ultra-low latency actuals updates without relying on Selenium or web scraping.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

COUNTRY_TO_CCY = {
    "US": "USD", "CA": "CAD", "GB": "GBP", "EU": "EUR", "DE": "EUR",
    "FR": "EUR", "IT": "EUR", "ES": "EUR", "JP": "JPY", "AU": "AUD",
    "NZ": "NZD", "CH": "CHF", "CN": "CNY"
}

def format_tv_value(val, scale, unit, title):
    if val is None:
        return ""
    if val % 1.0 == 0.0:
        s = str(int(val))
    else:
        s = f"{val:.1f}"
        
    if scale:
        return f"{s}{scale}"
        
    lower = title.lower()
    is_percent = (
        unit == "%" or
        "rate" in lower or
        "earnings" in lower or
        "cpi" in lower or
        "ppi" in lower or
        "pce" in lower or
        "inflation" in lower or
        "growth" in lower or
        ("sales" in lower and "m/m" in lower) or
        ("orders" in lower and "m/m" in lower)
    )
    if is_percent and not s.endswith("%"):
        return f"{s}%"
    return s

def is_tradingview_match(tv_title, local_title):
    tv = tv_title.lower().replace('&', 'and')
    loc = local_title.lower()

    # Generic exclusions
    if 'u6' in tv and 'u6' not in loc:
        return False
    if 'private' in tv and 'private' not in loc:
        return False
    if 'manufacturing' in tv and 'manufacturing' not in loc and 'pmi' not in loc:
        return False
    if 'full time' in tv or 'part time' in tv:
        return False
    if 'ex food energy and trade' in tv or 'machinery manufacturing' in tv:
        return False

    # Sub-indicator specificity guards
    for spec in ['italian', 'french', 'german', 'spanish', 'goods', 'services', 'median', 'trimmed', 'common', 'flash', 'final', 'prelim']:
        if (spec in tv) != (spec in loc):
            return False

    # Claims specificity (Initial vs Continuing vs 4-Week Average)
    tv_is_avg = '4-week' in tv or 'average' in tv
    loc_is_avg = '4-week' in loc or 'average' in loc
    if tv_is_avg != loc_is_avg:
        return False

    tv_is_cont = 'continuing' in tv
    loc_is_cont = 'continuing' in loc
    if tv_is_cont != loc_is_cont:
        return False

    # Core / Headline isolation
    tv_is_core = 'core' in tv or 'ex food' in tv
    loc_is_core = 'core' in loc
    if tv_is_core != loc_is_core:
        return False

    # Period isolation (MoM vs YoY vs QoQ)
    tv_mom = 'mom' in tv or 'm/m' in tv
    loc_mom = 'm/m' in loc or 'mom' in loc
    tv_yoy = 'yoy' in tv or 'y/y' in tv
    loc_yoy = 'y/y' in loc or 'yoy' in loc
    tv_qoq = 'qoq' in tv or 'q/q' in tv
    loc_qoq = 'q/q' in loc or 'qoq' in loc

    if (tv_mom or loc_mom) and (tv_mom != loc_mom):
        return False
    if (tv_yoy or loc_yoy) and (tv_yoy != loc_yoy):
        return False
    if (tv_qoq or loc_qoq) and (tv_qoq != loc_qoq):
        return False

    # Indicator checks
    if ('ppi' in tv or 'producer' in tv) and ('ppi' in loc or 'producer' in loc):
        return True
    if ('cpi' in tv or 'consumer price' in tv or 'harmonised index' in tv) and ('cpi' in loc or 'consumer price' in loc or 'hicp' in loc):
        return True
    if ('pce' in tv or 'personal consumption' in tv) and ('pce' in loc or 'personal consumption' in loc):
        return True
    if ('non farm' in tv or 'nonfarm' in tv) and ('non-farm' in loc or 'nonfarm' in loc or 'nfp' in loc):
        return True
    if 'unemployment rate' in tv and 'unemployment rate' in loc:
        return True
    if 'hourly earnings' in tv and 'hourly earnings' in loc:
        return True
    if 'employment change' in tv and 'employment change' in loc:
        return True
    if ('jobless claims' in tv or 'initial claims' in tv) and ('jobless claims' in loc or 'unemployment claims' in loc or 'claims' in loc):
        return True
    if 'retail sales' in tv and 'retail sales' in loc:
        return True
    if 'gdp' in tv and 'gdp' in loc:
        return True
    if 'pmi' in tv and 'pmi' in loc:
        return True
    if 'durable goods' in tv and 'durable goods' in loc:
        return True
    if ('interest rate' in tv or 'rate decision' in tv or 'fed funds' in tv or 'official bank rate' in tv) and ('interest rate' in loc or 'rate decision' in loc or 'federal funds' in loc or 'rate statement' in loc):
        return True
    if ('consumer sentiment' in tv or 'consumer confidence' in tv or 'consumer climate' in tv) and ('consumer sentiment' in loc or 'consumer confidence' in loc or 'consumer climate' in loc):
        return True
    if ('inflation expectations' in tv or 'michigan inflation' in tv) and 'inflation expectations' in loc:
        return True
    if ('trade balance' in tv or 'balance of trade' in tv) and ('trade balance' in loc or 'balance of trade' in loc):
        return True
    if ('building permits' in tv or 'housing starts' in tv) and ('building permits' in loc or 'housing starts' in loc):
        return True
    if 'ivey pmi' in tv and 'ivey pmi' in loc:
        return True
    if ('foreign currency reserves' in tv or 'foreign exchange reserves' in tv) and ('foreign currency reserves' in loc or 'foreign exchange reserves' in loc):
        return True

    return False

def sync_live_actuals(news_file='news.json', days_back=5, days_forward=2):
    if not os.path.exists(news_file):
        print(f"File not found: {news_file}")
        return 0

    now_utc = datetime.now(timezone.utc)
    from_date = (now_utc - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00.000Z")
    to_date = (now_utc + timedelta(days=days_forward)).strftime("%Y-%m-%dT23:59:59.000Z")

    url = f"https://economic-calendar.tradingview.com/events?from={from_date}&to={to_date}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Origin': 'https://www.tradingview.com',
        'Referer': 'https://www.tradingview.com/'
    })

    print(f"Fetching TradingView calendar: {from_date[:10]} to {to_date[:10]}...")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('result', [])
    except Exception as e:
        print(f"Failed to fetch TradingView data: {e}")
        return 0

    print(f"TradingView returned {len(results)} events")

    with open(news_file, 'r', encoding='utf-8') as f:
        local_data = json.load(f)

    local_events = local_data.get('events', [])
    updated_count = 0

    for tv_ev in results:
        actual_raw = tv_ev.get('actual')
        if actual_raw is None:
            continue

        country = tv_ev.get('country', '')
        ccy = COUNTRY_TO_CCY.get(country)
        if not ccy:
            continue

        tv_title = tv_ev.get('title', '')
        tv_date = tv_ev.get('date', '')
        tv_day = tv_date[:10] if len(tv_date) >= 10 else ''
        scale = tv_ev.get('scale', '') or ''
        unit = tv_ev.get('unit', '') or ''
        forecast_raw = tv_ev.get('forecast')
        previous_raw = tv_ev.get('previous')

        for loc_ev in local_events:
            loc_time = loc_ev.get('time', '')
            if not loc_time.startswith(tv_day):
                continue
            if loc_ev.get('currency', '').upper() != ccy:
                continue

            loc_title = loc_ev.get('title', '')
            if is_tradingview_match(tv_title, loc_title):
                formatted_actual = format_tv_value(actual_raw, scale, unit, loc_title)
                formatted_forecast = format_tv_value(forecast_raw, scale, unit, loc_title)
                formatted_previous = format_tv_value(previous_raw, scale, unit, loc_title)

                existing_actual = loc_ev.get('actual', '')
                if formatted_actual and formatted_actual != existing_actual:
                    loc_ev['actual'] = formatted_actual
                    if formatted_forecast and (not loc_ev.get('forecast') or loc_ev.get('forecast') in ['—', '-']):
                        loc_ev['forecast'] = formatted_forecast
                    if formatted_previous and (not loc_ev.get('previous') or loc_ev.get('previous') in ['—', '-']):
                        loc_ev['previous'] = formatted_previous
                    updated_count += 1
                    print(f"  ✓ Updated {loc_title} [{ccy}]: actual='{formatted_actual}' (prev was '{existing_actual}')")

    if updated_count > 0:
        local_data['updated_at'] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(news_file, 'w', encoding='utf-8') as f:
            json.dump(local_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {updated_count} live actual updates to {news_file}")
    else:
        print("No new actual updates needed (all matching events already up-to-date)")

    return updated_count

if __name__ == '__main__':
    target_file = sys.argv[1] if len(sys.argv) > 1 else 'news.json'
    sync_live_actuals(target_file)
