import telebot
import yfinance as yf
import ta
import pandas as pd

# === Bot Token (your token inserted) ===
BOT_TOKEN = "8208622897:AAH23ayuurLtjjUWBiFIb8HpzsppERpAWzk"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# === Pairs to watch (friendly names -> Yahoo tickers) ===
PAIR_MAP = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
    "USDJPY": "USDJPY=X",
    "XAUUSD": "XAUUSD=X"
}

# === Signal generator (1m primary, fallback to 5m/15m if no data) ===
def get_signal_for_pair(ticker):
    for interval in ["1m", "5m", "15m"]:
        try:
            data = yf.download(ticker, period="2d", interval=interval, progress=False)
        except Exception as e:
            return f"⚠️ Error fetching {ticker}: {e}"

        if data is None or data.empty or "Close" not in data:
            # try next interval
            continue

        # make sure Close is 1D series
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.squeeze()
        close = close.dropna()
        if len(close) < 30:
            # not enough candles -> try next interval
            continue

        try:
            # RSI
            rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

            # MACD
            macd = ta.trend.MACD(close)
            macd_val = macd.macd().iloc[-1]
            macd_sig = macd.macd_signal().iloc[-1]

            # Moving averages
            sma20 = ta.trend.SMAIndicator(close, window=20).sma_indicator().iloc[-1]
            sma50 = ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1]

            # Last candle direction
            last = data.iloc[-1]
            candle = "Bullish" if last["Close"] > last["Open"] else "Bearish"

            # Decision logic (predict next 1m/5m/15m direction)
            if rsi < 30 and macd_val > macd_sig and sma20 > sma50 and candle == "Bullish":
                return f"{ticker} ({interval}) → 📈 BUY (next {interval})\nRSI: {rsi:.2f}\nMACD: Bullish\nTrend: UP"
            if rsi > 70 and macd_val < macd_sig and sma20 < sma50 and candle == "Bearish":
                return f"{ticker} ({interval}) → 📉 SELL (next {interval})\nRSI: {rsi:.2f}\nMACD: Bearish\nTrend: DOWN"

            # If no strong confluence, still return neutral (safe)
            return f"{ticker} ({interval}) → ⏸️ NO CLEAR ENTRY\nRSI: {rsi:.2f}\nMACD: Neutral\nCandle: {candle}"

        except Exception as e:
            return f"⚠️ Indicator error for {ticker}: {e}"

    return f"⚠️ No data for {ticker} on 1m/5m/15m. Market may be closed."

# === Telegram handlers ===
@bot.message_handler(commands=["start"])
def cmd_start(message):
    txt = "📊 Welcome to MANBOY Signal Bot!\n\nUse /signal to request a pair. Pick one and I will check live (1m primary)."
    bot.send_message(message.chat.id, txt)

@bot.message_handler(commands=["signal"])
def cmd_signal(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("EURUSD", "GBPUSD", "AUDUSD")
    markup.add("USDJPY", "XAUUSD")
    bot.send_message(message.chat.id, "📌 Choose a pair (1m primary):", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and m.text.strip().upper() in PAIR_MAP.keys())
def handle_pair_choice(message):
    choice = message.text.strip().upper()
    ticker = PAIR_MAP[choice]
    bot.send_message(message.chat.id, f"🔎 Checking {choice} (1m primary). Wait small...")
    result = get_signal_for_pair(ticker)
    bot.send_message(message.chat.id, result)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "⚠️ Unknown command. Use /signal then pick a pair (EURUSD, GBPUSD, AUDUSD, USDJPY, XAUUSD)")

# === Run bot ===
print("✅ Bot starting (polling)...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
