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
            },
            {
                "india": {
                    "title": "Alarm baja par neend charts ne uda di? ⏰📈",
                    "body": "Good morning trader! Aaj 3 high-impact news catalysts queue me hain. Pehle calendar check karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "Woke up thinking about open trades? ⏰📈",
                    "body": "Morning! 3 high-impact Red-Folder catalysts are scheduled today. Check the forecast before London opens.",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "Chai & Chart setup ready? ☕📊",
                    "body": "Retail traders abhi so rahe hain, institutions orders bhar rahe hain. Aaj ka AI Bias dekho!",
                    "route": "home"
                },
                "global": {
                    "title": "Retail is asleep, Institutions are placing orders ☕📊",
                    "body": "Smart money is stacking order blocks before Frankfurt opens. Check today's AI Macro Sentiment!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Neend khulte hi portfolio laal dikha? 🔴☕",
                    "body": "Panic mat karo! London breakout session me trend reverse ho sakta hai. Key levels abhi check karo.",
                    "route": "home"
                },
                "global": {
                    "title": "Morning reality check: Red or Green? 🔴☕",
                    "body": "Don't panic trade. High-volatility European session is setting up fresh liquidity sweeps now.",
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
                    "title": "Scrolling TikTok won't grow your account 📱💸",
                    "body": "London traders are waking up. Major institutional order blocks forming on GBP and EUR pairs!",
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
            },
            {
                "india": {
                    "title": "Meme dekhna band karo, London setup dekho! 🤡📈",
                    "body": "Pre-London breakout 45 pips nikal chuka hai. Live Heatmap par strongest currency check karo!",
                    "route": "market"
                },
                "global": {
                    "title": "Put the memes down. London is moving! 🤡📈",
                    "body": "Pre-London breakout just moved 45 pips. Spot the strongest currency on the Live Heatmap!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Dost bol raha hai 'Crypto me daal de'? 🗣️📉",
                    "body": "Unverified tips se bacho. AI Quant Verdict scanning 500+ institutional sources for real signals.",
                    "route": "premium?reason=ai_verdict"
                },
                "global": {
                    "title": "Your buddy's 'guaranteed 100x signal'? 🗣️📉",
                    "body": "Stop trading on group-chat advice. AI Quant algorithms scan 500+ institutional sources in ms.",
                    "route": "premium?reason=ai_verdict"
                }
            },
            {
                "india": {
                    "title": "Aadha din nikal gaya, discipline kahan hai? ⏳🧭",
                    "body": "Overtrading mat karo. Sirf A+ quality setups trade karo. Economic calendar ka timer on karo!",
                    "route": "calendar"
                },
                "global": {
                    "title": "Half the day gone. Where's your edge? ⏳🧭",
                    "body": "Quality over quantity. Wait for A+ setups only. Check today's Red-Folder economic timer!",
                    "route": "calendar"
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
            },
            {
                "india": {
                    "title": "Swiggy se pehle pips deliver! 🍔⚡",
                    "body": "10 minute me burger aaye na aaye, market 50 pips zaroor de gaya! Stop loss check kiya?",
                    "route": "home"
                },
                "global": {
                    "title": "DoorDash won't deliver pips to your door 🍔⚡",
                    "body": "Lunchtime London surge just printed 50 pips. Did you secure your profits before the sweep?",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "1 pizza se bhi sasta hai VIP access 🍕💸",
                    "body": "Blind trade karke loss mat karo. AI Quant Verdict aur signals unlock karo sirf ₹99 me!",
                    "route": "premium?reason=smart_pricing"
                },
                "global": {
                    "title": "Cheaper than a single lunch: PRO Edge 🥗💡",
                    "body": "Stop donating $300 to institutional sweeps. Unlock AI Quant Verdicts with a 3-Day Free Trial!",
                    "route": "premium?reason=smart_pricing"
                }
            },
            {
                "india": {
                    "title": "Thali me biryani, chart pe breakdown? 🍛📉",
                    "body": "GBP/USD support tod chuka hai. Lunch se pehle trailing stop loss zaroor adjust kar lo!",
                    "route": "home"
                },
                "global": {
                    "title": "Eating lunch while your trades bleed? 🥪📉",
                    "body": "GBP/USD just sliced through support. Adjust your trailing stops before stepping away!",
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
                    "title": "'Trust me bro, it HAS to bounce here!' 🤡",
                    "body": "How many accounts have been blown on that exact thought? Check live macro data first.",
                    "route": "news_feed"
                }
            },
            {
                "india": {
                    "title": "Telegram 'guaranteed signals' par vishwas? 🚩💀",
                    "body": "99% signal channels fake hote hain. Real data dekho: AI Institutional Sentiment live hai!",
                    "route": "premium?reason=ai_verdict"
                },
                "global": {
                    "title": "Still trusting anonymous Telegram signals? 🚩💀",
                    "body": "Stop trading other people's gambles. Learn institutional order flow with verified macro data!",
                    "route": "premium?reason=ai_verdict"
                }
            },
            {
                "india": {
                    "title": "Retail traders trap hone wale hain! 🪤⚡",
                    "body": "Fake breakout detect hua hai EUR pairs par. Trap se bachna hai toh AI Verdict dekho!",
                    "route": "home"
                },
                "global": {
                    "title": "Retail liquidity trap forming right now! 🪤⚡",
                    "body": "Liquidity grab spotted on EUR pairs. Don't be the exit liquidity—check AI Bias now!",
                    "route": "home"
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
            },
            {
                "india": {
                    "title": "Emotional damage free me deliver ho raha hai? 📉🩸",
                    "body": "High-impact US session se pehle Lot Size Calculator open kiya tha? Tap to calculate risk!",
                    "route": "tools"
                },
                "global": {
                    "title": "Emotional damage delivered in 10 minutes? 📉🩸",
                    "body": "Trading 50x leverage on Red-Folder news? Use the 1-Tap Lot Size Calculator before you enter!",
                    "route": "tools"
                }
            },
            {
                "india": {
                    "title": "'Bhai trade le lu?' 🛑 Ruuk jao!",
                    "body": "Agle 30 minute me US initial jobless claims & data drop hone wala hai. Wait for the dust to settle!",
                    "route": "calendar"
                },
                "global": {
                    "title": "'Should I take this trade?' 🛑 Hold on!",
                    "body": "High-impact US economic data dropping in 30 mins. Never trade into the news spike blind!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "Margin call aane se pehle sambhal jao 🚨📊",
                    "body": "Agar drawdown 5% se zyada hai, toh hedging consider karo. AI Risk Manager check karo.",
                    "route": "home"
                },
                "global": {
                    "title": "Don't let a margin call end your week 🚨📊",
                    "body": "Over 5% drawdown on your prop account? Review your open exposures with AI Quant tools.",
                    "route": "home"
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
                    "body": "People disappear, but Gold's 100-pip CPI spike never flakes on you. Check live macro bias!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Wall Street ka dhol bajne wala hai! 🔔🇺🇸",
                    "body": "NYSE open hone me 10 minute! NASDAQ aur Dollar pairs me wild swings expect karo.",
                    "route": "home"
                },
                "global": {
                    "title": "Wall Street Opening Bell in 10 mins! 🔔🇺🇸",
                    "body": "Massive institutional order flow hitting NASDAQ, Dow & USD pairs right now. Ready?",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Revenge trade lene ja rahe ho? 🛑👊",
                    "body": "Market tumse badla nahi maang raha, tum galat entry le rahe ho! Take a deep breath & check news.",
                    "route": "home"
                },
                "global": {
                    "title": "Thinking about a revenge trade? 🛑👊",
                    "body": "The market has no feelings. Revenge trading only burns capital. Step back and check AI Bias!",
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
                    "body": "Market swept your SL like an amateur. Don't revenge trade—check the AI Quant post-news verdict!",
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
            },
            {
                "india": {
                    "title": "Account blow hone se 1 trade door? 💣📉",
                    "body": "Stop! Aaj ka trading session wrap karo. Trade Journal me apni mistake note karo aur kal aao.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "One bad trade away from blowing up? 💣📉",
                    "body": "Stop trading for today. Step away from the screen, log your mistakes in Trade Journal, reset!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Gold ne 15 minute me 120 pips uda diye! 🏆🚀",
                    "body": "Kya aapne rally pakdi ya side me baith ke dekhte rahe? Tap to see live shock chart!",
                    "route": "home"
                },
                "global": {
                    "title": "Gold just ripped 120 pips in 15 mins! 🏆🚀",
                    "body": "Did you catch the move or watch from the sidelines? Check the live breakout breakdown now!",
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
                    "body": "Dry your tears. Look at the USD/JPY 4-hour trend instead. Clean trendlines don't break hearts!",
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
                    "body": "Get used to rejection, or audit your trade setups in the Trade Journal. Tap to review your day!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Kal subah market me kya hone wala hai? 🔮⚡",
                    "body": "Asian session ke top catalysts ready hain. Sone se pehle kal ka gameplan dekh lo!",
                    "route": "calendar"
                },
                "global": {
                    "title": "What is the market cooking for tomorrow? 🔮⚡",
                    "body": "Tomorrow's high-impact releases are queued. Review the economic minefield before you sleep!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "PnL laal hai par sabak bada mila? 🧠💡",
                    "body": "Loss ko fee samjho market university ki. Par wahi galti dohrana gunah hai. Log it in Journal!",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Red day? Treat it as tuition, not a defeat 🧠💡",
                    "body": "Losses are the tuition fee of trading. Repeating the same mistake is on you. Log it in Journal!",
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
                    "title": "Mom thinks you're studying late at night 📚🥺",
                    "body": "You staring at a 1-minute Gold candle calculating drawdown at midnight: Take a break!",
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
                    "body": "Can't sleep anyway? Check Asian session setups. Much more productive than doom-scrolling!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Screen ki neeli roshni me aankhein jali? 📱🥱",
                    "body": "Charts se door hato bhai. Market kal bhi yahi rahegi. Sleep tight and trade fresh tomorrow!",
                    "route": "home"
                },
                "global": {
                    "title": "Blue light burning your eyes at 1 AM? 📱🥱",
                    "body": "Step away from the screens. The market will be here tomorrow. Rest up for the London open!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Overnight swap charges account kha jayenge 💸🌙",
                    "body": "Negative swap pairs hold kar rahe ho? Check swap calculator and secure positions now!",
                    "route": "tools"
                },
                "global": {
                    "title": "Overnight swap fees eating your profits? 💸🌙",
                    "body": "Holding high-interest pairs overnight? Check your swap exposure before broker rollover!",
                    "route": "tools"
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
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
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
                "india": {
                    "title": "Weekend par overtrading se bache? 🏖️🧘",
                    "body": "Forex closed hai toh shanti se Trade Journal review karo. Monday ko fresh mind se aao!",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Protected your capital from weekend itch? 🏖️🧘",
                    "body": "Markets are closed. Spend 15 minutes reviewing your trade setups, not revenge trading low liquidity!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Shaadi me gaye the ya charts par baithe rahe? 🍛😂",
                    "body": "Weekend par screen band karo! Haftaa bhar ka PnL summary Trade Journal me lock karo.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Did you step outside or stare at frozen charts? ☀️😂",
                    "body": "Markets are shut for the weekend. Log your weekly performance in Trade Journal and disconnect!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Weekend par bhi broker ko yaad kar rahe ho? 🧠💸",
                    "body": "Trading addiction se bacho. Apne win-rate aur risk-to-reward metrics calculate karo.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Still thinking about your open orders? 🧠💸",
                    "body": "Turn off chart anxiety. 10 minutes of journaling beats 10 hours of weekend overthinking.",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "Bina plan ke agla hafta bhi loss me jayega 📓⚠️",
                    "body": "Pro traders weekend par journal review karte hain. Apni top 3 trading mistakes filter karo!",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "Trading without a weekly audit is just gambling 📓⚠️",
                    "body": "Pro traders spend Saturdays reviewing setups. Filter your top 3 leakages in Trade Journal!",
                    "route": "trade_journal"
                }
            }
        ]
    },
    {
        "slot_id": "sat_0330pm",
        "ist_hour": 15,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
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
                "india": {
                    "title": "Pips kamaye the ya broker ko donate kiye? 💸🧐",
                    "body": "Spread aur commission charges review karo. Disciplined trading guide abhi padho!",
                    "route": "home"
                },
                "global": {
                    "title": "Did you trade with an edge or trade for adrenaline? 💸🧐",
                    "body": "Adrenaline is expensive. Edge is profitable. Master your psychological game this weekend.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Bhai, market tujhse dushmani nahi nikaal raha 🤡🛑",
                    "body": "Trading psychology improve karo! Emotions control karne ka 3-step formula abhi padho.",
                    "route": "home"
                },
                "global": {
                    "title": "The market isn't out to get you personally 🤡🛑",
                    "body": "Cut the victim mindset. Master emotional discipline with our weekend Trader Psychology guide.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Screen ghanto dekhne se profits nahi badhte 📲🧘",
                    "body": "1-Tap Home Screen Widget setup karo. News timer seedha screen par dekho bina app khole!",
                    "route": "widget"
                },
                "global": {
                    "title": "Glued to your screen all week? 📲🧘",
                    "body": "Set up the 1-Tap Home Screen Widget! Countdown to high-impact releases right from your home screen.",
                    "route": "widget"
                }
            },
            {
                "india": {
                    "title": "'Bas ek aakhri trade le leta hu...' 💀💣",
                    "body": "Isi soch ne account blow kiya tha na? Weekend par trading psychology reset karo!",
                    "route": "home"
                },
                "global": {
                    "title": "'Just one last trade before bed...' 💀💣",
                    "body": "How many times did that wipe out a week's gains? Reset your mindset with our psychology guide!",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "sat_0730pm",
        "ist_hour": 19,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
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
            },
            {
                "india": {
                    "title": "Saturday night party ya Crypto volatility? 🍕🪙",
                    "body": "BTC $1,000 swing le raha hai! 24/7 live crypto radar check karo.",
                    "route": "market"
                },
                "global": {
                    "title": "Saturday Night: Crypto never sleeps 🍕🪙",
                    "body": "Bitcoin testing key weekend support. Track live 24/7 crypto momentum on the radar!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Weekend par bore ho rahe ho? 🪙📊",
                    "body": "Crypto market 24/7 khula hai! BTC aur ETH ke key liquidity levels track karo.",
                    "route": "market"
                },
                "global": {
                    "title": "Missing market volatility on a Saturday? 🪙📊",
                    "body": "Crypto runs 24/7! Check live Bitcoin & Ethereum order flow and breakout heatmaps.",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Saturday Special: AI Quant VIP trial 💎🔥",
                    "body": "Weekend me trading strategy polish karo. AI Quant Verdict unlock karo aur Monday ke liye ready ho jao!",
                    "route": "premium?reason=weekend_crypto"
                },
                "global": {
                    "title": "Saturday VIP Pass: 3-Day Free Trial 💎🔥",
                    "body": "Refine your trading playbook over the weekend. Unlock institutional AI Quant signals ahead of Monday!",
                    "route": "premium?reason=weekend_crypto"
                }
            },
            {
                "india": {
                    "title": "Pizza mangwaya? Chart par Crypto dekho 🍕📈",
                    "body": "Weekend volatility par scalping karna hai? AI Sentiment aur heatmaps check karo!",
                    "route": "market"
                },
                "global": {
                    "title": "Ordered pizza? Check the weekend crypto charts 🍕📈",
                    "body": "Weekend scalpers are hunting liquidity sweeps on BTC. Check AI Quant sentiment now!",
                    "route": "market"
                }
            }
        ]
    }
]

SUNDAY_SLOTS = [
    {
        "slot_id": "sun_1200pm",
        "ist_hour": 12,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
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
                "india": {
                    "title": "Naye hafte ka gameplan tayar hai? 🎯🗓️",
                    "body": "Monday gap-open se pehle high-impact releases mark kar lo. Economic calendar dekho!",
                    "route": "calendar"
                },
                "global": {
                    "title": "Is your trading battle plan set for Monday? 🎯🗓️",
                    "body": "Don't get blindsided on Monday morning. Mark the week's Red-Folder catalysts in your calendar!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "Sunday ko tayyari, Monday ko munafa 📊🗓️",
                    "body": "Is hafte 7 high-impact red news scheduled hain! Calendar me reminders set karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "Prepare on Sunday, profit on Monday 📊🗓️",
                    "body": "7 high-impact Red-Folder events queued this week! Set your calendar reminders now.",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "Monday ko blind trade mat lena! 🛑🗓️",
                    "body": "Central banks ka schedule check kiya? Economic calendar kholo aur high-volatility hours note karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "Never trade Monday morning blind! 🛑🗓️",
                    "body": "Did you check the central bank speeches? Open the Economic Calendar and spot high-risk hours.",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "Sunday brunch ke saath market calendar ☕🗓️",
                    "body": "NFP aur CPI aane wale hain! Haftaa shuru hone se pehle key levels plan kar lo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "Sunday prep: Next week's macro catalysts ☕🗓️",
                    "body": "NFP, CPI, and central bank minutes incoming! Plan your risk exposure before markets open.",
                    "route": "calendar"
                }
            }
        ]
    },
    {
        "slot_id": "sun_0500pm",
        "ist_hour": 17,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
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
                "india": {
                    "title": "Weekend khatam! Monday ke orders set hain? ⏰📊",
                    "body": "Sydney market khulne me sirf 4 ghante. Currency strength ranking dekh lo!",
                    "route": "market"
                },
                "global": {
                    "title": "Weekend wrapping up. Sydney opens in 4 hours! ⏰📊",
                    "body": "First market opening of the week is hours away. Check global currency strength rankings!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Sunday evening tension: 'Kal market kahan khulega?' 📈👀",
                    "body": "Gold gap-up hoga ya gap-down? AI Institutional bias pehle hi predict kar chuka hai!",
                    "route": "home"
                },
                "global": {
                    "title": "Sunday evening jitters: Where will markets gap? 📈👀",
                    "body": "Gold gap-up or gap-down? See how institutional algorithms are positioning before the open!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Sydney session me orders lagane ka time aa gaya 🌏⚡",
                    "body": "New Zealand aur Australian dollar me early momentum aane wala hai. Heatmap dekho!",
                    "route": "market"
                },
                "global": {
                    "title": "Sydney & Tokyo sessions warming up 🌏⚡",
                    "body": "Early momentum building on AUD and NZD pairs. Check the live sessions heatmap before open!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Kal subah alarm bajte hi trade mat dabana ⏰🛑",
                    "body": "Sunday night gap fills observe karo. Patience rakhna hi sabse bada edge hai!",
                    "route": "home"
                },
                "global": {
                    "title": "Don't smash market-order the second markets open ⏰🛑",
                    "body": "Watch the Sunday gap fills settle before risking capital. Patience is your real edge!",
                    "route": "home"
                }
            }
        ]
    },
    {
        "slot_id": "sun_0930pm",
        "ist_hour": 21,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
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
            },
            {
                "india": {
                    "title": "Bhai market chalu ho gaya! Sydney gap-open live 🚀🌏",
                    "body": "Gold aur JPY pairs me early movement check karo. Naya week, naya discipline!",
                    "route": "home"
                },
                "global": {
                    "title": "The wait is over: Sydney Gap-Open is LIVE 🚀🌏",
                    "body": "Gold and JPY pairs already showing early volatility. Start your week disciplined!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Sunday night: Sydney session ne gap khol diya! 💥📈",
                    "body": "Gap-trade setups ban rahe hain! Currency Heatmap par early winners check karo.",
                    "route": "market"
                },
                "global": {
                    "title": "Sunday night action: Weekend gaps are active! 💥📈",
                    "body": "Opening price gaps are active on Gold & FX pairs. Check the live sessions radar now!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "Hafta shuru! Pehla trade discipline ke sath lena 🎯📊",
                    "body": "Sydney session live hai. Overleveraging mat karna, apna trading plan follow karo!",
                    "route": "home"
                },
                "global": {
                    "title": "New trading week is officially underway! 🎯📊",
                    "body": "Sydney session is live. Stick strictly to your risk rules—no revenge trades from last week!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "Neend nahi aa rahi? Sydney market dekh lo! 🌙🌏",
                    "body": "JPY pairs me move shuru ho chuka hai. Naye hafte ka live chart abhi dekho!",
                    "route": "home"
                },
                "global": {
                    "title": "Can't sleep on a Sunday night? Sydney is open! 🌙🌏",
                    "body": "Early liquidity entering JPY & AUD pairs. Check the live opening candles right now!",
                    "route": "home"
                }
            }
        ]
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
    day_of_year = now_ist.timetuple().tm_yday
    if weekday == 5: # Saturday
        for slot in SATURDAY_SLOTS:
            slot_h = slot["ist_hour"]
            # Active window: allows trigger anytime within a 3-hour window from slot start
            if slot_h <= ist_hour < slot_h + 3:
                dedup_key = f"retention_sat_{slot['slot_id']}_{date_str}"
                if is_sent_fn(dedup_key, local_history, db_client):
                    continue

                pool = slot["pool"]
                chosen = pool[day_of_year % len(pool)]
                ch_id = slot.get("channel_id", CHANNEL_DAILY_BRIEFING)

                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_INDIA,
                    title=chosen["india"]["title"],
                    body=chosen["india"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": chosen["india"]["route"], "channelId": ch_id},
                    channel_id=ch_id,
                    priority="high"
                )
                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_GLOBAL,
                    title=chosen["global"]["title"],
                    body=chosen["global"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": chosen["global"]["route"], "channelId": ch_id},
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

                pool = slot["pool"]
                chosen = pool[day_of_year % len(pool)]
                ch_id = slot.get("channel_id", CHANNEL_DAILY_BRIEFING)

                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_INDIA,
                    title=chosen["india"]["title"],
                    body=chosen["india"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": chosen["india"]["route"], "channelId": ch_id},
                    channel_id=ch_id,
                    priority="high"
                )
                send_message_fn(
                    messaging_client=messaging_client,
                    topic=TOPIC_GLOBAL,
                    title=chosen["global"]["title"],
                    body=chosen["global"]["body"],
                    data={"type": "RETENTION_WEEKEND", "route": chosen["global"]["route"], "channelId": ch_id},
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
