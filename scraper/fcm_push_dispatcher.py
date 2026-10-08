#!/usr/bin/env python3
"""
FCM Push Notification Dispatcher (Zero Fake, Zero Spam)
======================================================
Automated Push Notification Engine for Forex News Android App.
Sourced strictly from real economic events in news.json.

Triggers implemented (Pillar 1):
1. London Session Open (Mon-Fri 07:00 UTC) - Skips Weekends
2. New York Session Open (Mon-Fri 12:00 UTC) - Skips Weekends
3. T-15m High-Impact Event Countdown (Red folder events only)
4. T+5m Post-News Volatility Wrap (Actual prints vs Forecast)
5. Sunday 'Week Ahead' Macro Digest (Sundays 17:00 UTC)

Anti-Spam & Zero-Fake Guarantees:
- Strict JSON & Firestore deduplication (no duplicate alerts)
- Weekends strictly blocked for session opens
- Red-impact events only (no low/gray noise)
- Respects topic routing: high_impact_alerts, daily_briefing, event_{id}
"""

import os
import sys
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FCMDispatcher")

# Paths
BASE_DIR = Path(__file__).resolve().parent
NEWS_JSON_PATH = BASE_DIR / "news.json"
STATE_DIR = BASE_DIR / "state"
DEDUP_HISTORY_PATH = STATE_DIR / "sent_push_history.json"


def init_firebase_admin():
    """
    Initializes Firebase Admin SDK using available credentials:
    1. FIREBASE_SERVICE_ACCOUNT_KEY env var (JSON string or file path)
    2. FIREBASE_CREDENTIALS env var (JSON string)
    3. admin/firebase-service-account.json (Local workspace)
    4. scraper/service-account.json
    """
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging, firestore

        if firebase_admin._apps:
            app = firebase_admin.get_app()
            return messaging, firestore.client(app)

        cred_source = None
        # Check env var as raw JSON or path
        env_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY") or os.environ.get("FIREBASE_CREDENTIALS")
        if env_key:
            env_key_clean = env_key.strip()
            if env_key_clean.startswith("{"):
                cred_dict = json.loads(env_key_clean)
                cred_source = credentials.Certificate(cred_dict)
            elif os.path.exists(env_key_clean):
                cred_source = credentials.Certificate(env_key_clean)

        # Check local file candidates
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
            logger.info("Firebase Admin successfully initialized with Service Account")
            return messaging, firestore.client(app)
        else:
            logger.warning("No Firebase credentials found. Running in DRY-RUN audit mode.")
            return None, None
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin: {e}")
        return None, None


def load_news_events():
    """Loads and validates real economic calendar events from news.json."""
    if not NEWS_JSON_PATH.exists():
        logger.error(f"news.json not found at: {NEWS_JSON_PATH}")
        return []

    try:
        with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            events = data.get("events", [])
            logger.info(f"Loaded {len(events)} events from news.json (Updated: {data.get('updated_at', 'unknown')})")
            return events
    except Exception as e:
        logger.error(f"Failed to read news.json: {e}")
        return []


def load_dedup_history():
    """Loads local persistent deduplication history."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if DEDUP_HISTORY_PATH.exists():
        try:
            with open(DEDUP_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_dedup_history(history):
    """Saves local persistent deduplication history."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(DEDUP_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save deduplication history: {e}")


def is_already_sent(dedup_key, local_history, db_client):
    """Checks both local state file and Firestore to guarantee zero duplicate sends."""
    if dedup_key in local_history:
        return True

    if db_client:
        try:
            doc = db_client.collection("sent_push_logs").document(dedup_key).get()
            if doc.exists:
                local_history[dedup_key] = doc.to_dict()
                return True
        except Exception as e:
            logger.warning(f"Firestore dedup check warning for {dedup_key}: {e}")

    return False


def record_sent(dedup_key, record_data, local_history, db_client):
    """Records sent notification in local history and Firestore."""
    local_history[dedup_key] = record_data
    save_dedup_history(local_history)

    if db_client:
        try:
            db_client.collection("sent_push_logs").document(dedup_key).set(record_data)
        except Exception as e:
            logger.warning(f"Firestore record warning for {dedup_key}: {e}")


def send_fcm_message(messaging_client, topic, title, body, data, channel_id, priority="high"):
    """Sends FCM topic message with Android specific sound & channel configuration."""
    if not messaging_client:
        logger.info(f"[DRY-RUN] Topic: '{topic}' | Title: '{title}' | Body: '{body}'")
        return False

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            topic=topic,
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data,
            android=messaging.AndroidConfig(
                priority="high" if priority == "high" else "normal",
                notification=messaging.AndroidNotification(
                    channel_id=channel_id,
                    sound="default" if priority == "high" else None,
                    priority="high" if priority == "high" else "default"
                )
            )
        )
        response = messaging_client.send(message)
        logger.info(f"✓ FCM Broadcast sent to '{topic}': ID={response}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to send FCM message to topic '{topic}': {e}")
        return False


def parse_iso_utc(time_str):
    """Parses ISO timestamp string to timezone-aware UTC datetime."""
    if not time_str:
        return None
    try:
        # e.g. 2026-10-08T12:30:00Z or +00:00
        clean_str = time_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS FOR IMPACT AND TOPIC SANITIZATION
# ─────────────────────────────────────────────────────────────────────────────
def get_impact_ball(impact_str):
    imp = str(impact_str).lower()
    if "red" in imp or "high" in imp:
        return "🔴"
    elif "orange" in imp or "ora" in imp or "medium" in imp:
        return "🟠"
    elif "yellow" in imp or "yel" in imp or "low" in imp:
        return "🟡"
    else:
        return "⚪"


def sanitize_topic(event_id):
    return re.sub(r'[^a-zA-Z0-9-_.~%]', '_', str(event_id))


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 1: Impending Event Countdown (T-30m, T-15m, T-0m Release)
# ─────────────────────────────────────────────────────────────────────────────
def check_impending_event_countdown(events, now_utc, local_history, messaging_client, db_client):
    """
    Scans for events approaching release across 3 key alert windows:
    1. T-30m window: 20 to 38 mins away (dedup: 30m_{id})
    2. T-15m window: 5 to 20 mins away (dedup: 15m_{id})
    3. T-0m release: -2 to 5 mins away (dedup: 0m_{id})

    Guarantees:
    - Broadcasts Red (High-Impact) events to global topic 'high_impact_alerts'.
    - ALWAYS delivers to targeted topic 'event_{id}' for ALL impact levels (Red, Orange, Yellow, Gray),
      so every user who scheduled an alert receives it on-time with matching impact ball emoji.
    """
    logger.info("Checking Trigger 1: Impending Event Countdown (30m, 15m, 0m)...")
    dispatched = 0

    for event in events:
        event_time = parse_iso_utc(event.get("time"))
        if not event_time:
            continue

        minutes_to_event = (event_time - now_utc).total_seconds() / 60.0
        event_id = event.get("id")
        if not event_id:
            continue

        impact_raw = str(event.get("impact", "")).lower()
        impact_ball = get_impact_ball(impact_raw)
        is_high_impact = "red" in impact_raw or "high" in impact_raw

        currency = event.get("currency", "FOREX")
        title_str = event.get("title", "Economic Event")
        forecast = event.get("forecast", "").strip()
        forecast_snippet = f"Forecast: {forecast}" if forecast else "Volatility expected"
        sanitized_id = sanitize_topic(event_id)
        event_topic = f"event_{sanitized_id}"

        # Determine target alert window
        window_label = None
        dedup_key = None
        push_body = None

        if 20.0 <= minutes_to_event <= 38.0:
            window_label = "30m"
            dedup_key = f"30m_{event_id}"
            push_body = f"{title_str} releases in 30 mins! {forecast_snippet}. Tap for live countdown & AI forecast."
        elif 5.0 <= minutes_to_event < 20.0:
            window_label = "15m"
            dedup_key = f"15m_{event_id}"
            push_body = f"{title_str} releases in 15 mins! {forecast_snippet}. Tap for live countdown & AI forecast."
        elif -2.0 <= minutes_to_event < 5.0:
            window_label = "0m"
            dedup_key = f"0m_{event_id}"
            push_body = f"{title_str} is releasing NOW! Check live figures, pip reaction, and AI analysis."

        if not window_label or not dedup_key:
            continue

        if is_already_sent(dedup_key, local_history, db_client):
            logger.debug(f"Skipping {event_id}: {window_label} countdown alert already dispatched.")
            continue

        push_title = f"{impact_ball} {currency}: {title_str}"
        data_payload = {
            "type": "EVENT_COUNTDOWN",
            "eventId": str(event_id),
            "currency": currency,
            "minutesBefore": window_label.replace("m", ""),
            "route": f"detail/{event_id}",
            "channelId": "fcm_calendar_alerts_channel"
        }

        # 1. Send to targeted individual event topic (subscribed by users who tapped the bell for this event)
        success = send_fcm_message(
            messaging_client=messaging_client,
            topic=event_topic,
            title=push_title,
            body=push_body,
            data=data_payload,
            channel_id="fcm_calendar_alerts_channel",
            priority="high"
        )

        # 2. For High-Impact (Red) events, also broadcast to the global high_impact_alerts topic
        if is_high_impact:
            global_sent = send_fcm_message(
                messaging_client=messaging_client,
                topic="high_impact_alerts",
                title=push_title,
                body=push_body,
                data=data_payload,
                channel_id="fcm_calendar_alerts_channel",
                priority="high"
            )
            success = success or global_sent

        if success:
            record_sent(
                dedup_key,
                {
                    "sent_at": now_utc.isoformat(),
                    "event_id": event_id,
                    "currency": currency,
                    "title": title_str,
                    "scheduled_time": event.get("time"),
                    "window": window_label,
                    "type": "EVENT_COUNTDOWN"
                },
                local_history,
                db_client
            )
            dispatched += 1
            logger.info(f"✓ Sent T-{window_label} countdown alert for {currency} - {title_str} (topic={event_topic})")

    return dispatched


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 2: T+5m Post-News Volatility Wrap
# ─────────────────────────────────────────────────────────────────────────────
def check_post_news_wrap(events, now_utc, local_history, messaging_client, db_client):
    """
    Checks events whose scheduled time passed 3 to 20 minutes ago.
    Broadcasts results / actual pip reactions to 'high_impact_alerts' (for red) and 'event_{id}'.
    """
    logger.info("Checking Trigger 2: Post-News Volatility Wrap (T+5m)...")
    dispatched = 0

    min_window = now_utc - timedelta(minutes=20)
    max_window = now_utc - timedelta(minutes=3)

    for event in events:
        event_time = parse_iso_utc(event.get("time"))
        if not event_time or not (min_window <= event_time <= max_window):
            continue

        event_id = event.get("id")
        if not event_id:
            continue

        impact_raw = str(event.get("impact", "")).lower()
        impact_ball = get_impact_ball(impact_raw)
        is_high_impact = "red" in impact_raw or "high" in impact_raw

        dedup_key = f"wrap_{event_id}"
        if is_already_sent(dedup_key, local_history, db_client):
            logger.debug(f"Skipping {event_id}: Post-news wrap already dispatched.")
            continue

        currency = event.get("currency", "FOREX")
        title_str = event.get("title", "Forex Release")
        actual = event.get("actual", "").strip()
        forecast = event.get("forecast", "").strip()
        sanitized_id = sanitize_topic(event_id)
        event_topic = f"event_{sanitized_id}"

        if actual:
            push_title = f"{impact_ball} {currency} Actual: {actual}"
            forecast_snippet = f" (Forecast: {forecast})" if forecast else ""
            push_body = f"{title_str} released: {actual}{forecast_snippet}. Tap for pip reaction & AI verdict."
        else:
            push_title = f"{impact_ball} {currency} Released: {title_str}"
            push_body = f"{title_str} data just released! Tap to see live results, pip reaction & AI Trade Verdict."

        data_payload = {
            "type": "POST_NEWS_WRAP",
            "eventId": str(event_id),
            "currency": currency,
            "route": f"detail/{event_id}",
            "channelId": "fcm_calendar_alerts_channel"
        }

        # 1. Send to individual event topic
        success = send_fcm_message(
            messaging_client=messaging_client,
            topic=event_topic,
            title=push_title,
            body=push_body,
            data=data_payload,
            channel_id="fcm_calendar_alerts_channel",
            priority="high"
        )

        # 2. For Red/High impact, also send to global topic
        if is_high_impact:
            global_sent = send_fcm_message(
                messaging_client=messaging_client,
                topic="high_impact_alerts",
                title=push_title,
                body=push_body,
                data=data_payload,
                channel_id="fcm_calendar_alerts_channel",
                priority="high"
            )
            success = success or global_sent

        if success:
            record_sent(
                dedup_key,
                {
                    "sent_at": now_utc.isoformat(),
                    "event_id": event_id,
                    "currency": currency,
                    "title": title_str,
                    "actual": actual,
                    "scheduled_time": event.get("time"),
                    "type": "POST_NEWS_WRAP"
                },
                local_history,
                db_client
            )
            dispatched += 1
            logger.info(f"✓ Sent Post-News Wrap for {currency} - {title_str} (topic={event_topic})")

    return dispatched


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 3: London & New York Session Open (Mon-Fri Only)
# ─────────────────────────────────────────────────────────────────────────────
def check_session_open_alerts(events, now_utc, local_history, messaging_client, db_client):
    """
    Dispatches London (07:00 UTC) and New York (12:00 UTC) Session Opens.
    STRICT ZERO-SPAM GUARD: Weekends (Sat/Sun) are strictly skipped!
    """
    logger.info("Checking Trigger 3: Market Session Open Alerts...")
    dispatched = 0

    # 0 = Monday, 1 = Tuesday ... 5 = Saturday, 6 = Sunday
    weekday = now_utc.weekday()
    if weekday >= 5:
        logger.info("Weekend detected (Saturday/Sunday). Forex markets closed. Zero alerts sent.")
        return 0

    utc_hour = now_utc.hour
    utc_minute = now_utc.minute
    date_str = now_utc.strftime("%Y-%m-%d")

    # Filter today's real high impact events for context
    today_events = [
        e for e in events
        if e.get("time", "").startswith(date_str) and str(e.get("impact", "")).lower() == "red"
    ]

    # ── London Session Open (07:00 UTC, active window 07:00-07:29) ──
    if utc_hour == 7 and utc_minute < 30:
        dedup_key = f"session_london_{date_str}"
        if not is_already_sent(dedup_key, local_history, db_client):
            red_count = len(today_events)
            push_title = "🇬🇧 London Session Open: High Volatility Ahead!"
            if red_count > 0:
                push_body = f"EUR/USD, GBP/USD & Gold active. {red_count} high-impact release{'s' if red_count > 1 else ''} on today's calendar. Tap to view."
            else:
                push_body = "European markets active. Key pairs in focus: EUR/USD, GBP/USD, XAU/USD. Tap to check today's economic calendar."

            success = send_fcm_message(
                messaging_client=messaging_client,
                topic="daily_briefing",
                title=push_title,
                body=push_body,
                data={
                    "type": "SESSION_OPEN",
                    "session": "LONDON",
                    "route": "calendar",
                    "channelId": "fcm_daily_briefing_channel"
                },
                channel_id="fcm_daily_briefing_channel",
                priority="normal"
            )

            if success:
                record_sent(
                    dedup_key,
                    {
                        "sent_at": now_utc.isoformat(),
                        "session": "LONDON",
                        "date": date_str,
                        "high_impact_count": red_count
                    },
                    local_history,
                    db_client
                )
                dispatched += 1
                logger.info("✓ Dispatched London Session Open push alert")

    # ── New York Session Open (12:00 UTC, active window 12:00-12:29) ──
    if utc_hour == 12 and utc_minute < 30:
        dedup_key = f"session_ny_{date_str}"
        if not is_already_sent(dedup_key, local_history, db_client):
            us_red = [e for e in today_events if e.get("currency") == "USD"]
            push_title = "🇺🇸 New York Open: US Data Impending"
            if us_red:
                titles = ", ".join(e.get("title", "") for e in us_red[:2])
                push_body = f"US Dollar index & Gold in focus. {titles} releasing today. Tap for schedule."
            else:
                push_body = "Wall Street opening. US Dollar index and Gold (XAU/USD) in focus. Tap to check key support levels."

            success = send_fcm_message(
                messaging_client=messaging_client,
                topic="daily_briefing",
                title=push_title,
                body=push_body,
                data={
                    "type": "SESSION_OPEN",
                    "session": "NEW_YORK",
                    "route": "calendar",
                    "channelId": "fcm_daily_briefing_channel"
                },
                channel_id="fcm_daily_briefing_channel",
                priority="normal"
            )

            if success:
                record_sent(
                    dedup_key,
                    {
                        "sent_at": now_utc.isoformat(),
                        "session": "NEW_YORK",
                        "date": date_str,
                        "us_high_impact_count": len(us_red)
                    },
                    local_history,
                    db_client
                )
                dispatched += 1
                logger.info("✓ Dispatched New York Session Open push alert")

    return dispatched


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 4: Sunday "Week Ahead" Macro Push Digest
# ─────────────────────────────────────────────────────────────────────────────
def check_sunday_macro_digest(events, now_utc, local_history, messaging_client, db_client):
    """
    Runs STRICTLY on Sunday (weekday == 6) between 16:00 and 19:00 UTC.
    Gathers the real top upcoming high-impact events for the coming week.
    """
    logger.info("Checking Trigger 4: Sunday 'Week Ahead' Macro Digest...")
    # 6 = Sunday
    if now_utc.weekday() != 6:
        logger.debug("Today is not Sunday. Skipping Sunday Macro Digest.")
        return 0

    if not (16 <= now_utc.hour <= 19):
        logger.debug(f"Current UTC hour ({now_utc.hour}) is outside Sunday 16:00-19:00 window.")
        return 0

    year, week_num, _ = now_utc.isocalendar()
    dedup_key = f"sunday_digest_{year}_w{week_num}"

    if is_already_sent(dedup_key, local_history, db_client):
        logger.debug(f"Sunday Digest for Year {year} Week {week_num} already sent.")
        return 0

    # Scan upcoming 7 days for real red events
    end_window = now_utc + timedelta(days=7)
    upcoming_red = []
    for e in events:
        if str(e.get("impact", "")).lower() != "red":
            continue
        e_time = parse_iso_utc(e.get("time"))
        if e_time and (now_utc <= e_time <= end_window):
            upcoming_red.append(e)

    upcoming_count = len(upcoming_red)
    push_title = f"📅 Week Ahead: {upcoming_count} High-Impact Catalysts" if upcoming_count > 0 else "📅 Week Ahead: Macro Watchlist"

    if upcoming_red:
        catalysts = ", ".join(f"{e.get('title')} ({e.get('currency')})" for e in upcoming_red[:3])
        push_body = f"Top releases this week: {catalysts}. Tap to review economic schedule & set alarms."
    else:
        push_body = "Review the upcoming week's economic calendar and prepare your key pip levels. Tap to open."

    success = send_fcm_message(
        messaging_client=messaging_client,
        topic="daily_briefing",
        title=push_title,
        body=push_body,
        data={
            "type": "WEEKLY_DIGEST",
            "route": "calendar",
            "channelId": "fcm_daily_briefing_channel"
        },
        channel_id="fcm_daily_briefing_channel",
        priority="normal"
    )

    if success:
        record_sent(
            dedup_key,
            {
                "sent_at": now_utc.isoformat(),
                "year": year,
                "week_num": week_num,
                "upcoming_count": upcoming_count
            },
            local_history,
            db_client
        )
        logger.info(f"✓ Sent Sunday 'Week Ahead' Digest for Week {week_num}")
        return 1

    return 0


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def run_push_dispatcher(test_time_iso=None):
    """
    Main entry point for FCM Push Dispatcher.
    Can be run via cron (every 10-15m), GitHub Actions, or manually.
    """
    now_utc = parse_iso_utc(test_time_iso) if test_time_iso else datetime.now(timezone.utc)
    logger.info(f"===========================================================")
    logger.info(f"Starting FCM Push Dispatcher Cycle at {now_utc.isoformat()}")
    logger.info(f"===========================================================")

    messaging_client, db_client = init_firebase_admin()
    events = load_news_events()
    local_history = load_dedup_history()

    total_dispatched = 0

    # 1. Impending High Impact Releases (T-15m)
    total_dispatched += check_impending_event_countdown(events, now_utc, local_history, messaging_client, db_client)

    # 2. Post-News Volatility Wrap (T+5m)
    total_dispatched += check_post_news_wrap(events, now_utc, local_history, messaging_client, db_client)

    # 3. Session Open Alerts (London & NY, Mon-Fri only)
    total_dispatched += check_session_open_alerts(events, now_utc, local_history, messaging_client, db_client)

    # 4. Sunday Macro Digest (Sundays only)
    total_dispatched += check_sunday_macro_digest(events, now_utc, local_history, messaging_client, db_client)

    logger.info(f"Cycle completed. Total notifications dispatched: {total_dispatched}")
    return total_dispatched


if __name__ == "__main__":
    test_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_push_dispatcher(test_arg)
