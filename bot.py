import os
import time
import logging
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables or .env file
# This makes it compatible with Railway.app and local development
config = {}

# First try to load from environment variables (for Railway)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
CHAT_ID = os.environ.get('CHAT_ID')

# If any of these are missing, try to load from .env file (for local development)
if not all([TELEGRAM_BOT_TOKEN, BINANCE_API_KEY, BINANCE_API_SECRET, CHAT_ID]):
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
        
        # Get configuration values from .env file if not already set
        TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN or config.get('TELEGRAM_BOT_TOKEN')
        BINANCE_API_KEY = BINANCE_API_KEY or config.get('BINANCE_API_KEY')
        BINANCE_API_SECRET = BINANCE_API_SECRET or config.get('BINANCE_API_SECRET')
        CHAT_ID = CHAT_ID or config.get('CHAT_ID')
    except Exception as e:
        logger.error(f"Error reading .env file: {str(e)}")

# Initialize Binance client
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Initialize data storage - now with multiple symbols
price_history = {}
last_notification_time = {}
monitored_symbols = []

def load_symbols():
    """Load symbols to monitor"""
    global monitored_symbols
    try:
        # Get all Binance USDT trading pairs
        exchange_info = binance_client.get_exchange_info()
        all_usdt_symbols = [symbol['symbol'] for symbol in exchange_info['symbols'] 
                           if symbol['symbol'].endswith('USDT') and symbol['status'] == 'TRADING']
        
        # Use all USDT trading pairs instead of just top 20
        monitored_symbols = all_usdt_symbols
        
        logger.info(f"Monitoring all {len(monitored_symbols)} USDT trading pairs")
        return True
    except Exception as e:
        logger.error(f"Error loading symbols: {str(e)}")
        # Fallback to BTC if we can't get the list
        monitored_symbols = ['BTCUSDT']
        return False

def start(update, context):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(f'Hi {user.first_name}! I am monitoring {len(monitored_symbols)} cryptocurrencies.')

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Available commands:\n'
                             '/start - Start the bot\n'
                             '/price <symbol> - Get current price (e.g., /price BTCUSDT)\n'
                             '/list - Show all monitored cryptocurrencies\n'
                             '/add <symbol> - Add a cryptocurrency to monitor\n'
                             '/remove <symbol> - Stop monitoring a cryptocurrency\n'
                             '/help - Show this help message')

def price_command(update, context):
    """Send current price when the command /price is issued."""
    if context.args:
        symbol = context.args[0].upper()
    else:
        # Default to BTC if no symbol provided
        symbol = 'BTCUSDT'
        
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        # Format price with appropriate decimal places based on magnitude
        if current_price < 0.0001:
            price_str = f"${current_price:.8f}"
        elif current_price < 0.01:
            price_str = f"${current_price:.6f}"
        elif current_price < 1:
            price_str = f"${current_price:.4f}"
        else:
            price_str = f"${current_price:.2f}"
            
        update.message.reply_text(f'Current *{symbol}* price: {price_str}', parse_mode='Markdown')
    except BinanceAPIException as e:
        update.message.reply_text(f'Error fetching price: {str(e)}')

def list_command(update, context):
    """List all monitored cryptocurrencies."""
    if not monitored_symbols:
        update.message.reply_text('No cryptocurrencies are being monitored.')
        return
    
    total_pairs = len(monitored_symbols)
    
    # Check if arguments provided for pagination
    page = 1
    page_size = 20
    
    if context.args:
        try:
            page = int(context.args[0])
            if page < 1:
                page = 1
        except ValueError:
            pass
    
    # Calculate start and end indices for the current page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_pairs)
    
    # Get the subset of symbols for this page
    if start_idx >= total_pairs:
        update.message.reply_text(f"Invalid page number. Max page is {(total_pairs // page_size) + 1}")
        return
    
    current_page_symbols = monitored_symbols[start_idx:end_idx]
    
    # Construct the message
    symbols_text = f"Monitoring {total_pairs} cryptocurrencies (Page {page}/{(total_pairs // page_size) + 1}):\n"
    for symbol in current_page_symbols:
        symbols_text += f"• {symbol}\n"
    
    symbols_text += f"\nUse /list <page_number> to view more pairs"
    update.message.reply_text(symbols_text)

def add_command(update, context):
    """Add a cryptocurrency to monitor."""
    if not context.args:
        update.message.reply_text('Please specify a symbol to add (e.g., /add ETHUSDT)')
        return
        
    symbol = context.args[0].upper()
    
    # Check if already monitoring
    if symbol in monitored_symbols:
        update.message.reply_text(f'Already monitoring {symbol}')
        return
        
    # Verify the symbol exists on Binance
    try:
        binance_client.get_symbol_ticker(symbol=symbol)
        monitored_symbols.append(symbol)
        update.message.reply_text(f'Now monitoring {symbol}')
    except BinanceAPIException:
        update.message.reply_text(f'Invalid symbol: {symbol}')

def remove_command(update, context):
    """Remove a cryptocurrency from monitoring."""
    if not context.args:
        update.message.reply_text('Please specify a symbol to remove (e.g., /remove ETHUSDT)')
        return
        
    symbol = context.args[0].upper()
    
    if symbol in monitored_symbols:
        monitored_symbols.remove(symbol)
        # Clean up any stored data
        if symbol in price_history:
            del price_history[symbol]
        if symbol in last_notification_time:
            del last_notification_time[symbol]
        update.message.reply_text(f'Stopped monitoring {symbol}')
    else:
        update.message.reply_text(f'Not monitoring {symbol}')

def check_price_changes():
    """Check significant price changes for all monitored symbols."""
    current_time = datetime.now()
    
    # Log the number of symbols being monitored every 10 minutes
    if current_time.minute % 10 == 0 and current_time.second < 30:
        logger.info(f"Currently monitoring {len(monitored_symbols)} cryptocurrency pairs")
    
    # Process symbols in chunks to avoid rate limiting
    chunk_size = 100
    for i in range(0, len(monitored_symbols), chunk_size):
        chunk = monitored_symbols[i:i+chunk_size]
        
        # Get all prices in one API call if possible
        try:
            all_tickers = binance_client.get_symbol_ticker()
            price_dict = {ticker['symbol']: float(ticker['price']) for ticker in all_tickers}
        except Exception as e:
            logger.error(f"Error fetching all tickers: {str(e)}")
            # Fallback to individual requests if bulk request fails
            price_dict = {}
            # Add a longer delay to recover from potential connection issues
            time.sleep(5)
        
        for symbol in chunk:
            try:
                # Get current price (either from bulk request or individual)
                if symbol in price_dict:
                    current_price = price_dict[symbol]
                else:
                    try:
                        ticker = binance_client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                    except Exception as e:
                        logger.error(f"Error fetching price for {symbol}: {str(e)}")
                        continue  # Skip this symbol and move to the next one
                
                # Initialize if first time seeing this symbol
                if symbol not in price_history:
                    price_history[symbol] = {}
                    
                # Add current price to history
                price_history[symbol][current_time] = current_price
                
                # Remove prices older than 5 minutes
                cutoff_time = current_time - timedelta(minutes=5)
                old_times = [t for t in price_history[symbol] if t < cutoff_time]
                for t in old_times:
                    del price_history[symbol][t]
                
                # If we have price history to compare for this symbol
                if len(price_history[symbol]) > 1:
                    # Get the oldest price in our 5-minute window
                    oldest_time = min(price_history[symbol].keys())
                    oldest_price = price_history[symbol][oldest_time]
                    
                    # Calculate percentage change
                    price_change_pct = ((current_price - oldest_price) / oldest_price) * 100
                    
                    # Check if significant change (3% or more)
                    if abs(price_change_pct) >= 3.0:
                        # Check if we've already sent a notification in the last 15 minutes
                        last_time = last_notification_time.get(symbol)
                        if not last_time or (current_time - last_time) > timedelta(minutes=15):
                            # Format prices with appropriate decimal places based on price magnitude
                            def format_price(price):
                                if price < 0.0001:
                                    return f"${price:.8f}"
                                elif price < 0.01:
                                    return f"${price:.6f}"
                                elif price < 1:
                                    return f"${price:.4f}"
                                else:
                                    return f"${price:.2f}"
                                
                            # Different emoji and direction text based on increase or decrease
                            if price_change_pct > 0:
                                emoji = "🚀"  # Rocket for price increase
                                direction = "increased"
                            else:
                                emoji = "📉"  # Chart down for price decrease
                                direction = "decreased"
                                
                            # Make symbol bold using Telegram markdown
                            bold_symbol = f"*{symbol}*"
                            
                            # Create notification message with improved formatting
                            message = (
                                f"{emoji} {bold_symbol} price has {direction} by {abs(price_change_pct):.2f}% "
                                f"in the last {(current_time - oldest_time).seconds // 60} minutes!\n"
                                f"Current price: {format_price(current_price)}\n"
                                f"Previous price: {format_price(oldest_price)}"
                            )
                            
                            # Send to Telegram with markdown parsing
                            try:
                                updater.bot.send_message(
                                    chat_id=CHAT_ID, 
                                    text=message, 
                                    parse_mode='Markdown'
                                )
                                
                                # Update last notification time only if message was sent successfully
                                last_notification_time[symbol] = current_time
                                
                                logger.info(f"Notification sent for {symbol}: {price_change_pct:.2f}% change")
                            except Exception as e:
                                logger.error(f"Failed to send Telegram notification: {str(e)}")
                
                # Only log prices for main cryptocurrencies and limit frequency
                if symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'] and current_time.second < 10:
                    # Format price with appropriate decimal places
                    if current_price < 0.01:
                        price_str = f"${current_price:.6f}"
                    else:
                        price_str = f"${current_price:.2f}"
                    logger.info(f"Current {symbol} price: {price_str}")
                    
            except BinanceAPIException as e:
                if "Too much request weight" in str(e):
                    logger.warning(f"Rate limit reached, pausing for a moment")
                    time.sleep(5)  # Sleep to respect rate limits
                else:
                    logger.error(f"Binance API error for {symbol}: {str(e)}")
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {str(e)}")
        
        # Small delay between chunks to avoid rate limiting
        time.sleep(0.5)

def main():
    """Start the bot."""
    # First load the symbols to monitor
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            success = load_symbols()
            if success:
                break
        except Exception as e:
            logger.error(f"Error initializing (attempt {retry_count+1}/{max_retries}): {str(e)}")
        
        retry_count += 1
        time.sleep(10)  # Wait before retrying
    
    if retry_count == max_retries:
        logger.warning("Could not load symbols after multiple attempts. Using default (BTCUSDT only)")
        monitored_symbols.append('BTCUSDT')
    
    # Create the Updater and pass it your bot's token
    global updater
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("price", price_command))
    dispatcher.add_handler(CommandHandler("list", list_command))
    dispatcher.add_handler(CommandHandler("add", add_command))
    dispatcher.add_handler(CommandHandler("remove", remove_command))

    # Start the Bot
    updater.start_polling(drop_pending_updates=True)
    
    # Set up the price monitoring loop
    logger.info(f"Bot started, monitoring {len(monitored_symbols)} cryptocurrencies")
    
    # Main loop with error handling for 24/7 operation
    while True:
        try:
            check_price_changes()
            time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logger.info("Bot stopping due to keyboard interrupt...")
            updater.stop()
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {str(e)}")
            # Don't exit on error, just wait and try again
            time.sleep(60)  # Wait longer after an error

if __name__ == '__main__':
    main() 