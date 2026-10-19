#!/usr/bin/env python3
"""
Automated Retention, Savage Memes & Festival Push Notification Engine
====================================================================
Sourced strictly from notification.txt & HIGH_RETENTION_PUSH_NOTIFICATIONS.txt.

Architecture & Targeting:
- 🇮🇳 India Traders: Dispatches witty, relatable Hinglish to topic 'india_traders'
- 🌍 Global Traders: Dispatches crisp, savage Universal English to topic 'global_traders'
- ⏰ 2-Hour Weekday Interval Schedule (Mon-Fri 08:00 AM - 12:00 AM Midnight IST)
- 🏖️ Special Weekend Schedule (Sat & Sun: Journal, Psychology, Crypto, Re-open)
- 🎆 Festivals & Special Dates with Strict Start/Stop Dates & TTL
- 🛡️ Zero-Spam Deduplication: Each slot is sent at most once per calendar day.
- 🌙 Silent DND Night Window (12:00 AM to 08:00 AM IST) - Zero notifications sent.
"""

from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger("RetentionEngine")

# Notification Channels matching FcmManager.kt
CHANNEL_DAILY_BRIEFING = "fcm_daily_briefing_channel"
CHANNEL_BREAKING_NEWS = "fcm_breaking_news_channel"
CHANNEL_CALENDAR_ALERTS = "fcm_calendar_alerts_channel"

# Regional Topics matching FcmManager.kt
TOPIC_INDIA = "india_traders"
TOPIC_GLOBAL = "global_traders"


# ─────────────────────────────────────────────────────────────────────────────
# 1. 2-HOUR INTERVAL WEEKDAY SLOTS (MON - FRI)
# ─────────────────────────────────────────────────────────────────────────────
WEEKDAY_2HOUR_SLOTS = [
    {
        "slot_id": "slot_08am",
        "ist_hour": 8,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "Asian market ka move dekha? 🇯🇵⚡",
                    "body": "Tokyo session close hone ko hai. Europe session se pehle currency bias check kar lo!",
                    "route": "market"
                },
                "global": {
                    "title": "Asian markets made their move 🇯🇵⚡",
                    "body": "Tokyo session just wrapped. See the dominant currency momentum before Europe opens!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Chai peeli? Par trade ka kya? ☕📉",
                    "body": "London session shuru hone wala hai. GBP/USD aur Gold me heavy movement track karo!",
                    "route": "home"
                },
                "global": {
                    "title": "Coffee first, or pips first? ☕📈",
                    "body": "London session is gearing up. EUR/USD and GBP/USD volatility is picking up fast!",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "slot_10am",
        "ist_hour": 10,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "Insta scroll karne se pips nahi aate 📱💸",
                    "body": "London traders active ho rahe hain. GBP aur EUR pairs me order blocks ban rahe hain!",
                    "route": "home"
                },
                "global": {
                    "title": "Scrolling won't grow your account 📱💸",
                    "body": "London traders are waking up. Major order blocks forming on GBP and EUR pairs!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Charts jhooth bolte hain, macro data nahi 📊⚡",
                    "body": "Institutions fundamentals par trade karte hain. Aaj ka AI Macro Sentiment check karo!",
                    "route": "home"
                },
                "global": {
                    "title": "Charts lie. Macro data doesn't. 📊⚡",
                    "body": "Institutions trade fundamentals, not retail patterns. Check today's AI Macro Sentiment.",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "slot_12pm",
        "ist_hour": 12,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "London session open hone me 30 min! 🔔🇬🇧",
                    "body": "Market me heavy liquidity aane wali hai. EUR/USD aur GBP/USD ke breakout levels dekh lo!",
                    "route": "home"
                },
                "global": {
                    "title": "London Open in 30 mins! 🔔🇬🇧",
                    "body": "Heavy liquidity influx incoming. Check EUR/USD & GBP/USD key breakout levels!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Khana order karne aaye the? 🍕📈",
                    "body": "Bhook pet me nahi, pips ki honi chahiye! London breakout 60 pips bhaag chuka hai.",
                    "route": "home"
                },
                "global": {
                    "title": "Opening Uber Eats or opening charts? 🍕📈",
                    "body": "Hungry for pips? London session breakout just moved 60 pips in 20 minutes!",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "slot_02pm",
        "ist_hour": 14,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "Whales kahan buy kar rahi hain? 🐋📊",
                    "body": "AI Quant ne institutional buying detect ki hai. Weekly VIP pass sirf ₹99 se unlock karo!",
                    "route": "premium?reason=ai_verdict"
                },
                "global": {
                    "title": "Where are the hedge funds buying? 🐋📊",
                    "body": "Institutional volume spike detected by AI Quant. Unlock order flow with 3-Day Free Trial!",
                    "route": "premium?reason=ai_verdict"
                }
            },
            {
                "india": {
                    "title": "Dhokha toh har koi deta hai... 🥀",
                    "body": "Par hamara AI Quant Verdict kabhi jhooth nahi bolta! Check institutional bias before trading.",
                    "route": "premium?reason=ai_verdict"
                },
                "global": {
                    "title": "People lie. Candlesticks don't. 🥀",
                    "body": "Stop trading on gut feeling. AI Quant algorithms scan 500+ institutional sources in ms.",
                    "route": "premium?reason=ai_quant"
                }
            },
            {
                "india": {
                    "title": "'Bhai, market yahan se pakka reverse hoga!' 🤡",
                    "body": "Ye bolke kitne account uda chuke ho? Stop guessing, check hedge-fund retail sentiment data!",
                    "route": "news_feed"
                },
                "global": {
                    "title": "'Trust me bro, it has to reverse here!' 🤡",
                    "body": "How many accounts have been blown on that exact thought? Check live macro data first.",
                    "route": "news_feed"
                }
            }
        ]
    },
    {
        "slot_id": "slot_04pm",
        "ist_hour": 16,
        "channel_id": CHANNEL_CALENDAR_ALERTS,
        "pool": [
            {
                "india": {
                    "title": "Overleveraging se account blow ho jayega 🧮⚠️",
                    "body": "New York session se pehle risk calculate karo. 1-Tap Lot Size Calculator use karo!",
                    "route": "tools"
                },
                "global": {
                    "title": "Wrong lot size will blow your account 🧮⚠️",
                    "body": "Pre-US news volatility can wipe out accounts in seconds. Calculate your pip risk now!",
                    "route": "tools"
                }
            },
            {
                "india": {
                    "title": "Chai-sutta ka kharcha nikal gaya? ☕🚬",
                    "body": "Ya wo bhi market sweep kar gaya? Blind trade mat lo, PRO AI Verdict check karo!",
                    "route": "premium?reason=ai_verdict"
                },
                "global": {
                    "title": "Did you just donate your coffee money? ☕💸",
                    "body": "Market swept your premature entry? Check the economic calendar before clicking buy.",
                    "route": "calendar"
                }
            }
        ]
    },
    {
        "slot_id": "slot_06pm",
        "ist_hour": 18,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "Stop Loss lagaya tha ya bhool gaye? 💀🇺🇸",
                    "body": "New York session open + US Red-Folder news aane wali hai. SL check karo turant!",
                    "route": "calendar"
                },
                "global": {
                    "title": "Did you set your Stop Loss? 💀🇺🇸",
                    "body": "New York session opening now + Red-Folder US economic data dropping. Protect your capital!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "'We need to talk...' 💀🥀",
                    "body": "Ex ke is text se bhi zyada khatarnak Jerome Powell ki speech hai aaj! Protect your positions.",
                    "route": "calendar"
                },
                "global": {
                    "title": "'We need to talk...' 💀🥀",
                    "body": "Scarier than a text from your ex: Powell about to speak during high-impact US session!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "Usne ghost kar diya? 👻💔",
                    "body": "At least Gold ka 100-pip spike ghost nahi karega! Real-time economic forecast abhi dekho.",
                    "route": "home"
                },
                "global": {
                    "title": "She ghosted you? 👻💔",
                    "body": "At least today's 100-pip breakout won't ghost you! Check real-time volatility radar now.",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "slot_08pm",
        "ist_hour": 20,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "⚡ Market ka sabse bada move abhi ho raha hai!",
                    "body": "London aur New York dono open hain. Gold aur USD me massive volatility chal rahi hai!",
                    "route": "home"
                },
                "global": {
                    "title": "⚡ Overlap Frenzy: 100+ pip swings live!",
                    "body": "London & New York are both trading right now. Gold (XAU/USD) & US Dollar are exploding!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Kat gaya na? 💔✂️",
                    "body": "Dil bhi aur Stop Loss bhi! Revenge trading mat kar, pehle AI News Impact analysis padh le.",
                    "route": "home"
                },
                "global": {
                    "title": "Stop Loss got caught again? 💔✂️",
                    "body": "Revenge trading won't fix it. Check the AI Quant post-news verdict before your next trade.",
                    "route": "premium?reason=ai_verdict"
                }
            },
            {
                "india": {
                    "title": "Ex ki shaadi ki photo dekh li? 💍😭",
                    "body": "Revenge lene ka best tareeqa: Green PnL screenshot. Chart pe dhyan do, story par nahi!",
                    "route": "home"
                },
                "global": {
                    "title": "Saw your ex's wedding announcement? 💍😭",
                    "body": "Best revenge in life: A consistent green P&L. Focus on your charts, not on Instagram!",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "slot_10pm",
        "ist_hour": 22,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "Aaj kitna profit ya loss hua? 📓✏️",
                    "body": "Bina journal banaye trader nahi banoge! Aaj ke wins aur mistakes journal me add karo.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "How did you trade today? 📓✏️",
                    "body": "Don't sleep without logging today's trades. Top traders audit their journal every night!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Crying over a 2-word text? 🥺📱",
                    "body": "Ro mat mere bhai, USD/JPY ka green breakout dekh kar aansu sukh jayenge. Tap to see VIP analysis!",
                    "route": "premium?reason=ai_verdict"
                },
                "global": {
                    "title": "Crying over a 2-word text message? 🥺📱",
                    "body": "Dry your tears. Look at the USD/JPY 4-hour trend instead. Much cleaner structure!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Blue tick aaya par reply nahi? ⏱️🔵",
                    "body": "Ignore hone ki aadat daal lo, ya fir Trade Journal me apni mistakes analyze karo. Tap to journal!",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Seen at 11:42 PM with no reply? ⏱️🔵",
                    "body": "Get used to it, or audit your trade setup in the Trade Journal. Tap to review your day!",
                    "route": "trade_journal"
                }
            }
        ]
    },
    {
        "slot_id": "slot_12am",
        "ist_hour": 0, # Midnight
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "Raat ke 12 baje bhi trade open hai? 🌙🕯️",
                    "body": "Daily candle close ho chuki hai! Open trades me Stop Loss lock karo ya profit book karke so jao.",
                    "route": "home"
                },
                "global": {
                    "title": "Late-night trading? Don't leave trades unhedged 🌙🕯️",
                    "body": "Daily candle close is in! Protect open trades from overnight swap rates or secure your profits.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Mummy: 'Mera beta raat bhar padhta hai' 📚🥺",
                    "body": "Beta raat ke 1 baje Gold ke 1-minute chart par drawdown ginke ro raha hai. Take a break bhai!",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Mom: 'He works so hard late at night' 📚🥺",
                    "body": "You staring at a 1-minute Gold chart calculating drawdown at midnight: Take a break!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Raat ke 2:30 baje overthinking? 🌙🦉",
                    "body": "Neend waise bhi nahi aa rahi, toh Asian session ka pre-market setup dekh lo!",
                    "route": "home"
                },
                "global": {
                    "title": "Overthinking at 2:30 AM? 🌙🦉",
                    "body": "Can't sleep anyway? Check the Asian session pre-market setups. Much more thrilling than doom-scrolling!",
                    "route": "home"
                }
            }
        ]
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. SPECIAL WEEKEND SLOTS (SATURDAY & SUNDAY - ZERO LIVE ALERT SPAM)
# ─────────────────────────────────────────────────────────────────────────────
SATURDAY_SLOTS = [
    {
        "slot_id": "sat_1130am",
        "ist_hour": 11,
        "ist_minute_min": 0,
        "ist_minute_max": 59,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "india": {
            "title": "Is hafte ka hisab-kitab kya raha? 📓🏆",
            "body": "Forex market band hai! Apne is hafte ke trades ka analysis karo Trade Journal me.",
            "route": "trade_journal"
        },
        "global": {
            "title": "Did you beat the market this week? 📓🏆",
            "body": "Week is closed! Review your wins, cut recurring mistakes, and analyze your win-rate in Trade Journal.",
            "route": "trade_journal"
        }
    },
    {
        "slot_id": "sat_0330pm",
        "ist_hour": 15,
        "ist_minute_min": 0,
        "ist_minute_max": 59,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "india": {
            "title": "90% traders ye galti karke fail hote hain... 🧠💡",
            "body": "Revenge trading se bachna hai? Home screen widget lagao aur bina screen dekhe disciplined raho!",
            "route": "widget"
        },
        "global": {
            "title": "90% of traders fail right here... 🧠💡",
            "body": "Revenge trading and lack of discipline blow more accounts than bad indicators. Read today's guide.",
            "route": "widget"
        }
    },
    {
        "slot_id": "sat_0730pm",
        "ist_hour": 19,
        "ist_minute_min": 0,
        "ist_minute_max": 59,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "india": {
            "title": "Forex band hai, par Crypto live hai! 🪙🔥",
            "body": "Weekend me Bitcoin & Ethereum charts par action shuru hai. PRO subscription sirf ₹99 se start karo!",
            "route": "premium?reason=weekend_crypto"
        },
        "global": {
            "title": "Forex sleeps, Crypto doesn't 🪙🔥",
            "body": "Bitcoin & Ethereum moving while Forex is closed! Unlock Weekly PRO for AI sentiment insights.",
            "route": "premium?reason=weekend_crypto"
        }
    }
]

SUNDAY_SLOTS = [
    {
        "slot_id": "sun_1200pm",
        "ist_hour": 12,
        "ist_minute_min": 0,
        "ist_minute_max": 59,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "india": {
            "title": "🗓️ Agle hafte ka economic calendar ready hai!",
            "body": "Fed interest rate aur US inflation news aane wali hai. Poore hafte ki high-impact list check karo!",
            "route": "calendar"
        },
        "global": {
            "title": "🗓️ Next Week's Economic Minefield is Ready!",
            "body": "Fed Interest Rate decision, US CPI & ECB rate meet scheduled this week. See dates & forecasts!",
            "route": "calendar"
        }
    },
    {
        "slot_id": "sun_0500pm",
        "ist_hour": 17,
        "ist_minute_min": 0,
        "ist_minute_max": 59,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "india": {
            "title": "Sunday night market gap up ya gap down? 📊⚠️",
            "body": "Weekend ki major news se Gold aur USD me bada gap expected hai. AI Macro Bias check karo!",
            "route": "home"
        },
        "global": {
            "title": "Sunday Market Opening Gaps incoming? 📊⚠️",
            "body": "Geopolitical developments over the weekend may cause big opening gaps on Gold & USD. See AI bias!",
            "route": "home"
        }
    },
    {
        "slot_id": "sun_0930pm",
        "ist_hour": 21,
        "ist_minute_min": 0,
        "ist_minute_max": 59,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "india": {
            "title": "🚨 Forex market khul chuka hai! 🌏📈",
            "body": "Sydney aur Tokyo session shuru ho gaya hai. Naye week ke pehle moves track karo abhi!",
            "route": "home"
        },
        "global": {
            "title": "🚨 The Forex Markets are OPEN! 🌏📈",
            "body": "Sydney & Tokyo trading sessions have kicked off. New trading week is live—catch the opening moves!",
            "route": "home"
        }
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# 3. FESTIVAL & SPECIAL CALENDAR HOOKS (STRICT ACTIVE WINDOWS & STOP DATES)
# ─────────────────────────────────────────────────────────────────────────────
def is_valentine_window(now_ist):
    # Feb 13 to Feb 14 only. Stop strictly after Feb 14 midnight.
    return now_ist.month == 2 and now_ist.day in (13, 14)

def is_new_year_window(now_ist):
    # Dec 31 to Jan 3 only. Stop strictly on Jan 4.
    return (now_ist.month == 12 and now_ist.day == 31) or (now_ist.month == 1 and now_ist.day in (1, 2, 3))

def is_payday_window(now_ist):
    # 1st, 2nd, 3rd of month (Payday salary credit hours: 11:00 AM IST)
    return now_ist.day in (1, 2, 3) and now_ist.hour == 11

def is_month_end_window(now_ist):
    # 25th - 30th of month (Month-end struggle hours: 08:00 PM IST)
    return now_ist.day in (25, 26, 27, 28, 29, 30) and now_ist.hour == 20

def is_halloween_window(now_ist):
    # Oct 30 & 31 only. Stop strictly on Nov 1.
    return now_ist.month == 10 and now_ist.day in (30, 31)

def is_christmas_window(now_ist):
    # Dec 24, 25, 26 only.
    return now_ist.month == 12 and now_ist.day in (24, 25, 26)

def get_special_calendar_hook(now_ist):
    """
    Evaluates current IST time against strict calendar festival/special date windows.
    Returns hook dictionary if an active event matches, else None.
    """
    # 1. Payday (1st - 3rd of month, 11:00 AM IST)
    if is_payday_window(now_ist):
        return {
            "key": f"payday_{now_ist.strftime('%Y_%m')}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "Salary credited: 10:00 AM 🤑 | Balance: 10:30 AM 😭",
                "body": "Mahine ki mehnat ko 30 minute me market ko daan mat do bhai! Risk calculator use karo.",
                "route": "tools"
            },
            "global": {
                "title": "Paycheck lifespan: 48 hours? 💸📉",
                "body": "Don't blow your hard-earned paycheck on revenge trading. Calculate your risk before clicking buy!",
                "route": "tools"
            }
        }

    # 2. Month-End Maggi Days (25th - 30th of month, 08:00 PM IST)
    if is_month_end_window(now_ist):
        return {
            "key": f"monthend_{now_ist.strftime('%Y_%m')}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "1st ko Biryani, 25th ko Maggi? 🍲🍜",
                "body": "Life me consistency chahiye toh emotional revenge trading chhod do. Journal today's trades!",
                "route": "trade_journal"
            },
            "global": {
                "title": "Steak at start of month, Ramen by the 25th? 🍜🥩",
                "body": "Lack of consistency kills accounts. Audit your trading habits in the Trade Journal tonight!",
                "route": "trade_journal"
            }
        }

    # 3. Valentine's Day (Feb 13 - 14)
    if is_valentine_window(now_ist) and now_ist.hour in (13, 20):
        return {
            "key": f"val_{now_ist.year}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "Valentine pe single ho? 🌹🚫",
                "body": "Teddy bear aur phoolon ke paise bach gaye! Ab 3-Day Free Trial leke chart study karo.",
                "route": "premium?reason=valentine_single"
            },
            "global": {
                "title": "Single this Valentine's Day? 🌹🚫",
                "body": "Saved money on overpriced roses! Invest in your trading discipline with 3-Day Free Trial instead.",
                "route": "premium?reason=valentine_single"
            }
        }

    # 4. New Year Resolution (Dec 31 - Jan 3)
    if is_new_year_window(now_ist) and now_ist.hour in (10, 18):
        return {
            "key": f"newyear_{now_ist.year}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "31st Dec: 'Is saal disciplined rahunga' 🥂",
                "body": "2nd Jan: 100x leverage pe revenge buy! Check economic calendar before blowing another account.",
                "route": "calendar"
            },
            "global": {
                "title": "Jan 1st: 'I will strictly follow my rules' 🥂",
                "body": "Jan 3rd: 100x revenge trade into red news! Stay disciplined, check the economic calendar first.",
                "route": "calendar"
            }
        }

    # 5. Halloween (Oct 30 - 31)
    if is_halloween_window(now_ist) and now_ist.hour in (12, 19):
        return {
            "key": f"halloween_{now_ist.year}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "Bhoot se darr nahi lagta, red candle se lagta hai 🎃👻",
                "body": "Halloween par market fakeouts se bacho. AI Quant Verdict check karke trade plan banao!",
                "route": "premium?reason=halloween"
            },
            "global": {
                "title": "Horror movies aren't scary. Red candles are. 🎃👻",
                "body": "Halloween volatility is live. Don't let market makers ghost your account—set your Stop Loss!",
                "route": "home"
            }
        }

    # 6. Christmas / Holiday Thin Liquidity (Dec 24 - 26)
    if is_christmas_window(now_ist) and now_ist.hour in (11, 16):
        return {
            "key": f"christmas_{now_ist.year}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "Holiday season: Market me liquidity thin hai 🎄❄️",
                "body": "Spreads wide ho sakte hain! Aggressive trades lene se bacho aur Journal audit karo.",
                "route": "trade_journal"
            },
            "global": {
                "title": "Holiday Season: Thin liquidity warning! 🎄❄️",
                "body": "Banks are on vacation and spreads are wide. Protect your capital and avoid retail traps.",
                "route": "trade_journal"
            }
        }

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. MASTER RETENTION DISPATCH LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def check_retention_campaign_dispatch(now_utc, local_history, messaging_client, db_client, send_message_fn, record_sent_fn, is_sent_fn):
    """
    Main retention dispatcher called every 5 minutes from fcm_push_dispatcher.py.
    
    Guarantees:
    - Silent DND hours (12:00 AM to 08:00 AM IST) are strictly protected.
    - Sends Hinglish to 'india_traders' and Universal English to 'global_traders'.
    - Deduplicated strictly per slot per calendar day.
    """
    # Convert UTC to IST (+5:30)
    now_ist = now_utc + timedelta(hours=5, minutes=30)
    ist_hour = now_ist.hour
    ist_minute = now_ist.minute
    date_str = now_ist.strftime("%Y-%m-%d")
    weekday = now_ist.weekday() # 0 = Monday, ..., 5 = Saturday, 6 = Sunday

    # DND Window: 12:30 AM to 07:59 AM IST (Do not send marketing alerts while users sleep)
    if 1 <= ist_hour < 8:
        logger.debug(f"Current IST time ({now_ist.strftime('%H:%M')}) is in silent night DND. Skipping retention.")
        return 0

    dispatched = 0

    # ── CHECK 1: SPECIAL FESTIVAL / CALENDAR DATE HOOKS ──
    special_hook = get_special_calendar_hook(now_ist)
    if special_hook:
        hook_key = special_hook["key"]
        dedup_key = f"retention_special_{hook_key}_{date_str}_{ist_hour}"
        if not is_sent_fn(dedup_key, local_history, db_client):
            ch_id = special_hook.get("channel_id", CHANNEL_DAILY_BRIEFING)
            
            # Send India
            in_item = special_hook["india"]
            send_message_fn(
                messaging_client=messaging_client,
                topic=TOPIC_INDIA,
                title=in_item["title"],
                body=in_item["body"],
                data={"type": "RETENTION_MARKETING", "route": in_item["route"], "channelId": ch_id},
                channel_id=ch_id,
                priority="high"
            )

            # Send Global
            gl_item = special_hook["global"]
            send_message_fn(
                messaging_client=messaging_client,
                topic=TOPIC_GLOBAL,
                title=gl_item["title"],
                body=gl_item["body"],
                data={"type": "RETENTION_MARKETING", "route": gl_item["route"], "channelId": ch_id},
                channel_id=ch_id,
                priority="high"
            )

            record_sent_fn(
                dedup_key,
                {"sent_at": now_utc.isoformat(), "slot": hook_key, "date": date_str, "type": "SPECIAL_FESTIVAL_HOOK"},
                local_history,
                db_client
            )
            logger.info(f"✓ Dispatched Special Calendar Hook: {hook_key}")
            dispatched += 1
            return dispatched

    # ── CHECK 2: WEEKENDS (SATURDAY & SUNDAY) ──
    if weekday == 5: # Saturday
        for slot in SATURDAY_SLOTS:
            slot_h = slot["ist_hour"]
            # Active window: allows trigger anytime within a 3-hour window from slot start
            if slot_h <= ist_hour < slot_h + 3:
                dedup_key = f"retention_sat_{slot['slot_id']}_{date_str}"
                if is_sent_fn(dedup_key, local_history, db_client):
                    continue

                ch_id = CHANNEL_BREAKING_NEWS
                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_INDIA,
                    title=slot["india"]["title"],
                    body=slot["india"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": slot["india"]["route"], "channelId": ch_id},
                    channel_id=ch_id,
                    priority="high"
                )
                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_GLOBAL,
                    title=slot["global"]["title"],
                    body=slot["global"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": slot["global"]["route"], "channelId": ch_id},
                    channel_id=ch_id,
                    priority="high"
                )

                record_sent_fn(
                    dedup_key,
                    {"sent_at": now_utc.isoformat(), "slot": slot["slot_id"], "date": date_str, "type": "SATURDAY_RETENTION"},
                    local_history,
                    db_client
                )
                logger.info(f"✓ Dispatched Saturday Retention Slot: {slot['slot_id']}")
                dispatched += 1

        return dispatched

    elif weekday == 6: # Sunday
        for slot in SUNDAY_SLOTS:
            slot_h = slot["ist_hour"]
            # Active window: allows trigger anytime within a 3-hour window from slot start
            if slot_h <= ist_hour < slot_h + 3:
                dedup_key = f"retention_sun_{slot['slot_id']}_{date_str}"
                if is_sent_fn(dedup_key, local_history, db_client):
                    continue

                ch_id = CHANNEL_BREAKING_NEWS
                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_INDIA,
                    title=slot["india"]["title"],
                    body=slot["india"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": slot["india"]["route"], "channelId": ch_id},
                    channel_id=ch_id,
                    priority="high"
                )
                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_GLOBAL,
                    title=slot["global"]["title"],
                    body=slot["global"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": slot["global"]["route"], "channelId": ch_id},
                    channel_id=ch_id,
                    priority="high"
                )

                record_sent_fn(
                    dedup_key,
                    {"sent_at": now_utc.isoformat(), "slot": slot["slot_id"], "date": date_str, "type": "SUNDAY_RETENTION"},
                    local_history,
                    db_client
                )
                logger.info(f"✓ Dispatched Sunday Retention Slot: {slot['slot_id']}")
                dispatched += 1

        return dispatched

    # ── CHECK 3: WEEKDAY 2-HOUR INTERVAL SLOTS (MON - FRI) ──
    for slot in WEEKDAY_2HOUR_SLOTS:
        # Match slot's full 2-hour window (e.g. 16:00 to 17:59 IST for slot_04pm, 18:00 to 19:59 for slot_06pm)
        # Allows cron (which runs every 5 to 60 mins) to dispatch at ANY minute during the window without missing.
        # Deduplication key strictly prevents any double dispatch for the same day.
        slot_h = slot["ist_hour"]
        if slot_h <= ist_hour < slot_h + 2:
            dedup_key = f"retention_weekday_{slot['slot_id']}_{date_str}"
            if is_sent_fn(dedup_key, local_history, db_client):
                logger.debug(f"Retention slot {slot['slot_id']} already sent for {date_str}.")
                continue

            pool = slot["pool"]
            # Rotate daily based on day of year so message is never boring or repetitive
            day_of_year = now_ist.timetuple().tm_yday
            chosen = pool[day_of_year % len(pool)]

            ch_id = CHANNEL_BREAKING_NEWS

            # 1. Send India (Hinglish)
            send_message_fn(
                messaging_client=messaging_client,
                topic=TOPIC_INDIA,
                title=chosen["india"]["title"],
                body=chosen["india"]["body"],
                data={"type": "RETENTION_2HOUR", "route": chosen["india"]["route"], "channelId": ch_id},
                channel_id=ch_id,
                priority="high"
            )

            # 2. Send Global (Universal English)
            send_message_fn(
                messaging_client=messaging_client,
                topic=TOPIC_GLOBAL,
                title=chosen["global"]["title"],
                body=chosen["global"]["body"],
                data={"type": "RETENTION_2HOUR", "route": chosen["global"]["route"], "channelId": ch_id},
                channel_id=ch_id,
                priority="high"
            )

            record_sent_fn(
                dedup_key,
                {
                    "sent_at": now_utc.isoformat(),
                    "slot": slot["slot_id"],
                    "date": date_str,
                    "india_title": chosen["india"]["title"],
                    "global_title": chosen["global"]["title"],
                    "type": "WEEKDAY_2HOUR_RETENTION"
                },
                local_history,
                db_client
            )
            logger.info(f"✓ Dispatched Weekday 2-Hour Retention Slot: {slot['slot_id']} ({chosen['india']['title']})")
            dispatched += 1

    return dispatched
