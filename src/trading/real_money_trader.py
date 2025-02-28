#!/usr/bin/env python3
"""
REAL MONEY TRADER - Trade with real money using cryptocurrency exchange APIs
WARNING: This uses REAL money! Only use if you understand the risks.
"""
import os
import logging
import time
from datetime import datetime
import json
import hmac
import hashlib
import base64
import requests
import uuid
from .base_trading_game import BaseTradingGame

logger = logging.getLogger(__name__)

class RealMoneyTrader(BaseTradingGame):
    """Trading with real money using exchange APIs"""
    
    def __init__(self, starting_balance=100, api_key=None, api_secret=None, api_passphrase=None, exchange="dryrun"):
        """
        Initialize the real money trader
        
        Parameters:
        - starting_balance: Initial balance to track performance (not actual trading amount)
        - api_key: Exchange API key
        - api_secret: Exchange API secret
        - api_passphrase: Exchange API passphrase (needed for some exchanges like Coinbase Advanced)
        - exchange: Exchange to use ("dryrun", "coinbase", "binance", etc.)
        """
        # Always use real prices with real money
        super().__init__(starting_balance, use_real_prices=True)
        
        self.exchange = exchange.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        
        # Exchange-specific settings
        self.exchange_settings = {
            "coinbase": {
                "api_url": "https://api.exchange.coinbase.com",
                "product_id": "BTC-USD",
                "tick_size": 0.01,  # Minimum price increment
                "min_order_size": 0.0001  # Minimum BTC amount
            },
            "binance": {
                "api_url": "https://api.binance.com",
                "symbol": "BTCUSDT",
                "tick_size": 0.01,
                "min_order_size": 0.0001
            }
        }
        
        # If no API credentials, force into dry run mode
        if not api_key or not api_secret:
            self.exchange = "dryrun"
            logger.warning("No API credentials provided. Running in dry run mode.")
        
        # Set up exchange handler and check connection
        if self.setup_exchange():
            # Get actual account balances if connected successfully
            self.refresh_balances()
        
        logger.info(f"Trading on {self.exchange} exchange with BTC")
        logger.info(f"Starting with ${self.balance:.2f} USD and {self.btc_holdings:.8f} BTC")
        logger.info(f"Total portfolio value: ${self.balance + (self.btc_holdings * self.current_price):.2f}")
    
    def setup_exchange(self):
        """Set up the exchange API handler"""
        if self.exchange == "dryrun":
            logger.warning("🧪 RUNNING IN DRY RUN MODE - No real trading will occur")
            return True
            
        elif self.exchange == "coinbase":
            logger.info("🏛️ Using Coinbase Advanced Trade API")
            # Verify API credentials format
            if not self.api_key or not self.api_secret:
                logger.error("❌ Missing API credentials for Coinbase")
                self.exchange = "dryrun"
                return False
                
            # Test API connection
            try:
                self.test_exchange_connection()
            except Exception as e:
                logger.error(f"❌ Could not connect to Coinbase: {e}")
                self.exchange = "dryrun"
                return False
        
        elif self.exchange == "binance":












































































                raise ConnectionError(f"Could not authenticate with Coinbase: {response.text}")            if response.status_code != 200:            response = requests.get(url, headers=headers)            }                'CB-ACCESS-PASSPHRASE': self.api_passphrase                'CB-ACCESS-TIMESTAMP': timestamp,                'CB-ACCESS-SIGN': signature_b64,                'CB-ACCESS-KEY': self.api_key,            headers = {                        signature_b64 = base64.b64encode(signature).decode('utf-8')            ).digest()                hashlib.sha256                message.encode('utf-8'),                base64.b64decode(self.api_secret),            signature = hmac.new(            message = timestamp + 'GET' + '/accounts'            timestamp = str(time.time())            url = f"{self.exchange_settings['coinbase']['api_url']}/accounts"            # Test authenticated endpoint                            raise ConnectionError(f"Could not connect to Coinbase: {response.text}")            if response.status_code != 200:            response = requests.get(url)            url = f"{self.exchange_settings['coinbase']['api_url']}/time"            # Coinbase time endpoint doesn't require authentication        elif self.exchange == "coinbase":                        raise ConnectionError(f"Could not authenticate with Binance: {response.text}")            if response.status_code != 200:            response = requests.get(f"{url}?{query_string}&signature={signature}", headers=headers)            }                'X-MBX-APIKEY': self.api_key            headers = {                        ).hexdigest()                hashlib.sha256                query_string.encode('utf-8'),                self.api_secret.encode('utf-8'),            signature = hmac.new(            query_string = f"timestamp={timestamp}"            timestamp = int(time.time() * 1000)            url = "https://api.binance.com/api/v3/account"            # Test authenticated endpoint                            raise ConnectionError(f"Could not connect to Binance: {response.text}")            if response.status_code != 200:            response = requests.get(url)            url = "https://api.binance.com/api/v3/ping"            # Binance ping endpoint doesn't require authentication        if self.exchange == "binance":        """Test connection to the exchange"""    def test_exchange_connection(self):            return True                    return False            self.exchange = "dryrun"            logger.warning("🧪 Falling back to dry run mode")            logger.error(f"❌ Unsupported exchange: {self.exchange}")        else:                        return False                self.exchange = "dryrun"                logger.error(f"❌ Could not connect to Binance: {e}")            except Exception as e:                self.test_exchange_connection()            try:            # Test API connection                                return False                self.exchange = "dryrun"                logger.error("❌ Missing API credentials for Binance")            if not self.api_key or not self.api_secret:            # Verify API credentials format            logger.info("🏛️ Using Binance exchange API")        