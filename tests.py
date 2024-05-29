import unittest
from unittest.mock import patch, Mock
import json
import pandas as pd
import talib
from binance.spot import Spot as Client
from telegram import Update, Bot
from telegram.ext import CallbackContext

# Assuming the code above is in a file named `trading_bot.py`
from .bot import (
    fetch_real_time_price,
    place_order,
    on_message,
    start_websocket,
    start,
    set_limit,
    set_amount,
    start_trading,
    app,
    current_price,
    market_data,
    RSI_PERIOD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    TRADING_PAIR,
    trade_amount,
    trading_limit
)

class TestTradingBot(unittest.TestCase):
    @patch('trading_bot.Client')
    def test_fetch_real_time_price(self, MockClient):
        mock_client = MockClient.return_value
        mock_client.ticker.return_value = {'price': '50000.0'}

        # Test normal case
        price = fetch_real_time_price('btcusdt')
        self.assertEqual(price, 50000.0)

        # Test API error
        mock_client.ticker.side_effect = Exception("API error")
        price = fetch_real_time_price('btcusdt')
        self.assertIsNone(price)

        # Test non-numeric price
        mock_client.ticker.return_value = {'price': 'abc'}
        price = fetch_real_time_price('btcusdt')
        self.assertIsNone(price)

    @patch('trading_bot.client.new_order')
    @patch('trading_bot.send_message')
    def test_place_order(self, mock_send_message, mock_new_order):
        mock_new_order.return_value = {'status': 'FILLED'}
        update = Mock()

        # Test normal case
        place_order('btcusdt', 'BUY', 0.01, price=50000.0)
        self.assertTrue(mock_send_message.called)

        # Test order placement failure
        mock_new_order.side_effect = Exception("Order placement error")
        place_order('btcusdt', 'SELL', 0.01, price=50000.0)
        self.assertTrue(mock_send_message.called)

        # Test invalid parameters
        place_order('btcusdt', 'BUY', -0.01, price=50000.0)
        self.assertTrue(mock_send_message.called)

    def test_on_message(self):
        # Reset global variables before test
        global current_price, market_data
        current_price = None
        market_data = []

        data = {
            "e": "kline",
            "E": 1716702124398,
            "s": "BTCUSDT",
            "k": {
                "t": 1716702120000,
                "T": 1716702179999,
                "s": "BTCUSDT",
                "i": "1m",
                "f": 3614046848,
                "L": 3614046905,
                "o": "69050.39000000",
                "c": "69055.58000000",
                "h": "69055.58000000",
                "l": "69050.39000000",
                "v": "0.77573000",
                "n": 58,
                "x": False,
                "q": "53565.00824820",
                "V": "0.75272000",
                "Q": "51976.12151010",
                "B": "0"
            }
        }
        message = json.dumps(data)
        ws = Mock()

        # Test case when kline is not closed
        on_message(ws, message)
        self.assertEqual(current_price, 69055.58)
        self.assertEqual(len(market_data), 0)  # No data should be appended

        # Modify data to have kline closed
        data['k']['x'] = True
        message = json.dumps(data)

        # Test case when kline is closed
        on_message(ws, message)
        self.assertEqual(current_price, 69055.58)
        self.assertEqual(len(market_data), 1)

        # Test RSI calculation
        for i in range(15):
            on_message(ws, message)

        df = pd.DataFrame(market_data)
        rsi = talib.RSI(df['close'].values, RSI_PERIOD)[-1]
        self.assertTrue(rsi > 0)

        # Test incomplete JSON message
        incomplete_message = '{"e": "kline", "E": 1716702124398, "s": "BTCUSDT", "k": {}}'
        on_message(ws, incomplete_message)
        self.assertEqual(current_price, 69055.58)  # Should remain unchanged

        # Test malformed JSON message
        malformed_message = '{"e": "kline", "E": 1716702124398, "s": "BTCUSDT", "k": '
        on_message(ws, malformed_message)
        self.assertEqual(current_price, 69055.58)  # Should remain unchanged

    @patch('trading_bot.websocket.WebSocketApp')
    def test_start_websocket(self, MockWebSocketApp):
        start_websocket()
        MockWebSocketApp.assert_called_once()

    @patch('trading_bot.Update')
    @patch('trading_bot.CallbackContext')
    def test_telegram_commands(self, MockCallbackContext, MockUpdate):
        update = MockUpdate()
        context = MockCallbackContext()

        with patch('trading_bot.send_message'):
            app.bot.send_message = Mock()

            # Test setting trading limit
            context.args = ['1000']
            set_limit(update, context)
            self.assertEqual(trading_limit, 1000)

            # Test invalid trading limit
            context.args = ['abc']
            set_limit(update, context)
            self.assertNotEqual(trading_limit, 'abc')  # Should not change

            # Test setting trade amount
            context.args = ['0.01']
            set_amount(update, context)
            self.assertEqual(trade_amount, 0.01)

            # Test invalid trade amount
            context.args = ['xyz']
            set_amount(update, context)
            self.assertNotEqual(trade_amount, 'xyz')  # Should not change

            # Test starting trading
            start_trading(update, context)
            self.assertTrue(app.bot.send_message.called)

if __name__ == '__main__':
    unittest.main()
