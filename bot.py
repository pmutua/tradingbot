import logging
import threading
import time
import requests
import websocket
import json
import asyncio
import talib
import pandas as pd
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from binance.spot import Spot as Client
import telegram
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram import Update
import db


# Initialize the Binance client
binance_api_key = 'YOUR_BINANCE_API_KEY'
binance_api_secret = 'YOUR_BINANCE_API_SECRET'
client = Client(api_key=binance_api_key, api_secret=binance_api_secret)

# Telegram bot token
TELEGRAM_TOKEN = '6452060768:AAENP-ek2lcHgERTlVIb6dzrK6kg3oB1xMw'
CHAT_ID = 699510250
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Global variables to store trading limits and amount
trading_limit = 1000  # Default trading limit
trade_amount = 0.001  # Default trade amount
current_price = None  # Global variable to store the current price
market_data = []
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
trade_amount = 0.01  # Example trade amount
trading_limit = 1000  # Example trading limit
TRADING_PAIR = 'btcusdt' #BTCUSDT
# Function to fetch real-time price
def fetch_real_time_price(symbol):
    try:
        ticker = client.ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Function to place an order
def place_order(symbol, side, quantity, order_type='LIMIT', timeInForce='GTC', price=None):
    try:
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'timeInForce': timeInForce,
            'quantity': quantity
        }
        if price is not None:
            params['price'] = price
        # Construct the message with order details
        message = f"Order placed:\n\nSymbol: {symbol}\nSide: {side}\nQuantity: {quantity}\nOrder Type: {order_type}\nTime in Force: {timeInForce}\nPrice: {price if price else 'Market'}"
        print('ORDER==============')
        send_message(message)
        # When order placed record market data market data
        # update_database([new_row])
        # order = client.new_order(**params)
        # print(f"Order placed: {order}")
        # return order
    except Exception as e:
        print(f"An error occurred while placing the order: {e}")
        return None

# Function to handle incoming WebSocket messages
def on_message(ws, message):
    """Purpose of the Function
    TODO: Cache streamed data and do  bulk insert 
    ================================================================================================
    *Data Processing: To update the local market data with the latest kline information.
    *RSI Calculation: To calculate the Relative Strength Index (RSI) based on the updated market data.
    *Trade Decision: To make buy or sell decisions based on the RSI values and execute trades accordingly.
    """
    global current_price, market_data

    try:
        #==========================================================
        # Start Update streamed data to Database
        #===========================================================
        data = json.loads(message)  # Parse the message as JSON
        print()
        db.log_db(message)
        #==========================================================
        # End Database
        #===========================================================

        event_time = data['E']
        kline = data['k'] #candlestick
        
        is_kline_closed = kline['x']
        close_price = float(kline['c'])
        open_price = float(kline['o'])
        high_price = float(kline['h'])
        low_price = float(kline['l'])
        volume = float(kline['v'])

        # Set the current price to the close price of the current kline
        current_price = close_price

        if is_kline_closed:
            # Append new data to market_data
            # Append new data to market_data
            new_row = {
                'event_time': event_time,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            }
            market_data.append(new_row)
            print("==========================Append Data")

            if len(market_data) == RSI_PERIOD:
                # Trigger notification when 14 rows are reached
                message = "Notification: Sufficient data available for analysis. Ready to make trading decisions."
                send_message(message)
                #TODO: Clear local data
                # Now you have enough data to start making trading decisions based on RSI
                # Implement your trading logic here

            if len(market_data) > RSI_PERIOD:
                # Convert market_data to DataFrame
                df = pd.DataFrame(market_data)
                # Keep only the last RSI_PERIOD data points
                df = df.iloc[-RSI_PERIOD:]
                rsi = talib.RSI(df['close'].values, RSI_PERIOD)[-1]

                if rsi > RSI_OVERBOUGHT:
                    msg = f"Sell signal triggered! RSI: {rsi:.2f}"
                    send_message(msg)
                    logging.info(msg)
                    if trade_amount * current_price <= trading_limit:
                        place_order(TRADING_PAIR, 'SELL', trade_amount)
                    else:
                        msg = f"Trade amount exceeds trading limit. Current price: {current_price}, Trading limit: {trading_limit}"
                        logging.info(msg)
                elif rsi < RSI_OVERSOLD:
                    msg = f"Buy signal triggered! RSI: {rsi:.2f}"
                    send_message(msg)
                    logging.info(msg)
                    if trade_amount * current_price <= trading_limit:
                        place_order(TRADING_PAIR, 'BUY', trade_amount)
                    else:
                        msg = f"Trade amount exceeds trading limit. Current price: {current_price}, Trading limit: {trading_limit}"
                        logging.info(msg)
                        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")



# Function to start the WebSocket
def stream_kline():
    """
    Here, @kline_1m indicates that you are subscribing to 1-minute k-line data for the BTCUSDT trading pair.
    This means that each k-line represents the price movement over a 1-minute period.
    Therefore, the period for the k-line data is 1 minute. If you want to subscribe to k-line data for a different period, you can adjust the suffix in the URL accordingly.
    For example, @kline_5m would subscribe to 5-minute k-line data, @kline_1h would subscribe to 1-hour k-line data, and so on.

    NOTE: 
    In this case, with RSI_PERIOD = 14, it means that the RSI is calculated based on the closing prices of the last 14 periods. For example, if you are analyzing one-minute candlestick data, the RSI will be calculated based on the closing prices of the last 14 one-minute candlesticks. Similarly, if you are analyzing daily data, the RSI will be calculated based on the closing prices of the last 14 days.
    """
    websocket.enableTrace(True)
    # "wss://stream.binance.com:9443/ws/<CURRENCY>@kline_<INTERVAL>"
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@kline_1m",
                                on_open=on_open,
                                on_message=on_message,  # Run on_message in a separate asyncio event loop
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever(reconnect=5)

# Initialize the Telegram updater and dispatcher
app = Application.builder().token(TELEGRAM_TOKEN).build()


# Function to send a message to the Telegram bot
# Function to send a message to the Telegram bot
def send_message(text: str):
    try:
        # Construct the URL for sending the message
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

        # Set the message you want to send
        message_text = text

        # Set the parameters for the request
        params = {
            'chat_id': CHAT_ID,
            'text': message_text
        }

        # Send the message using a GET request
        response = requests.get(url, params=params)

        # Check if the message was sent successfully
        if response.status_code == 200:
            print('Message sent successfully!')
        else:
            print('Failed to send message. Status code:', response.status_code)
            print('Response:', response.text)
    except Exception as e:
        print(f"Error sending message: {e}")



# Command handler to start the bot
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Welcome to the Binance Trading Bot! Use /setlimit to set your trading limit.')

# Command handler to set trading limit
async def set_limit(update: Update, context: CallbackContext):
    global trading_limit
    try:
        limit = float(context.args[0])
        trading_limit = limit
        await update.message.reply_text(f'Trading limit set to {trading_limit} USD.')
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /setlimit <amount>')

# Command handler to set trade amount
async def set_amount(update: Update, context: CallbackContext):
    global trade_amount
    try:
        amount = float(context.args[0])
        trade_amount = amount
        await update.message.reply_text(f'Trade amount set to {trade_amount} units.')
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /setamount <amount>')

# Command handler to start trading
async def start_trading(update: Update, context: CallbackContext):
    await update.message.reply_text('Starting automated trading...')
    await automated_trading()  # Assuming automated_trading is async

# Add command handlers to the dispatcher
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setlimit", set_limit))
app.add_handler(CommandHandler("setamount", set_amount))
app.add_handler(CommandHandler("starttrading", start_trading))

# Automated trading function
async def automated_trading():
    # Start the WebSocket connection
    await stream_kline()

    # Ensure initial price is received before continuing
    while current_price is None:
        print("Waiting for initial price...")
        await asyncio.sleep(1)  # Use asyncio.sleep for async operations



if __name__ == "__main__":
    db.init_db()
    stream_kline()
    app.run_polling()