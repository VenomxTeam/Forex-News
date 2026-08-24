cd scraper
python scraper.py scrape --config config.yaml --months jan.2026 feb.2026 mar.2026 apr.2026 may.2026 jun.2026 jul.2026 aug.2026 sep.2026 oct.2026 nov.2026 dec.2026
python generate_news_json.py
cd ..
git add .
git commit -m "Scrape all 12 months with updated currencies and revert workflow"
git push origin main
