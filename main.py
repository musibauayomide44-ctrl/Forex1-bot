import telebot
import yfinance as yf
import ta

# =======================
# YOUR BOT TOKEN
# =======================
BOT_TOKEN = "PUT-YOUR-BOT-TOKEN-HERE"
bot = telebot.TeleBot(BOT_TOKEN)

# =======================
# Function to get signal
# =======================
def get_signal(symbol, interval):
    try:
        # Fetch recent data
        data = yf.download(symbol, period="2d", interval=interval)
        if data.empty:
            return f"⚠️ No data for {symbol} ({interval}). Market may be closed."

        close = data["Close"]

        # RSI
        rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]

        # MACD
        macd = ta.trend.MACD(close)
        macd_val = macd.macd().iloc[-1]
        signal_val = macd.macd_signal().iloc[-1]

        # Trading logic
        if rsi < 30 and macd_val > signal_val:
            return f"{symbol} {interval} → BUY 📈\nRSI: {rsi:.2f}\nMACD: Bullish crossover ✅"
        elif rsi > 70 and macd_val < signal_val:
            return f"{symbol} {interval} → SELL 📉\nRSI: {rsi:.2f}\nMACD: Bearish crossover ❌"
        else:
            return f"{symbol} {interval} → No trade ⚠️\nRSI: {rsi:.2f}\nMACD: Neutral"

    except Exception as e:
        return f"⚠️ Error: {e}"

# =======================
# Telegram Commands
# =======================
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "📊 Welcome to Forex Signal Bot!\nUse /signal to request live signals.")

@bot.message_handler(commands=["signal"])
def ask_signal(message):
    bot.reply_to(message, "📌 Choose a pair & timeframe:\nExample: EURUSD 1m")

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    try:
        parts = message.text.upper().split()
        if len(parts) != 2:
            bot.reply_to(message, "⚠️ Format: PAIR TIMEFRAME\nExample: EURUSD 1m")
            return

        pair, tf = parts
        symbol = pair + "=X" if not pair.endswith("=X") else pair
        interval = tf

        # Send signal
        signal = get_signal(symbol, interval)
        bot.reply_to(message, signal)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# =======================
# Run bot
# =======================
bot.polling(none_stop=True)
