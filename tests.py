import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
import pandas as pd

# Import functions to be tested
from bot import on_message, stream_kline

class TestTradingBot(unittest.TestCase):
    
    @patch('bot.websocket.WebSocketApp')
    @patch('bot.client.ticker')
    @patch('bot.send_message')
    @patch('bot.db.get_recent_market_data')
    @patch('bot.place_order')
    def test_on_message_sell_signal(self, mock_place_order, mock_get_recent_market_data, mock_send_message, mock_ticker, mock_websocket_app):
        # Mock WebSocket message
        message = {
            "k": {
                "x": True,
                "c": "69229.99"
            }
        }
        mock_get_recent_market_data.return_value = [{"close": 69000}] * 14  # Mock recent market data
        mock_ticker.return_value = {'price': '70600'}  # Mock ticker response
        mock_websocket_app.return_value = MagicMock()  # Mock WebSocketApp instance

        # Call on_message function
        on_message(None, json.dumps(message))

        # Assert sell signal message sent
        mock_send_message.assert_called_once_with("Sell signal triggered! RSI: 68.97 - LOG: - 2024-05-30 14:30:00")
        # Assert place_order called with expected parameters
        mock_place_order.assert_called_once_with('btcusdt', 'SELL', 0.01)

    @patch('bot.websocket.WebSocketApp')
    @patch('bot.client.ticker')
    @patch('bot.send_message')
    @patch('bot.db.get_recent_market_data')
    @patch('bot.place_order')
    def test_on_message_buy_signal(self, mock_place_order, mock_get_recent_market_data, mock_send_message, mock_ticker, mock_websocket_app):
        # Mock WebSocket message
        message = {
            "k": {
                "x": True,
                "c": "69229.99"
            }
        }
        mock_get_recent_market_data.return_value = [{"close": 70000}] * 14  # Mock recent market data
        mock_ticker.return_value = {'price': '70600'}  # Mock ticker response
        mock_websocket_app.return_value = MagicMock()  # Mock WebSocketApp instance

        # Call on_message function
        on_message(None, json.dumps(message))

        # Assert buy signal message sent
        mock_send_message.assert_called_once_with("Buy signal triggered! RSI: 42.86 - LOG: 2024-05-30 14:30:00")
        # Assert place_order called with expected parameters
        mock_place_order.assert_called_once_with('btcusdt', 'BUY', 0.01)

    @patch('bot.websocket.WebSocketApp')
    def test_stream_kline(self, mock_websocket_app):
        # Mock WebSocketApp instance
        mock_websocket_app.return_value = MagicMock()
        # Call stream_kline function
        stream_kline()
        # Assert WebSocketApp.run_forever called
        mock_websocket_app.return_value.run_forever.assert_called_once_with(reconnect=5)

if __name__ == '__main__':
    unittest.main()