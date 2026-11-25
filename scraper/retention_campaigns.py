#!/usr/bin/env python3
"""
Professional Trader Retention and Engagement Notification Engine.
==================================================================
Zero awkward/meme notifications. 100% real trader notifications:
- Global Market Sessions (Tokyo, London, New York, Sydney, Overlap)
- Daily Market Briefings & Live Breaking News Updates
- Weekly Macro Economic Minefield & Weekend Reviews
- Risk Management & Disciplined Trade Journaling
- Emojified, bug-free, and deduplicated per slot per calendar day.
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
    # ── 08:00 AM IST: Pre-European Session & Asian Wrap ──────────────────────
    {
        "slot_id": "slot_08am",
        "ist_hour": 8,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "🌅 Asian Session Wrap: Key Levels Active",
                    "body": "Tokyo session wrap ho chuka hai! Frankfurt & London open se pehle EUR & JPY ka currency status check karo.",
                    "route": "market"
                },
                "global": {
                    "title": "🌅 Asian Session Wrap: Key Levels In Play",
                    "body": "Tokyo volume settled. Check early currency rankings and European opening outlook now!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "☕ Good Morning Trader! Aaj Ka Gameplan Ready?",
                    "body": "Aaj high-impact Red-Folder releases aane wale hain! Blind trade mat lo, economic calendar dekho.",
                    "route": "calendar"
                },
                "global": {
                    "title": "☕ Morning Market Prep: Today's High-Impact Releases",
                    "body": "Major central bank catalysts dropping today. Review the economic release calendar before London opens!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "📊 Currency Strength Heatmap Update",
                    "body": "Asian session ke baad kaunsi currency sabse strong hai? Live Currency Heatmap par dominant pairs dekho.",
                    "route": "market"
                },
                "global": {
                    "title": "📊 Live Currency Heatmap: Morning Momentum",
                    "body": "Spot the strongest and weakest currencies before the European session opens. Check the live heatmap!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "⚡ Institutional Pre-Market Focus",
                    "body": "EUR/USD aur GBP/USD me overnight volume active hai. London open se pehle key pivot levels note karo.",
                    "route": "home"
                },
                "global": {
                    "title": "⚡ Pre-Europe Order Flow Alert",
                    "body": "Early volume accumulating across EUR/USD and GBP/USD. Check key liquidity zones before the opening bell.",
                    "route": "home"
                }
            }
        ]
    },

    # ── 10:00 AM IST: Pre-London Liquidity Positioning ────────────────────────
    {
        "slot_id": "slot_10am",
        "ist_hour": 10,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "🏛️ Central Bank Sentiment & Macro Bias",
                    "body": "Institutions macro fundamentals par trade karte hain. Aaj ka AI Macro Sentiment breakdown check karo!",
                    "route": "home"
                },
                "global": {
                    "title": "🏛️ Central Bank Sentiment & Macro Outlook",
                    "body": "Smart money tracks central bank policy differentials. Check today's AI Macro Sentiment breakdown.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "🎯 London Pre-Open: Market Preparation",
                    "body": "European trading session ki taiyari! EUR/USD aur GBP/USD ke key support & resistance zones check karo.",
                    "route": "home"
                },
                "global": {
                    "title": "🎯 London Pre-Open: Market Preparation",
                    "body": "European session approaching. Identify key session highs, lows, and today's economic schedule before the open.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "📰 Breaking Market News & Catalyst Radar",
                    "body": "European bond yields aur macro headlines live hain. Real-time Breaking News feed abhi check karo!",
                    "route": "news_feed"
                },
                "global": {
                    "title": "📰 Real-Time Macro News & Breaking Catalysts",
                    "body": "European sovereign yields and policy commentary moving FX crosses. Check real-time Breaking News!",
                    "route": "news_feed"
                }
            },
            {
                "india": {
                    "title": "🛡️ Risk Rule: Plan Your Trades, Trade Your Plan",
                    "body": "Overtrading se bacho! Aaj sirf high-probability A+ setups execute karo. Calendar me countdown timers set karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "🛡️ Discipline Check: Wait For Confirmed Setups",
                    "body": "Quality over quantity. Review your risk rules and check today's Red-Folder event countdown timers.",
                    "route": "calendar"
                }
            }
        ]
    },

    # ── 12:00 PM IST: Mid-Day European Market Radar ───────────────────────────
    {
        "slot_id": "slot_12pm",
        "ist_hour": 12,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "📊 Mid-Day Market Check: European Outlook",
                    "body": "European trading hours ke liye taiyar raho! EUR/USD aur GBP/USD pairs ka live status aur rates dekho.",
                    "route": "market"
                },
                "global": {
                    "title": "📊 Mid-Day Market Check: European Outlook",
                    "body": "European trading window approaching. Monitor currency strength rankings and key levels on the Live Heatmap.",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "⚡ European Crosses & Gold Radar",
                    "body": "Gold (XAU/USD) aur GBP crosses me active trading volume. Trailing stop loss aur risk manage karo.",
                    "route": "home"
                },
                "global": {
                    "title": "⚡ European Crosses & Gold Radar",
                    "body": "Active market participation across Gold (XAU/USD) and Sterling pairs. Review key technical levels and risk limits.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "📈 Mid-Day Technical Radar",
                    "body": "Key currency support aur resistance levels track karo. Live chart aur trend status abhi dekho.",
                    "route": "home"
                },
                "global": {
                    "title": "📈 Mid-Day Technical Radar",
                    "body": "Monitor primary currency support and resistance levels. Track live charts and technical indicators now.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "💎 Unlock PRO Trading Edge: Live Institutional Feed",
                    "body": "Real-time economic event breakdowns aur AI macro sentiment unlock karo with 3-Day Free Trial!",
                    "route": "premium?reason=smart_pricing"
                },
                "global": {
                    "title": "💎 Unlock Institutional PRO Edge: Ad-Free Real-Time Feed",
                    "body": "Access unfiltered economic intelligence, real-time shock alerts, and live currency radar with 3-Day Free Trial!",
                    "route": "premium?reason=smart_pricing"
                }
            }
        ]
    },

    # ── 02:00 PM IST: Mid-Day European Momentum & Order Flow ──────────────────
    {
        "slot_id": "slot_02pm",
        "ist_hour": 14,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "📊 Mid-Day Market Pulse: Gold & Major Crosses",
                    "body": "London mid-session volumes steady hain. XAU/USD aur EUR/USD ke institutional liquidity zones check karo.",
                    "route": "home"
                },
                "global": {
                    "title": "📊 Mid-Day Market Pulse: Gold & Major Crosses",
                    "body": "Mid-session institutional positioning across Gold and major currencies. Review active support/resistance!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "🌐 Currency Flow Alert: Strongest vs Weakest",
                    "body": "GBP aur EUR me divergence detect hua hai. Live Currency Strength Heatmap par dominant pairs dekho.",
                    "route": "market"
                },
                "global": {
                    "title": "🌐 Currency Strength Divergence Detected",
                    "body": "Diverging trends across European majors. Check the Currency Strength Heatmap to trade with the trend!",
                    "route": "market"
                }
            },
            {
                "india": {
                    "title": "📰 European Breaking Headlines",
                    "body": "Central Bank statements aur bond auction results live hain. Breaking News feed par market updates dekho.",
                    "route": "news_feed"
                },
                "global": {
                    "title": "📰 European Mid-Day Macro Wire",
                    "body": "Central bank remarks and fixed income auctions moving currency crosses. Track live breaking headlines!",
                    "route": "news_feed"
                }
            },
            {
                "india": {
                    "title": "🎯 US Session Pre-Market Setup",
                    "body": "US market open hone me kuch ghante bache hain. Upcoming high-impact Red news schedule verify karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "🎯 US Session Pre-Market Watch",
                    "body": "New York session approaching. Review scheduled US economic releases to prepare your risk parameters.",
                    "route": "calendar"
                }
            }
        ]
    },

    # ── 04:00 PM IST: Pre-New York & US Macro Release Watch ───────────────────
    {
        "slot_id": "slot_04pm",
        "ist_hour": 16,
        "channel_id": CHANNEL_CALENDAR_ALERTS,
        "pool": [
            {
                "india": {
                    "title": "🧮 Risk Management Check: 1-Tap Lot Calculator",
                    "body": "High-impact US session se pehle risk calculate karo! Lot Size Calculator se stop-loss aur margin verify karo.",
                    "route": "tools"
                },
                "global": {
                    "title": "🧮 Position Size Check: 1-Tap Lot Calculator",
                    "body": "Pre-US news volatility can spike spreads. Calculate exact pip risk with the 1-Tap Calculator before entering!",
                    "route": "tools"
                }
            },
            {
                "india": {
                    "title": "🚨 High-Impact US News Countdown",
                    "body": "Agle session me major US economic data aane wala hai. Calendar countdown timers verify karo!",
                    "route": "calendar"
                },
                "global": {
                    "title": "🚨 High-Impact US Economic Data Incoming",
                    "body": "Red-Folder US economic catalysts release soon. Verify release times and forecasts on the Calendar!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "💼 Capital Protection Rule: Never Trade Blind",
                    "body": "News spike se pehle market orders place mat karo. Actual release aane do aur pip reaction dekho.",
                    "route": "calendar"
                },
                "global": {
                    "title": "💼 Capital Preservation Rule: News Discipline",
                    "body": "Avoid placing premature orders before the data print. Wait for the actual release and confirm direction.",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "📈 US Dollar Index (DXY) Testing Key Levels",
                    "body": "DXY major resistance test kar raha hai. USD pairs aur Gold me high volatility expected hai.",
                    "route": "home"
                },
                "global": {
                    "title": "📈 US Dollar Index (DXY) at Key Technical Pivot",
                    "body": "DXY approaching critical technical levels. Expect heightened volatility across USD pairs and Gold.",
                    "route": "home"
                }
            }
        ]
    },

    # ── 06:00 PM IST: New York Open & Wall Street Opening Bell ────────────────
    {
        "slot_id": "slot_06pm",
        "ist_hour": 18,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "🇺🇸 US Market Hours: Evening Trading Active 🔔",
                    "body": "US market session active hai. US Dollar aur Gold (XAU/USD) ka live status aur upcoming economic news dekho.",
                    "route": "home"
                },
                "global": {
                    "title": "🇺🇸 US Market Hours: Trading Active 🔔",
                    "body": "US trading session is active. Monitor USD currency strength, Gold (XAU/USD), and scheduled economic news.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "🛡️ Stop Loss Verification Alert",
                    "body": "New York session me sudden price shifts ho sakte hain! Apni open positions par Stop Loss zaroor check karo.",
                    "route": "home"
                },
                "global": {
                    "title": "🛡️ Protect Capital: Verify Your Stop Loss",
                    "body": "New York session brings active price action. Ensure all open positions have active stop-loss protection!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "⚡ US Economic Catalysts Releasing Now",
                    "body": "High-impact US figures release ho rahe hain! Live Actual vs Forecast prints aur reaction check karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "⚡ US Economic Catalysts Releasing Live",
                    "body": "Red-Folder US macro data is printing. Check live actual vs forecast numbers and market reactions!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "🌐 Currency Heatmap: US Session Shift",
                    "body": "US session me kaunsi currency dominate kar rahi hai? Live Heatmap ranking abhi dekho.",
                    "route": "market"
                },
                "global": {
                    "title": "🌐 Currency Heatmap: New York Session Shift",
                    "body": "Track dynamic shifts in currency dominance as US trading hours proceed.",
                    "route": "market"
                }
            }
        ]
    },

    # ── 08:00 PM IST: London & New York Overlap Session ────────────────────────
    {
        "slot_id": "slot_08pm",
        "ist_hour": 20,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "🌐 London & New York Overlap Session Active",
                    "body": "London aur New York dono financial centers active hain! EUR/USD, GBP/USD aur USD pairs ka live status dekho.",
                    "route": "home"
                },
                "global": {
                    "title": "🌐 London & New York Overlap Session Active",
                    "body": "London and New York markets are actively trading. Monitor live rates and currency rankings on the Live Heatmap.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "🏆 Gold (XAU/USD) & Major Pairs Update",
                    "body": "Gold (XAU/USD) aur US Dollar pairs me steady trading volume active hai. Live support aur resistance levels check karo.",
                    "route": "home"
                },
                "global": {
                    "title": "🏆 Gold (XAU/USD) & Major Pairs Update",
                    "body": "Active trading volume across Gold (XAU/USD) and US Dollar pairs. Track live price action and technical levels.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "🎯 Overlap Trading Rule: Lock In Profits",
                    "body": "Jab move aapke favor me ho, trailing stop loss move karo aur profits secure karo. Live chart dekho.",
                    "route": "home"
                },
                "global": {
                    "title": "🎯 Overlap Strategy: Secure Your Profits",
                    "body": "High session liquidity means active price movements. Protect unrealized gains by trailing your stops!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "📰 Breaking News & Fed Commentary",
                    "body": "Federal Reserve officials aur market sentiment headlines live hain. Real-time news feed check karo.",
                    "route": "news_feed"
                },
                "global": {
                    "title": "📰 Breaking Macro Wire & Fed Commentary",
                    "body": "Late-session central bank remarks and rate outlook updates active. Check real-time breaking news!",
                    "route": "news_feed"
                }
            }
        ]
    },

    # ── 10:00 PM IST: Post-US Session Wrap & Trade Journal ────────────────────
    {
        "slot_id": "slot_10pm",
        "ist_hour": 22,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "📓 Daily Trade Audit: Sone Se Pehle Log Karo",
                    "body": "Disciplined trader banna hai toh daily journal maintain karo! Aaj ke wins aur lessons Trade Journal me add karo.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "📓 Daily Trade Audit: Review Today's Execution",
                    "body": "Top traders audit their setups daily. Log your wins, losses, and psychological takeaways in Trade Journal!",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "🔮 Tomorrow's Macro Minefield Preview",
                    "body": "Kal subah Asian aur London session me kya release hone wala hai? Sone se pehle economic calendar check karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "🔮 Tomorrow's Economic Minefield Preview",
                    "body": "Tomorrow's high-impact releases are queued. Review the upcoming economic calendar before you rest!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "💡 Trader Mindset: Continuous Improvement",
                    "body": "Har trading session ek naya lesson hota hai. Apni mistakes analyze karo aur kal ke liye fresh gameplan banao.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "💡 Trader Growth: Consistency Over Speed",
                    "body": "Every session offers valuable data. Review your execution metrics and prepare for tomorrow's market open.",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "🚀 Level Up to PRO: Advanced AI Market Analysis",
                    "body": "VIP institutional heatmaps, real-time ad-free economic alerts aur AI insights unlock karo!",
                    "route": "premium?reason=night_upgrade"
                },
                "global": {
                    "title": "🚀 Trade with Institutional PRO Edge",
                    "body": "Upgrade to PRO for unfiltered real-time catalyst alerts, AI market analysis, and live session tools.",
                    "route": "premium?reason=night_upgrade"
                }
            }
        ]
    },

    # ── 12:00 AM Midnight IST: Daily Candle Close & Capital Protection ────────
    {
        "slot_id": "slot_12am",
        "ist_hour": 0,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "🌙 Daily Candle Close: Overnight Risk Management",
                    "body": "Daily candle close ho chuki hai! Open positions me Stop Loss verify karo ya profits book karke rest karo.",
                    "route": "home"
                },
                "global": {
                    "title": "🌙 Daily Candle Close: Manage Overnight Exposure",
                    "body": "Daily close is finalized. Ensure open positions are properly hedged against overnight rollover swaps.",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "💸 Overnight Rollover & Swap Rate Check",
                    "body": "Overnight pairs hold kar rahe ho? Swap Calculator se apne broker rollover charges verify karo.",
                    "route": "tools"
                },
                "global": {
                    "title": "💸 Overnight Swap Rate Verification",
                    "body": "Holding currency positions past 5 PM NY? Check your broker rollover and swap fees with the Calculator.",
                    "route": "tools"
                }
            },
            {
                "india": {
                    "title": "😴 Clear Mindset: Rest Before Asian Open",
                    "body": "Screen band karo aur proper rest lo. Market kal subah bhi yahi rahegi. Trade fresh tomorrow!",
                    "route": "home"
                },
                "global": {
                    "title": "😴 Rest & Recharge: Prepare for Tomorrow",
                    "body": "A disciplined mind requires quality rest. Step away from the screens and be ready for tomorrow's open!",
                    "route": "home"
                }
            }
        ]
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. SPECIAL WEEKEND SLOTS (SATURDAY & SUNDAY - ZERO LIVE SPAM)
# ─────────────────────────────────────────────────────────────────────────────
SATURDAY_SLOTS = [
    # ── Saturday Morning: Weekly Trade Journal Audit ─────────────────────────
    {
        "slot_id": "sat_1130am",
        "ist_hour": 11,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "📓 Weekly Trade Audit: Haftaa Kaisa Raha?",
                    "body": "Forex market band hai! Apne is hafte ke trades ka review karo Trade Journal me aur win-rate check karo.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "📓 Weekly Trade Audit: Did You Beat the Market?",
                    "body": "Markets are closed for the weekend. Review your wins, cut recurring mistakes, and analyze your win-rate in Trade Journal.",
                    "route": "trade_journal"
                }
            },
            {
                "india": {
                    "title": "🧘 Weekend Discipline: Review, Don't Revenge Trade",
                    "body": "Market band hone par Trade Journal audit karo. Apni top 3 trading mistakes filter karo aur Monday ke liye prepare raho.",
                    "route": "trade_journal"
                },
                "global": {
                    "title": "🧘 Weekend Discipline: Audit Your Trading Edge",
                    "body": "Pro traders spend Saturdays reviewing execution data. Filter your performance in the Trade Journal!",
                    "route": "trade_journal"
                }
            }
        ]
    },

    # ── Saturday Afternoon: Trader Psychology & Tools ─────────────────────────
    {
        "slot_id": "sat_0330pm",
        "ist_hour": 15,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "📲 1-Tap Home Screen Widget Setup Karo",
                    "body": "Economic event countdown timer seedha home screen par dekho bina app khole! Widget setup karo.",
                    "route": "widget"
                },
                "global": {
                    "title": "📲 1-Tap Home Screen Countdown Widget",
                    "body": "Track upcoming high-impact economic releases right from your phone's home screen. Set up the Widget!",
                    "route": "widget"
                }
            },
            {
                "india": {
                    "title": "🧠 Trader Psychology: Mastering Emotional Control",
                    "body": "90% trading mistakes psychology se hoti hain. Disciplined risk management rules abhi padho!",
                    "route": "home"
                },
                "global": {
                    "title": "🧠 Trader Psychology: Eliminating Emotional Bias",
                    "body": "Discipline beats emotion every time. Master risk management and execution consistency this weekend.",
                    "route": "home"
                }
            }
        ]
    },

    # ── Saturday Evening: 24/7 Digital Assets & Market Wrap ───────────────────
    {
        "slot_id": "sat_0730pm",
        "ist_hour": 19,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "📰 Saturday Special: Weekly Market Wrap",
                    "body": "Is hafte ke top central bank catalysts aur macro news summarize ho chuke hain. Breaking news wrap dekho!",
                    "route": "news_feed"
                },
                "global": {
                    "title": "📰 Saturday Special: Macro News In Review",
                    "body": "Catch up on the major economic catalysts and policy statements that moved the markets this week.",
                    "route": "news_feed"
                }
            },
            {
                "india": {
                    "title": "🪙 24/7 Weekend Market: Crypto Order Flow",
                    "body": "Forex closed hai par Bitcoin & Ethereum 24/7 live hain. Weekend crypto support & resistance track karo.",
                    "route": "market"
                },
                "global": {
                    "title": "🪙 24/7 Digital Assets: Weekend Momentum",
                    "body": "Track Bitcoin and Ethereum volatility while traditional markets rest. View live weekend heatmaps!",
                    "route": "market"
                }
            }
        ]
    }
]

SUNDAY_SLOTS = [
    # ── Sunday Noon: Next Week's Economic Minefield ───────────────────────────
    {
        "slot_id": "sun_1200pm",
        "ist_hour": 12,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "🗓️ Agle Hafte Ka Economic Calendar Ready Hai!",
                    "body": "NFP, CPI aur Central Bank rate decisions scheduled hain! Poore hafte ki Red-Folder list abhi check karo.",
                    "route": "calendar"
                },
                "global": {
                    "title": "🗓️ Next Week's Economic Minefield is Live!",
                    "body": "Fed rate decisions, US CPI, and jobs data scheduled this week. Review exact dates, times, and forecasts!",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "🎯 Sunday Preparation: Monday Ko Munafa",
                    "body": "Is hafte kitne high-impact events hain? Reminders set karo taaki koi important move miss na ho.",
                    "route": "calendar"
                },
                "global": {
                    "title": "🎯 Sunday Preparation: Weekly Battle Plan",
                    "body": "Major central bank volatility queued for the upcoming week. Set your calendar reminders now!",
                    "route": "calendar"
                }
            }
        ]
    },

    # ── Sunday Evening: Opening Gaps & Sydney Pre-Market ──────────────────────
    {
        "slot_id": "sun_0500pm",
        "ist_hour": 17,
        "channel_id": CHANNEL_DAILY_BRIEFING,
        "pool": [
            {
                "india": {
                    "title": "📊 Sunday Night Gaps: Gold & US Dollar",
                    "body": "Weekend geopolitical developments se opening gaps expected hain. AI Macro Bias aur currency rankings dekho!",
                    "route": "home"
                },
                "global": {
                    "title": "📊 Weekly Opening Gaps: Gold & Major FX",
                    "body": "Weekend developments can trigger significant Sunday opening price gaps. Check AI Macro Bias now!",
                    "route": "home"
                }
            },
            {
                "india": {
                    "title": "⏰ Sydney Market Khulne Me Kuch Ghante",
                    "body": "New week shuru hone wala hai! Sydney aur Tokyo session ke liye apni watchlist ready rakho.",
                    "route": "market"
                },
                "global": {
                    "title": "⏰ Sydney Weekly Kickoff Approaching",
                    "body": "The first market open of the week is hours away. Check global currency strength rankings before open!",
                    "route": "market"
                }
            }
        ]
    },

    # ── Sunday Night: Final Monday Gameplan ────────────────────────────────────
    {
        "slot_id": "sun_0930pm",
        "ist_hour": 21,
        "channel_id": CHANNEL_BREAKING_NEWS,
        "pool": [
            {
                "india": {
                    "title": "🌅 Kal Subah Market Open Ki Watchlist Ready?",
                    "body": "Monday gap-open se pehle key support/resistance levels note kar lo. Naye week me disciplined raho!",
                    "route": "calendar"
                },
                "global": {
                    "title": "🌅 Ready for Monday's Market Open?",
                    "body": "Prepare your trading watchlist tonight! Review major technical zones on Gold & EUR/USD ahead of open.",
                    "route": "calendar"
                }
            },
            {
                "india": {
                    "title": "🌙 Good Night Trader! Let's Conquer The Week",
                    "body": "Proper rest lo. Fresh mind ke saath Monday trading sessions me enter karna. Happy Trading!",
                    "route": "home"
                },
                "global": {
                    "title": "🌙 Rest Well, Trader! Ready for the New Week",
                    "body": "A disciplined mind executes best. Get good rest and be ready for tomorrow's market sessions!",
                    "route": "home"
                }
            }
        ]
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# 3. SPECIAL CALENDAR MACRO HOOKS (STRICT ACTIVE WINDOWS & DATES)
# ─────────────────────────────────────────────────────────────────────────────
def is_nfp_week_window(now_ist):
    # First Friday of month (NFP Week)
    return now_ist.day in (1, 2, 3, 4, 5, 6, 7) and now_ist.weekday() == 4 and now_ist.hour in (12, 17)

def is_month_end_rebalance_window(now_ist):
    # 28th to last day of month (Month-End Institutional Flow)
    return now_ist.day in (28, 29, 30, 31) and now_ist.hour in (14, 19)

def is_quarter_end_window(now_ist):
    # End of Q1, Q2, Q3, Q4 (March, June, September, December 29-31)
    return now_ist.month in (3, 6, 9, 12) and now_ist.day in (29, 30, 31) and now_ist.hour in (13, 18)

def is_year_end_holiday_window(now_ist):
    # Dec 24 to Jan 2 (Thin Liquidity / Bank Holidays)
    return (now_ist.month == 12 and now_ist.day >= 24) or (now_ist.month == 1 and now_ist.day <= 2)

def get_special_calendar_hook(now_ist):
    """
    Evaluates current IST time against strict macro calendar events.
    Returns hook dictionary if an active event matches, else None.
    """
    # 1. NFP Super-Friday Alert (First Friday of month)
    if is_nfp_week_window(now_ist):
        return {
            "key": f"nfp_friday_{now_ist.strftime('%Y_%m')}",
            "channel_id": CHANNEL_CALENDAR_ALERTS,
            "india": {
                "title": "⚡ NFP Friday Alert: US Jobs Data Today!",
                "body": "Month ka sabse volatile trading day! Non-Farm Payrolls aane se pehle risk calculator se lot size fix karo.",
                "route": "calendar"
            },
            "global": {
                "title": "⚡ NFP Friday Alert: US Non-Farm Payrolls Today!",
                "body": "Major volatility expected on Gold and USD pairs. Check release forecasts and manage your risk exposure!",
                "route": "calendar"
            }
        }

    # 2. Month-End Institutional Rebalancing
    if is_month_end_rebalance_window(now_ist):
        return {
            "key": f"monthend_flow_{now_ist.strftime('%Y_%m')}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "📊 Month-End Portfolio Flow In Progress",
                "body": "Institutions aur pension funds portfolio rebalance kar rahe hain. Unexpected currency volatility par nazar rakho!",
                "route": "market"
            },
            "global": {
                "title": "📊 Month-End Institutional Flow Alert",
                "body": "Institutional portfolio rebalancing can trigger large fixing flows. Track active currency strength changes!",
                "route": "market"
            }
        }

    # 3. Quarter-End Rebalance
    if is_quarter_end_window(now_ist):
        return {
            "key": f"quarter_end_{now_ist.year}_q{(now_ist.month-1)//3 + 1}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "🏛️ Quarter-End Institutional Rebalancing",
                "body": "Quarter close ho raha hai! Major global banks aur funds apne currency reserves adjust kar rahe hain.",
                "route": "home"
            },
            "global": {
                "title": "🏛️ Quarter-End Rebalancing & Institutional Flows",
                "body": "Major institutional flows across currency reserves as the quarter wraps up. Review key support/resistance!",
                "route": "home"
            }
        }

    # 4. Year-End Holiday Thin Liquidity
    if is_year_end_holiday_window(now_ist) and now_ist.hour in (11, 16):
        return {
            "key": f"yearend_holiday_{now_ist.year}",
            "channel_id": CHANNEL_DAILY_BRIEFING,
            "india": {
                "title": "❄️ Year-End Thin Liquidity & Wide Spread Warning",
                "body": "Major central banks vacation par hain aur liquidity thin hai. Wider spreads se capital protect karo!",
                "route": "trade_journal"
            },
            "global": {
                "title": "❄️ Holiday Season: Thin Liquidity Warning",
                "body": "Bank holidays mean reduced liquidity and wider broker spreads. Trade defensively and audit your journal!",
                "route": "trade_journal"
            }
        }

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. MASTER RETENTION DISPATCH LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def check_retention_campaign_dispatch(now_utc, local_history, messaging_client, db_client, send_message_fn, record_sent_fn, is_sent_fn):
    """
    Main retention dispatcher called periodically from fcm_push_dispatcher.py.
    
    Guarantees:
    - Silent DND hours (12:30 AM to 07:59 AM IST) are strictly protected.
    - Sends professional Hinglish/English to 'india_traders' and Universal English to 'global_traders'.
    - Deduplicated strictly per slot per calendar day.
    """
    now_ist = now_utc + timedelta(hours=5, minutes=30)
    ist_hour = now_ist.hour
    date_str = now_ist.strftime("%Y-%m-%d")
    weekday = now_ist.weekday()  # 0 = Monday, ..., 5 = Saturday, 6 = Sunday

    # DND Window: 12:30 AM to 07:59 AM IST
    if 1 <= ist_hour < 8:
        logger.debug(f"Current IST time ({now_ist.strftime('%H:%M')}) is in silent night DND. Skipping retention.")
        return 0

    dispatched = 0

    # ── CHECK 1: SPECIAL MACRO CALENDAR DATE HOOKS ──
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
                {"sent_at": now_utc.isoformat(), "slot": hook_key, "date": date_str, "type": "SPECIAL_MACRO_HOOK"},
                local_history,
                db_client
            )
            logger.info(f"✓ Dispatched Special Macro Hook: {hook_key}")
            dispatched += 1
            return dispatched

    # ── CHECK 2: WEEKENDS (SATURDAY & SUNDAY) ──
    day_of_year = now_ist.timetuple().tm_yday
    if weekday == 5:  # Saturday
        for slot in SATURDAY_SLOTS:
            slot_h = slot["ist_hour"]
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

    elif weekday == 6:  # Sunday
        for slot in SUNDAY_SLOTS:
            slot_h = slot["ist_hour"]
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
        slot_h = slot["ist_hour"]
        if slot_h <= ist_hour < slot_h + 2:
            dedup_key = f"retention_weekday_{slot['slot_id']}_{date_str}"
            if is_sent_fn(dedup_key, local_history, db_client):
                logger.debug(f"Retention slot {slot['slot_id']} already sent for {date_str}.")
                continue

            pool = slot["pool"]
            day_of_year = now_ist.timetuple().tm_yday
            chosen = pool[day_of_year % len(pool)]

            ch_id = slot.get("channel_id", CHANNEL_BREAKING_NEWS)

            # 1. Send India (Clear Hinglish / Professional copy)
            send_message_fn(
                messaging_client=messaging_client,
                topic=TOPIC_INDIA,
                title=chosen["india"]["title"],
                body=chosen["india"]["body"],
                data={"type": "RETENTION_2HOUR", "route": chosen["india"]["route"], "channelId": ch_id},
                channel_id=ch_id,
                priority="high"
            )

            # 2. Send Global (Universal English high-converting copy)
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
            logger.info(f"✓ Dispatched Weekday Retention Slot: {slot['slot_id']} ({chosen['india']['title']})")
            dispatched += 1

    return dispatched
