$ErrorActionPreference = "Stop"

Write-Host "Starting historical scrape for 2024 and 2025..."
$months = "jan.2024","feb.2024","mar.2024","apr.2024","may.2024","jun.2024","jul.2024","aug.2024","sep.2024","oct.2024","nov.2024","dec.2024","jan.2025","feb.2025","mar.2025","apr.2025","may.2025","jun.2025","jul.2025","aug.2025","sep.2025","oct.2025","nov.2025","dec.2025"

python -m ff_calendar_toolkit.cli scrape --months $months

Write-Host "Compiling news.json..."
python generate_news_json.py

Write-Host "Pushing to github..."
git add news/ news.json
git commit -m "Add 2024-2025 historical data for deeper charts"
git push

Write-Host "Done!"
