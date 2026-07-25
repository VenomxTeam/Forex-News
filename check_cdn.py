import requests
res = requests.get('https://cdn.jsdelivr.net/gh/VenomxTeam/Forex-News@main/scraper/news.json').json()
if 'events' in res:
    data = res['events']
else:
    data = res
print([x['time'] for x in data if x['id'] == 'cad_cpi_mm_20260720'])
