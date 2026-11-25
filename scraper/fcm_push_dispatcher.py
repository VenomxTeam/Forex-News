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
5. Sunday 'Week Ahead' Macro Digest (Sundays 14:00-19:59 UTC, full week titles)
6. Daily Morning High-Impact Digest (Mon-Fri 01:00-03:59 UTC / 06:30-09:29 AM IST with release times)
7. Automated 2-Hour Retention & Memes (Mon-Fri 08:00 AM - 12:00 AM Midnight IST, India vs Global)
8. Special Weekend & Calendar Retention (Saturday, Sunday, and strictly timed holiday hooks)

Anti-Spam & Zero-Fake Guarantees:
- Strict JSON & Firestore deduplication (no duplicate alerts)
- Weekends strictly blocked for session opens
- Red-impact events only (no low/gray noise)
- Respects topic routing: high_impact_alerts, daily_briefing, event_{id}, india_traders, global_traders
"""

import os
import sys
import json
import logging
import re
import zoneinfo
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

        full_data = {
            "title": str(title),
            "body": str(body),
            "message": str(body),
            "channelId": str(channel_id),
            **(data or {})
        }

        # Data-only high-priority message:
        # Crucial Android FCM architectural rule:
        # When an FCM message contains a top-level 'notification' block, Android OS / Play Services
        # intercepts it in background/killed states and bypasses onMessageReceived().
        # This prevented notificationHistoryDao.insert() from running until the user clicked the notification.
        # By sending a pure data payload with priority="high", ForexFirebaseMessagingService.onMessageReceived()
        # is GUARANTEED to be invoked in foreground, background, and killed states.
        # This ensures:
        # 1. Immediate insertion into Room notification_history so in-app Notifications Screen
        #    shows the notification immediately even if the app was launched without tapping the push.
        # 2. Complete deduplication and deterministic system notification display with large icon & sound.
        message = messaging.Message(
            topic=topic,
            data=full_data,
            android=messaging.AndroidConfig(
                priority="high"
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
            push_body = f"{title_str} released: {actual}{forecast_snippet}. Tap for pip reaction & breaking event impact."
        else:
            push_title = f"{impact_ball} {currency} Released: {title_str}"
            push_body = f"{title_str} data just released! Tap to see live results, pip reaction & economic news impact."

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
# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 3: All 4 Global Market Session Opens (Tokyo, London, NY, Sydney)
# ─────────────────────────────────────────────────────────────────────────────
def check_session_open_alerts(events, now_utc, local_history, messaging_client, db_client):
    """
    Dispatches alerts for ALL 4 Major Market Session Opens:
    1. Tokyo (Asian) Session Open: 09:00 JST (00:00 UTC / 05:30 AM IST) - Weekdays
    2. London (European) Session Open: 08:00 London Time (Europe/London: 08:00 UTC Winter / 07:00 UTC Summer) - Weekdays
    3. New York (US) Session Open: 08:00 NY Time (America/New_York: 13:00 UTC Winter / 12:00 UTC Summer) - Weekdays
    4. Sydney (Pacific) Session Open: 08:00 Sydney Time (Australia/Sydney: 21:00 UTC Summer AEDT / 22:00 UTC Winter AEST) - Weekday mornings & Sunday weekly open

    Zero-Fake & Anti-Spam:
    - Automatically accounts for Daylight Saving Time (DST) across global exchanges.
    - Strictly deduplicated once per session per calendar day.
    - Factual, professional, emojified alerts with real session status and key active currency pairs.
    - Zero fake claims, zero hype, zero spam.
    """
    logger.info("Checking Trigger 3: All 4 Market Session Open Alerts (Tokyo, London, NY, Sydney)...")
    dispatched = 0

    date_str = now_utc.strftime("%Y-%m-%d")

    # Load exchange timezones to accurately handle Daylight Saving Time (DST)
    tz_tokyo = zoneinfo.ZoneInfo("Asia/Tokyo")
    tz_london = zoneinfo.ZoneInfo("Europe/London")
    tz_ny = zoneinfo.ZoneInfo("America/New_York")
    tz_sydney = zoneinfo.ZoneInfo("Australia/Sydney")

    now_tokyo = now_utc.astimezone(tz_tokyo)
    now_london = now_utc.astimezone(tz_london)
    now_ny = now_utc.astimezone(tz_ny)
    now_sydney = now_utc.astimezone(tz_sydney)

    # Filter today's real high-impact events for dynamic context
    today_red = [
        e for e in events
        if e.get("time", "").startswith(date_str) and str(e.get("impact", "")).lower() == "red"
    ]
    red_count = len(today_red)
    day_of_year = now_utc.timetuple().tm_yday

    # Helper function to dispatch session open to both India & Global topics
    def dispatch_session_notification(session_code, dedup_key, in_title, in_body, gl_title, gl_body, route="market"):
        if is_already_sent(dedup_key, local_history, db_client):
            return 0

        ch_id = "fcm_daily_briefing_channel"
        # 1. Send India (Hinglish copy)
        send_fcm_message(
            messaging_client=messaging_client,
            topic="india_traders",
            title=in_title,
            body=in_body,
            data={"type": "SESSION_OPEN", "session": session_code, "route": route, "channelId": ch_id},
            channel_id=ch_id,
            priority="high"
        )
        # 2. Send Global (English copy)
        send_fcm_message(
            messaging_client=messaging_client,
            topic="global_traders",
            title=gl_title,
            body=gl_body,
            data={"type": "SESSION_OPEN", "session": session_code, "route": route, "channelId": ch_id},
            channel_id=ch_id,
            priority="high"
        )
        # 3. Legacy broadcast topic
        send_fcm_message(
            messaging_client=messaging_client,
            topic="daily_briefing",
            title=gl_title,
            body=gl_body,
            data={"type": "SESSION_OPEN", "session": session_code, "route": route, "channelId": ch_id},
            channel_id=ch_id,
            priority="normal"
        )

        record_sent(
            dedup_key,
            {
                "sent_at": now_utc.isoformat(),
                "session": session_code,
                "date": date_str,
                "high_impact_count": red_count
            },
            local_history,
            db_client
        )
        logger.info(f"✓ Dispatched {session_code} Session Open alert ({gl_title})")
        return 1

    # ═════════════════════════════════════════════════════════════════════════
    # 1. TOKYO (ASIAN) SESSION OPEN (09:00 JST / 00:00 UTC / 05:30 AM IST) - Mon to Fri
    # ═════════════════════════════════════════════════════════════════════════
    if now_tokyo.weekday() in (0, 1, 2, 3, 4) and now_tokyo.hour == 9:
        dedup_key = f"session_tokyo_{date_str}"
        tokyo_in_titles = [
            "🇯🇵 Tokyo Market Open: Asian Session Shuru",
            "🇯🇵 Tokyo Session Live: USD/JPY & Asian Pairs Active",
            "🇯🇵 Asian Market Open: Tokyo Trading Session Shuru"
        ]
        tokyo_in_bodies = [
            "Tokyo market open ho chuka hai (09:00 JST). USD/JPY, AUD/USD aur JPY pairs ka live status check karo.",
            "Asian session live hai. Live Currency Heatmap par dominant pairs aur session rankings track karo.",
            f"Tokyo session open hai. Aaj {red_count} high-impact economic releases scheduled hain. Calendar check karo." if red_count > 0 else "Tokyo session live hai. Live market radar par currency strength aur rates check karo."
        ]
        tokyo_gl_titles = [
            "🇯🇵 Tokyo Market Open: Asian Session is Now Live",
            "🇯🇵 Tokyo Session Open: USD/JPY & Asian Crosses Active",
            "🇯🇵 Asian Market Open: Tokyo Trading Active"
        ]
        tokyo_gl_bodies = [
            "The Tokyo trading session is now active (09:00 JST). Primary pairs in focus: USD/JPY, AUD/USD, and JPY crosses.",
            "Asian markets are trading. Monitor live currency strength and opening session momentum on the Live Heatmap.",
            f"Tokyo session is open. {red_count} high-impact releases scheduled today. Review the economic calendar." if red_count > 0 else "Tokyo session is open. Track active currency strength rankings and live forex rates."
        ]
        idx = day_of_year % len(tokyo_in_titles)
        dispatched += dispatch_session_notification(
            session_code="TOKYO",
            dedup_key=dedup_key,
            in_title=tokyo_in_titles[idx],
            in_body=tokyo_in_bodies[idx],
            gl_title=tokyo_gl_titles[idx],
            gl_body=tokyo_gl_bodies[idx],
            route="market"
        )

    # ═════════════════════════════════════════════════════════════════════════
    # 2. LONDON (EUROPEAN) SESSION OPEN (08:00 London Time: 08:00 UTC Winter / 07:00 UTC Summer) - Mon to Fri
    # ═════════════════════════════════════════════════════════════════════════
    if now_london.weekday() in (0, 1, 2, 3, 4) and now_london.hour == 8:
        dedup_key = f"session_london_{date_str}"
        london_in_titles = [
            "🇬🇧 London Market Open: European Session Shuru",
            "🇬🇧 London Session Live: EUR/USD & GBP/USD In Focus",
            "🇬🇧 European Market Open: London Trading Active"
        ]
        london_in_bodies = [
            "London trading session open ho chuka hai. EUR/USD, GBP/USD aur European crosses ka live status check karo.",
            "European session live hai. Live Currency Heatmap par currency strength aur session volume track karo.",
            f"London market open ho chuka hai. Aaj {red_count} high-impact economic events scheduled hain. Calendar dekho." if red_count > 0 else "London session open hai. European market status aur live currency rates check karo."
        ]
        london_gl_titles = [
            "🇬🇧 London Market Open: European Session is Now Live",
            "🇬🇧 London Session Open: EUR/USD & GBP/USD in Focus",
            "🇬🇧 European Market Open: London Trading is Live"
        ]
        london_gl_bodies = [
            "The London trading session is now active (08:00 London Time). Major pairs: EUR/USD, GBP/USD, EUR/GBP.",
            "European trading session is officially underway. Check the Live Heatmap for dynamic currency strength rankings.",
            f"London session is open. {red_count} Red-Folder economic releases scheduled today. Review upcoming releases." if red_count > 0 else "London session is active. Over 35% of global forex volume trades during European hours. Check live rates!"
        ]
        idx = day_of_year % len(london_in_titles)
        dispatched += dispatch_session_notification(
            session_code="LONDON",
            dedup_key=dedup_key,
            in_title=london_in_titles[idx],
            in_body=london_in_bodies[idx],
            gl_title=london_gl_titles[idx],
            gl_body=london_gl_bodies[idx],
            route="calendar" if red_count > 0 else "home"
        )

    # ═════════════════════════════════════════════════════════════════════════
    # 3. NEW YORK (US) SESSION OPEN (08:00 Eastern: 13:00 UTC Winter / 12:00 UTC Summer) - Mon to Fri
    # ═════════════════════════════════════════════════════════════════════════
    if now_ny.weekday() in (0, 1, 2, 3, 4) and now_ny.hour == 8:
        dedup_key = f"session_ny_{date_str}"
        us_red = [e for e in today_red if e.get("currency") == "USD"]
        us_titles = ", ".join(e.get("title", "") for e in us_red[:2]) if us_red else "US Economic News"

        ny_in_titles = [
            "🇺🇸 New York Market Open: US Session Shuru",
            "🇺🇸 New York Session Live: USD & Gold In Focus",
            "🇺🇸 US Market Open: New York Trading Active"
        ]
        ny_in_bodies = [
            f"New York session open ho chuka hai (08:00 EST). {us_titles} in focus. Live market status check karo." if us_red else "New York trading session open ho chuka hai (08:00 EST). USD, Gold (XAU/USD) aur major pairs ka status dekho.",
            "US trading session shuru ho chuka hai. Live Currency Heatmap par USD strength aur major crosses track karo.",
            "New York market open hai. US economic data releases aur Gold (XAU/USD) price action check karo."
        ]
        ny_gl_titles = [
            "🇺🇸 New York Market Open: US Session is Now Live",
            "🇺🇸 New York Session Open: USD & Gold in Focus",
            "🇺🇸 US Market Open: New York Trading is Live"
        ]
        ny_gl_bodies = [
            f"The New York trading session is now active (08:00 EST). {us_titles} in play today. Monitor live rates and releases." if us_red else "The New York trading session is now active (08:00 EST). Primary pairs: USD, Gold (XAU/USD), EUR/USD.",
            "US trading session is open. Active market participation underway across USD pairs and commodities. Check live status.",
            "New York session has begun. Check the Live Currency Heatmap for USD strength and breaking news updates."
        ]
        idx = day_of_year % len(ny_in_titles)
        dispatched += dispatch_session_notification(
            session_code="NEW_YORK",
            dedup_key=dedup_key,
            in_title=ny_in_titles[idx],
            in_body=ny_in_bodies[idx],
            gl_title=ny_gl_titles[idx],
            gl_body=ny_gl_bodies[idx],
            route="calendar" if us_red else "home"
        )

    # ═════════════════════════════════════════════════════════════════════════
    # 4. SYDNEY (PACIFIC) SESSION OPEN (08:00 Sydney Time: 21:00 UTC Summer / 22:00 UTC Winter)
    # ═════════════════════════════════════════════════════════════════════════
    # Sydney local time Monday-Friday mornings (includes Sunday evening UTC weekly market open)
    if now_sydney.weekday() in (0, 1, 2, 3, 4) and now_sydney.hour == 8:
        dedup_key = f"session_sydney_{now_sydney.strftime('%Y-%m-%d')}"
        sydney_in_titles = [
            "🇦🇺 Sydney Market Open: Pacific Session Shuru",
            "🇦🇺 Sydney Session Live: AUD & NZD In Focus",
            "🇦🇺 Pacific Market Open: Sydney Trading Active"
        ]
        sydney_in_bodies = [
            "Sydney trading session open ho chuka hai (08:00 Sydney Time). AUD/USD aur NZD/USD pairs ka live status check karo.",
            "Pacific trading session live hai. Live Currency Heatmap par early currency movements track karo.",
            "Sydney session shuru ho chuka hai. AUD, NZD aur Asian-Pacific crosses ka live status check karo."
        ]
        sydney_gl_titles = [
            "🇦🇺 Sydney Market Open: Pacific Session is Now Live",
            "🇦🇺 Sydney Session Open: AUD & NZD in Focus",
            "🇦🇺 Pacific Market Open: Sydney Trading is Live"
        ]
        sydney_gl_bodies = [
            "The Sydney trading session is now active (08:00 Sydney Time). Major pairs: AUD/USD, NZD/USD, and Pacific crosses.",
            "Pacific trading session is underway. Monitor opening market rates and currency rankings on the Live Heatmap.",
            "Sydney session has begun. Check early market momentum across AUD, NZD, and Pacific currencies."
        ]
        idx = day_of_year % len(sydney_in_titles)
        dispatched += dispatch_session_notification(
            session_code="SYDNEY",
            dedup_key=dedup_key,
            in_title=sydney_in_titles[idx],
            in_body=sydney_in_bodies[idx],
            gl_title=sydney_gl_titles[idx],
            gl_body=sydney_gl_bodies[idx],
            route="market"
        )

    return dispatched


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 4: Sunday "Week Ahead" Macro Push Digest (Full Week Titles)
# ─────────────────────────────────────────────────────────────────────────────
def check_sunday_macro_digest(events, now_utc, local_history, messaging_client, db_client):
    """
    Runs STRICTLY on Sunday (weekday == 6) between 14:00 and 19:59 UTC.
    Gathers all real high-impact (red) events for the entire upcoming week (Mon-Fri)
    and formats them with their exact day, currency, and titles.
    """
    logger.info("Checking Trigger 4: Sunday 'Week Ahead' Macro Digest...")
    # 6 = Sunday
    if now_utc.weekday() != 6:
        logger.debug("Today is not Sunday. Skipping Sunday Macro Digest.")
        return 0

    if not (14 <= now_utc.hour <= 19):
        logger.debug(f"Current UTC hour ({now_utc.hour}) is outside Sunday 14:00-19:59 window.")
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
            upcoming_red.append((e_time, e))

    upcoming_red.sort(key=lambda x: x[0])
    upcoming_count = len(upcoming_red)

    if upcoming_count > 0:
        push_title = f"📅 Week Ahead: {upcoming_count} High-Impact Catalysts"

        # Group titles by day of week (Mon, Tue, Wed, Thu, Fri)
        by_day = {}
        for e_time, e in upcoming_red:
            day_name = e_time.strftime("%a")  # e.g., "Mon", "Tue"
            curr = e.get("currency", "FOREX")
            title = e.get("title", "High-Impact Event").strip()
            item = f"{curr} {title}"
            if day_name not in by_day:
                by_day[day_name] = []
            if item not in by_day[day_name]:
                by_day[day_name].append(item)

        day_lines = []
        for day_name, items in by_day.items():
            day_lines.append(f"• {day_name}: {', '.join(items)}")

        schedule_block = "\n".join(day_lines)
        push_body = (
            f"🔴 High-Impact Releases This Week:\n"
            f"{schedule_block}\n\n"
            f"Tap to view full calendar & set alarms."
        )
    else:
        push_title = "📅 Week Ahead: Macro Watchlist"
        push_body = "Markets open soon. Review the upcoming week's economic calendar and prepare your key pip levels. Tap to open."

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
        priority="high"
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
        logger.info(f"✓ Sent Sunday 'Week Ahead' Digest for Week {week_num} ({upcoming_count} catalysts)")
        return 1

    return 0


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 5: Daily Morning High-Impact News Digest (With Time)
# ─────────────────────────────────────────────────────────────────────────────
def check_daily_morning_high_impact_digest(events, now_utc, local_history, messaging_client, db_client):
    """
    Runs in the morning between 01:00 and 03:59 UTC (06:30 to 09:29 AM IST).
    Checks if today has any Red (High-Impact) economic events.

    Guarantees:
    - If NO high-impact events exist today: skips entirely (Zero Fake, Zero Spam).
    - If high-impact events exist: sends a morning notification listing all today's
      high-impact news titles with their scheduled release times (in UTC and IST).
    - Deduplicated per calendar day: sent strictly ONCE per day.
    """
    logger.info("Checking Trigger 5: Daily Morning High-Impact Digest...")

    # Skip Sunday as Sunday has Trigger 4 (Week Ahead Macro Digest)
    if now_utc.weekday() == 6:
        logger.debug("Sunday detected. Handled by Sunday Macro Digest.")
        return 0

    # Active morning window: 01:00 to 03:59 UTC (06:30 to 09:29 AM IST)
    if not (1 <= now_utc.hour <= 3):
        logger.debug(f"Current UTC hour ({now_utc.hour}) is outside morning window (01:00-03:59 UTC).")
        return 0

    date_str = now_utc.strftime("%Y-%m-%d")
    dedup_key = f"daily_morning_red_{date_str}"

    if is_already_sent(dedup_key, local_history, db_client):
        logger.debug(f"Daily Morning Digest for {date_str} already sent.")
        return 0

    # Filter today's real high-impact events
    today_red = []
    for e in events:
        if str(e.get("impact", "")).lower() != "red":
            continue
        e_time = parse_iso_utc(e.get("time"))
        if e_time and e_time.strftime("%Y-%m-%d") == date_str:
            today_red.append((e_time, e))

    if not today_red:
        logger.info(f"No high-impact (red) events scheduled for today ({date_str}). Zero morning alert sent.")
        return 0

    today_red.sort(key=lambda x: x[0])
    count = len(today_red)

    # Format event lines with UTC and IST times
    lines = []
    for e_time, e in today_red:
        curr = e.get("currency", "FOREX")
        title = e.get("title", "High-Impact Event").strip()
        time_utc_str = e_time.strftime("%H:%M UTC")
        ist_time = e_time + timedelta(hours=5, minutes=30)
        time_ist_str = ist_time.strftime("%I:%M %p IST").lstrip("0")

        forecast = e.get("forecast", "").strip()
        fcst_str = f" [Fcst: {forecast}]" if forecast else ""
        lines.append(f"• {time_utc_str} ({time_ist_str}) — {curr}: {title}{fcst_str}")

    if count == 1:
        first_event = today_red[0][1]
        push_title = f"🔴 High-Impact Today: {first_event.get('currency')} {first_event.get('title')}"
    else:
        push_title = f"🔴 Today's High-Impact News: {count} Major Releases"

    event_list_block = "\n".join(lines)
    push_body = (
        f"Today's High-Impact Schedule:\n"
        f"{event_list_block}\n\n"
        f"Tap for live countdowns, forecasts & AI analysis."
    )

    data_payload = {
        "type": "DAILY_BRIEFING",
        "subType": "HIGH_IMPACT_DIGEST",
        "date": date_str,
        "count": str(count),
        "route": "calendar",
        "channelId": "fcm_daily_briefing_channel"
    }

    success = send_fcm_message(
        messaging_client=messaging_client,
        topic="daily_briefing",
        title=push_title,
        body=push_body,
        data=data_payload,
        channel_id="fcm_daily_briefing_channel",
        priority="high"
    )

    if success:
        record_sent(
            dedup_key,
            {
                "sent_at": now_utc.isoformat(),
                "date": date_str,
                "high_impact_count": count,
                "type": "DAILY_MORNING_HIGH_IMPACT_DIGEST"
            },
            local_history,
            db_client
        )
        logger.info(f"✓ Sent Daily Morning High-Impact Digest for {date_str} ({count} events)")
        return 1

    return 0


def check_telegram_community_alerts(now_utc, local_history, messaging_client, db_client):
    """
    Dispatches 2 daily English notifications (Morning 10:00 AM IST & Evening 07:00 PM IST windows)
    inviting users to join the Forex News Telegram community (https://t.me/ForexBrief),
    strictly deduplicated once per window per calendar day.
    """
    logger.info("Checking Trigger 7: Daily 2x Telegram Community Alerts...")
    dispatched = 0

    tz_ist = zoneinfo.ZoneInfo("Asia/Kolkata")
    now_ist = now_utc.astimezone(tz_ist)
    ist_hour = now_ist.hour
    date_str = now_ist.strftime("%Y-%m-%d")

    slots = [
        {
            "slot_id": "morning",
            "hours": (10, 11),
            "title": "Join the Forex News Community",
            "body": "Connect with traders on our official Forex News Telegram channel. Tap to join free!"
        },
        {
            "slot_id": "evening",
            "hours": (19, 20),
            "title": "Stay Connected on Telegram",
            "body": "Be part of the official Forex News Telegram community with fellow traders. Tap to join!"
        }
    ]

    channel_url = "https://t.me/ForexBrief"
    ch_id = "fcm_daily_briefing_channel"

    for slot in slots:
        if ist_hour not in slot["hours"]:
            continue

        dedup_key = f"telegram_forexbrief_{slot['slot_id']}_{date_str}"
        if is_already_sent(dedup_key, local_history, db_client):
            logger.debug(f"Telegram community {slot['slot_id']} alert already sent for {date_str}.")
            continue

        payload_data = {
            "type": "COMMUNITY_TELEGRAM",
            "route": channel_url,
            "url": channel_url,
            "channelId": ch_id
        }

        s1 = send_fcm_message(
            messaging_client=messaging_client,
            topic="india_traders",
            title=slot["title"],
            body=slot["body"],
            data=payload_data,
            channel_id=ch_id,
            priority="high"
        )
        s2 = send_fcm_message(
            messaging_client=messaging_client,
            topic="global_traders",
            title=slot["title"],
            body=slot["body"],
            data=payload_data,
            channel_id=ch_id,
            priority="high"
        )

        if s1 or s2:
            record_sent(
                dedup_key,
                {
                    "sent_at": now_utc.isoformat(),
                    "slot": slot["slot_id"],
                    "date": date_str,
                    "channel": channel_url,
                    "type": "COMMUNITY_TELEGRAM"
                },
                local_history,
                db_client
            )
            logger.info(f"✓ Dispatched Telegram Community {slot['slot_id']} alert for {date_str}")
            dispatched += 1

    return dispatched


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

    # 4. Sunday Macro Digest (Sundays only, full week ahead high-impact titles)
    total_dispatched += check_sunday_macro_digest(events, now_utc, local_history, messaging_client, db_client)

    # 5. Daily Morning High-Impact Digest (Mon-Fri morning, only if red events exist today, with time)
    total_dispatched += check_daily_morning_high_impact_digest(events, now_utc, local_history, messaging_client, db_client)

    # 6. Automated 2-Hour Retention, Memes & Special Calendar Hooks (India vs Global)
    logger.info("Checking Trigger 6: Automated 2-Hour Retention & Memes...")
    try:
        from retention_campaigns import check_retention_campaign_dispatch
        retention_count = check_retention_campaign_dispatch(
            now_utc=now_utc,
            local_history=local_history,
            messaging_client=messaging_client,
            db_client=db_client,
            send_message_fn=send_fcm_message,
            record_sent_fn=record_sent,
            is_sent_fn=is_already_sent
        )
        total_dispatched += retention_count
        logger.info(f"Trigger 6 completed: {retention_count} retention notification(s) dispatched.")
    except Exception as e:
        logger.error(f"Error in Retention Campaign Dispatcher: {e}")

    # 7. Daily 2x Telegram Community Alerts (Morning & Evening)
    total_dispatched += check_telegram_community_alerts(now_utc, local_history, messaging_client, db_client)

    logger.info(f"Cycle completed. Total notifications dispatched: {total_dispatched}")
    return total_dispatched


if __name__ == "__main__":
    test_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if test_arg in ("--force-retention", "-r", "retention"):
        # Force dispatch current retention slot ignoring deduplication for instant test
        logger.info("Manual flag triggered: Running Retention Campaign directly...")
        from retention_campaigns import check_retention_campaign_dispatch
        now_utc = datetime.now(timezone.utc)
        messaging_client, db_client = init_firebase_admin()
        local_history = load_dedup_history()
        
        # Override is_sent_fn to return False so it forcefully sends
        check_retention_campaign_dispatch(
            now_utc=now_utc,
            local_history={},
            messaging_client=messaging_client,
            db_client=db_client,
            send_message_fn=send_fcm_message,
            record_sent_fn=record_sent,
            is_sent_fn=lambda k, h, db: False
        )
    else:
        run_push_dispatcher(test_arg)
