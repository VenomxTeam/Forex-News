#!/usr/bin/env python3
"""
Central Bank Rates Real-Time Firestore Sync
===========================================
Synchronizes benchmark interest rates and upcoming policy decision
schedules for the 8 major global central banks into Google Cloud Firestore:
- FED: Federal Reserve (USD)
- ECB: European Central Bank (EUR)
- BOE: Bank of England (GBP)
- BOJ: Bank of Japan (JPY)
- BOC: Bank of Canada (CAD)
- RBA: Reserve Bank of Australia (AUD)
- SNB: Swiss National Bank (CHF)
- RBNZ: Reserve Bank of New Zealand (NZD)

Features:
1. Primary JSON feed: https://interestratedecision.com/data/rates.json
2. Authoritative cross-check: Bank of Canada Valet API (series V39079)
3. Safety bounds validation (-2.0 <= rate <= 30.0)
4. Monetary stance & bias calculation (Rate Hikes, Rate Cuts, Hawkish Hold, Dovish Hold, Neutral)
5. Firestore collection /central_bank_rates/{bankCode} upserts with merge=True
6. Graceful dry-run fallback if credentials are unavailable
"""

import os
import sys
import json
import logging
import argparse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CentralBankSync")

BASE_DIR = Path(__file__).resolve().parent

BANK_MAPPING = {
    "fed": "FED",
    "ecb": "ECB",
    "boe": "BOE",
    "boj": "BOJ",
    "boc": "BOC",
    "rba": "RBA",
    "snb": "SNB",
    "rbnz": "RBNZ"
}

BANK_METADATA = {
    "FED": {
        "currency": "USD",
        "countryFlag": "🇺🇸",
        "bankName": "Federal Reserve",
        "economy": "USA",
        "policyInstrument": "Federal Funds Target Range (Upper Bound)",
        "officialRateSource": "U.S. Federal Reserve (FOMC)",
        "officialCpiSource": "U.S. Bureau of Labor Statistics",
        "defaultCpi": 2.7,
        "cpiReleaseDate": "14 Oct 2026",
        "defaultPreviousRate": 3.75,
        "defaultSourceUrl": "https://interestratedecision.com/fed/",
    },
    "ECB": {
        "currency": "EUR",
        "countryFlag": "🇪🇺",
        "bankName": "European Central Bank",
        "economy": "Eurozone",
        "policyInstrument": "Deposit Facility Rate",
        "officialRateSource": "European Central Bank (ECB)",
        "officialCpiSource": "Eurostat (HICP)",
        "defaultCpi": 2.2,
        "cpiReleaseDate": "17 Oct 2026",
        "defaultPreviousRate": 2.75,
        "defaultSourceUrl": "https://interestratedecision.com/ecb/",
    },
    "BOE": {
        "currency": "GBP",
        "countryFlag": "🇬🇧",
        "bankName": "Bank of England",
        "economy": "UK",
        "policyInstrument": "Official Bank Rate",
        "officialRateSource": "Bank of England (MPC)",
        "officialCpiSource": "UK Office for National Statistics (ONS)",
        "defaultCpi": 2.2,
        "cpiReleaseDate": "16 Oct 2026",
        "defaultPreviousRate": 4.25,
        "defaultSourceUrl": "https://interestratedecision.com/boe/",
    },
    "BOJ": {
        "currency": "JPY",
        "countryFlag": "🇯🇵",
        "bankName": "Bank of Japan",
        "economy": "Japan",
        "policyInstrument": "Short-Term Policy Interest Rate",
        "officialRateSource": "Bank of Japan (Policy Board)",
        "officialCpiSource": "Statistics Bureau of Japan",
        "defaultCpi": 2.5,
        "cpiReleaseDate": "20 Oct 2026",
        "defaultPreviousRate": 1.00,
        "defaultSourceUrl": "https://interestratedecision.com/boj/",
    },
    "BOC": {
        "currency": "CAD",
        "countryFlag": "🇨🇦",
        "bankName": "Bank of Canada",
        "economy": "Canada",
        "policyInstrument": "Target for the Overnight Rate",
        "officialRateSource": "Bank of Canada (Governing Council)",
        "officialCpiSource": "Statistics Canada",
        "defaultCpi": 1.9,
        "cpiReleaseDate": "19 Oct 2026",
        "defaultPreviousRate": 2.75,
        "defaultSourceUrl": "https://interestratedecision.com/boc/",
    },
    "RBA": {
        "currency": "AUD",
        "countryFlag": "🇦🇺",
        "bankName": "Reserve Bank of Australia",
        "economy": "Australia",
        "policyInstrument": "Cash Rate Target",
        "officialRateSource": "Reserve Bank of Australia (Board)",
        "officialCpiSource": "Australian Bureau of Statistics",
        "defaultCpi": 3.2,
        "cpiReleaseDate": "28 Oct 2026",
        "defaultPreviousRate": 4.35,
        "defaultSourceUrl": "https://interestratedecision.com/rba/",
    },
    "SNB": {
        "currency": "CHF",
        "countryFlag": "🇨🇭",
        "bankName": "Swiss National Bank",
        "economy": "Switzerland",
        "policyInstrument": "SNB Policy Rate",
        "officialRateSource": "Swiss National Bank (Governing Board)",
        "officialCpiSource": "Swiss Federal Statistical Office",
        "defaultCpi": 0.8,
        "cpiReleaseDate": "03 Oct 2026",
        "defaultPreviousRate": 0.25,
        "defaultSourceUrl": "https://interestratedecision.com/snb/",
    },
    "RBNZ": {
        "currency": "NZD",
        "countryFlag": "🇳🇿",
        "bankName": "Reserve Bank of New Zealand",
        "economy": "New Zealand",
        "policyInstrument": "Official Cash Rate (OCR)",
        "officialRateSource": "Reserve Bank of New Zealand (MPC)",
        "officialCpiSource": "Statistics New Zealand",
        "defaultCpi": 2.2,
        "cpiReleaseDate": "15 Oct 2026",
        "defaultPreviousRate": 3.00,
        "defaultSourceUrl": "https://interestratedecision.com/rbnz/",
    },
}


def init_firestore(dry_run: bool = False):
    """
    Initializes Google Cloud Firestore client.
    Returns Firestore client or None (dry-run mode).
    """
    if dry_run:
        logger.info("Explicit dry-run flag specified. Running without Firestore connection.")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if firebase_admin._apps:
            app = firebase_admin.get_app()
            return firestore.client(app)

        cred_source = None
        env_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY") or os.environ.get("FIREBASE_CREDENTIALS")

        if env_key:
            env_key_clean = env_key.strip()
            if env_key_clean.startswith("{"):
                cred_dict = json.loads(env_key_clean)
                cred_source = credentials.Certificate(cred_dict)
            elif os.path.exists(env_key_clean):
                cred_source = credentials.Certificate(env_key_clean)

        if not cred_source:
            candidates = [
                BASE_DIR.parent / "admin" / "firebase-service-account.json",
                BASE_DIR / "service-account.json",
                BASE_DIR / "firebase-service-account.json",
                BASE_DIR.parent / "admin" / "service-account.json",
            ]
            for c in candidates:
                if c.exists():
                    cred_source = credentials.Certificate(str(c))
                    logger.info(f"Loaded Firebase credentials from: {c}")
                    break

        if cred_source:
            app = firebase_admin.initialize_app(cred_source)
            logger.info("Firebase Admin successfully initialized with Service Account.")
            return firestore.client(app)
        else:
            logger.warning("No Firebase credentials found. Running in DRY-RUN mode.")
            return None
    except Exception as e:
        logger.warning(f"Notice initializing Firebase Admin ({e}). Running in DRY-RUN mode.")
        return None


def fetch_primary_rates() -> list:
    """Fetches real-time benchmark rates from interestratedecision.com."""
    url = "https://interestratedecision.com/data/rates.json"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ForexNewsSync/1.0 (Automated Cron Scraper)"}
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        if res.status != 200:
            raise RuntimeError(f"HTTP {res.status}: Failed to fetch primary rates feed")
        raw = res.read().decode("utf-8")
        data = json.loads(raw)
        return data.get("rates", [])


def fetch_boc_valet_rate() -> float | None:
    """Fetches Bank of Canada official policy rate from Valet API (V39079)."""
    url = "https://www.bankofcanada.ca/valet/observations/V39079/json?recent=1"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ForexNewsSync/1.0 (Bank of Canada Valet Client)"}
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            if res.status == 200:
                raw = res.read().decode("utf-8")
                data = json.loads(raw)
                obs_list = data.get("observations", [])
                if obs_list:
                    rate_str = obs_list[0].get("V39079", {}).get("v")
                    if rate_str:
                        val = float(rate_str)
                        logger.info(f"Bank of Canada Valet API confirmed BOC rate: {val:.2f}%")
                        return val
    except Exception as e:
        logger.warning(f"BOC Valet API check notice: {e} (falling back to primary feed)")
    return None


def calculate_stance_and_bias(current_rate: float, previous_rate: float, cpi_yoy: float):
    """
    Computes monetary policy stance and hawkish/dovish bias.
    Returns: (stance: str, is_hawkish: bool | None)
    """
    delta = current_rate - previous_rate
    real_rate = current_rate - cpi_yoy

    # 1. Direct rate moves supersede hold conditions
    if delta < -0.01:
        return "Rate Cuts", False
    if delta > 0.01:
        return "Rate Hikes", True

    # 2. Holds evaluated by real interest rate (Taylor Principle)
    if real_rate > 2.0:
        return "Hawkish Hold", True
    if real_rate <= 0.0:
        return "Dovish Hold", False

    return "Neutral", None


def format_date_str(epoch_ms: int) -> str:
    """Formats epoch timestamp in milliseconds to 'DD MMM YYYY'."""
    if not epoch_ms:
        return "TBD"
    d = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
    return d.strftime("%d %b %Y")


def parse_iso_to_epoch_ms(iso_str: str | None) -> int:
    """Parses ISO-8601 string to epoch timestamp in milliseconds."""
    if not iso_str:
        return 0
    try:
        clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def sync_central_bank_rates(dry_run: bool = False) -> dict:
    """Main synchronization logic for the 8 major central banks."""
    logger.info("Starting Central Bank Rates Sync Pipeline...")
    db = init_firestore(dry_run=dry_run)

    rates_list = fetch_primary_rates()
    logger.info(f"Fetched {len(rates_list)} bank records from primary rates feed.")

    boc_valet = fetch_boc_valet_rate()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    synced_records = {}
    skipped_records = []

    for item in rates_list:
        raw_bank = (item.get("bank") or "").lower()
        bank_code = BANK_MAPPING.get(raw_bank)
        if not bank_code:
            continue

        meta = BANK_METADATA.get(bank_code)
        if not meta:
            continue

        # Rate determination
        rate_val = float(item["rate"])
        if bank_code == "BOC" and boc_valet is not None:
            rate_val = boc_valet

        # Bounds validation (-2.0 <= rate <= 30.0)
        if not (-2.0 <= rate_val <= 30.0):
            logger.warning(f"Rejecting out-of-bounds rate for {bank_code}: {rate_val}%")
            skipped_records.append((bank_code, rate_val, "Out of bounds"))
            continue

        # Timestamps and dates
        last_change_ms = parse_iso_to_epoch_ms(item.get("lastChange")) or now_ms
        next_decision_ms = parse_iso_to_epoch_ms(item.get("nextDecision"))

        effective_date = format_date_str(last_change_ms)
        next_meeting_date = format_date_str(next_decision_ms) if next_decision_ms > 0 else "TBD"

        # Determine previousRate and preserve existing document delta if available
        previous_rate = meta["defaultPreviousRate"]
        if db:
            try:
                doc_ref = db.collection("central_bank_rates").document(bank_code)
                existing_snap = doc_ref.get()
                if existing_snap.exists:
                    existing_data = existing_snap.to_dict() or {}
                    existing_curr = existing_data.get("currentRate")
                    existing_prev = existing_data.get("previousRate")
                    if isinstance(existing_curr, (int, float)):
                        if abs(existing_curr - rate_val) > 0.001:
                            previous_rate = float(existing_curr)
                        elif isinstance(existing_prev, (int, float)):
                            previous_rate = float(existing_prev)
            except Exception as read_err:
                logger.debug(f"Notice reading existing doc for {bank_code}: {read_err}")

        # Metrics calculation
        cpi_val = float(meta["defaultCpi"])
        delta = round(rate_val - previous_rate, 4)
        real_rate = round(rate_val - cpi_val, 2)
        stance, is_hawkish = calculate_stance_and_bias(rate_val, previous_rate, cpi_val)

        doc_payload = {
            "bankCode": bank_code,
            "currency": meta["currency"],
            "countryFlag": meta["countryFlag"],
            "bankName": meta["bankName"],
            "economy": meta["economy"],
            "policyInstrument": meta["policyInstrument"],
            "rateName": item.get("rateName") or meta["policyInstrument"],
            "currentRate": float(rate_val),
            "previousRate": float(previous_rate),
            "change": float(delta),
            "rateFormatted": f"{rate_val:.2f}%",
            "cpiYoY": float(cpi_val),
            "cpiFormatted": f"{cpi_val:.1f}%",
            "cpiReleaseDate": meta["cpiReleaseDate"],
            "realRate": float(real_rate),
            "stance": stance,
            "isHawkish": is_hawkish,
            "effectiveDate": effective_date,
            "lastChangeTimestamp": int(last_change_ms),
            "nextMeetingDate": next_meeting_date,
            "nextMeetingDateText": next_meeting_date,
            "nextMeetingTimestampEpochMs": int(next_decision_ms),
            "nextMeetingTimestamp": int(next_decision_ms),
            "officialRateSource": meta["officialRateSource"],
            "officialCpiSource": meta["officialCpiSource"],
            "sourceUrl": item.get("page") or meta["defaultSourceUrl"],
            "lastUpdatedTimestamp": int(now_ms),
            "lastSyncTimestamp": int(now_ms),
            "status": "active"
        }

        if db:
            try:
                db.collection("central_bank_rates").document(bank_code).set(doc_payload, merge=True)
                logger.info(
                    f"✅ Synced Firestore: {bank_code} ({meta['currency']}) -> "
                    f"Rate: {rate_val:.2f}% | Prev: {previous_rate:.2f}% | "
                    f"Stance: {stance} | Next: {next_meeting_date}"
                )
            except Exception as write_err:
                logger.error(f"Failed to write {bank_code} to Firestore: {write_err}")
                skipped_records.append((bank_code, rate_val, str(write_err)))
                continue
        else:
            logger.info(
                f"[DRY-RUN] Would sync {bank_code} ({meta['currency']}) -> "
                f"Rate: {rate_val:.2f}% | Stance: {stance} | Next: {next_meeting_date}"
            )

        synced_records[bank_code] = doc_payload

    logger.info(
        f"Central Bank Rates Sync complete: {len(synced_records)}/8 major banks synchronized "
        f"({len(skipped_records)} skipped/failed)."
    )
    return synced_records


def main():
    parser = argparse.ArgumentParser(description="Synchronize central bank rates to Firestore.")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to Firestore.")
    args = parser.parse_args()

    try:
        results = sync_central_bank_rates(dry_run=args.dry_run)
        if len(results) < 8:
            logger.warning(f"Only {len(results)} of 8 banks were synchronized.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in sync_central_bank_rates: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
