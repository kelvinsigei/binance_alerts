# Binance Crypto Price Monitor Telegram Bot

A Telegram bot that monitors cryptocurrency prices on Binance and sends notifications when there's a 3% price change within the last 5 minutes.

## Features

- Monitors crypto prices in real-time
- Sends alerts when price changes by 3% or more within 5 minutes
- Supports monitoring any cryptocurrency available on Binance
- Command interface to check current prices and change monitored cryptocurrency

## Setup

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory (copy from `.env.example`):
   ```
   cp .env.example .env
   ```
4. Fill in the required values in the `.env` file:
   - `TELEGRAM_BOT_TOKEN`: Get this by creating a new bot through [@BotFather](https://t.me/botfather) on Telegram
   - `BINANCE_API_KEY` and `BINANCE_API_SECRET`: Create these on [Binance](https://www.binance.com/en/my/settings/api-management)
   - `CHAT_ID`: Your Telegram chat ID (you can get this from [@userinfobot](https://t.me/userinfobot))
   - `CRYPTO_SYMBOL`: The symbol to monitor (default is BTCUSDT)

## Usage

Run the bot:
```
python bot.py
```

### Commands

- `/start` - Start the bot
- `/help` - Show help message with available commands
- `/price` - Get the current price of the monitored cryptocurrency
- `/monitor <symbol>` - Change the cryptocurrency being monitored (e.g., `/monitor ETHUSDT`)

## Notes

- The bot checks prices every 30 seconds
- Notifications have a 15-minute cooldown to prevent spam
- The bot requires read-only API access to Binance (no trading permissions needed) 