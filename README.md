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
- `/price <symbol>` - Get the current price of the monitored cryptocurrency
- `/list <page>` - Show all monitored cryptocurrencies (paginated)
- `/add <symbol>` - Add a cryptocurrency to monitor
- `/remove <symbol>` - Stop monitoring a cryptocurrency

## Notes

- The bot checks prices every 30 seconds
- Notifications have a 15-minute cooldown to prevent spam
- The bot requires read-only API access to Binance (no trading permissions needed)

## Deployment to Railway

### Prerequisites
1. A Railway account (sign up at [railway.app](https://railway.app))
2. Git installed on your computer
3. Your Telegram bot token and Binance API credentials

### Steps to Deploy

1. Create a new project in Railway:
   - Go to [railway.app](https://railway.app) and log in
   - Click "New Project" and select "Deploy from GitHub repo"

2. Connect your GitHub repository:
   - Push this code to a GitHub repository
   - Select your repository in Railway

3. Add environment variables:
   - In your Railway project, go to the "Variables" tab
   - Add the following variables:
     - `TELEGRAM_BOT_TOKEN`
     - `BINANCE_API_KEY`
     - `BINANCE_API_SECRET`
     - `CHAT_ID`

4. Deploy:
   - Railway will automatically detect your Procfile and deploy your bot
   - The bot should start running automatically

5. Monitor:
   - You can view the logs in the Railway dashboard to ensure your bot is running properly

### Keeping the Bot Running

Railway's free tier should allow your bot to run 24/7, but with some monthly usage limits. For continuous operation, consider upgrading to a paid plan if needed. 