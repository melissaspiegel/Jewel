#!/usr/bin/env python3
"""
Exchange Handler for Live Trading
Connects to cryptocurrency exchanges using CCXT library
"""
import os
import json
import logging
import ccxt
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/exchange_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

class ExchangeHandler:
    """Handles all exchange communication for live trading"""
    
    def __init__(self, config_path="config/config.json"):
        """Initialize the exchange handler with config"""
        self.config_path = config_path
        self.config = self._load_config()
        self.exchange = self._initialize_exchange()
        self.trading_enabled = self.config["risk_management"]["trading_enabled"]
        self.paper_trading = self.config["advanced"]["paper_trading_mode"]
        
        # Show critical warnings if live trading is enabled
        if self.trading_enabled and not self.paper_trading:
            logger.warning("⚠️ LIVE TRADING MODE ENABLED - REAL MONEY WILL BE USED ⚠️")
            logger.warning("⚠️ TRADING CRYPTOCURRENCY INVOLVES SIGNIFICANT RISK OF LOSS ⚠️")
            
        elif self.paper_trading:
            logger.info("🧪 Paper trading mode enabled - no real money will be used")
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _initialize_exchange(self):
        """Initialize exchange connection using CCXT"""
        exchange_id = self.config["api_keys"]["exchange_name"].lower()
        
        try:
            # Check if exchange is supported by ccxt
            if not hasattr(ccxt, exchange_id):
                logger.error(f"Exchange {exchange_id} is not supported by CCXT")
                raise ValueError(f"Unsupported exchange: {exchange_id}")
            
            # Create exchange instance
            exchange_class = getattr(ccxt, exchange_id)
            
            # Configure with API credentials
            exchange = exchange_class({
                'apiKey': self.config["api_keys"]["api_key"],
                'secret': self.config["api_keys"]["api_secret"],
                'enableRateLimit': True,
            })
            
            logger.info(f"Successfully initialized connection to {exchange_id}")
            
            # Test connection
            if not self.config["advanced"]["paper_trading_mode"]:
                markets = exchange.load_markets()
                logger.info(f"Connected to {exchange_id}, found {len(markets)} markets")
                
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange {exchange_id}: {e}")
            if "Invalid API key" in str(e):
                logger.error("Please check your API key and secret in config.json")
            raise
    
    def get_balance(self, currency='USDT'):
        """Get account balance for a specific currency"""
        try:
            if self.paper_trading:
                # Return simulated balance from config
                return self.config["trading"]["starting_balance"]
            
            # Get real balance from exchange
            balance = self.exchange.fetch_balance()
            return balance['total'].get(currency, 0)
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0
    
    def get_ticker(self, symbol='BTC/USDT'):
        """Get current ticker data for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.debug(f"Got ticker for {symbol}: {ticker['last']}")
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def place_market_buy(self, symbol, amount):
        """Place a market buy order"""
        if not self.trading_enabled:
            logger.warning("Trading is disabled in config. Not placing buy order.")
            return {"id": "simulation", "status": "simulated", "amount": amount}
            
        try:
            if self.paper_trading:
                ticker = self.get_ticker(symbol)
                price = ticker['last'] if ticker else 0
                logger.info(f"PAPER TRADE - BUY {amount} {symbol} at {price}")
                return {"id": "paper_trade", "status": "filled", "amount": amount, "price": price}
            
            # Place actual order on the exchange
            order = self.exchange.create_market_buy_order(symbol, amount)
            logger.info(f"MARKET BUY: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing market buy: {e}")
            return None
    
    def place_market_sell(self, symbol, amount):
        """Place a market sell order"""
        if not self.trading_enabled:
            logger.warning("Trading is disabled in config. Not placing sell order.")
            return {"id": "simulation", "status": "simulated", "amount": amount}
            
        try:
            if self.paper_trading:
                ticker = self.get_ticker(symbol)
                price = ticker['last'] if ticker else 0
                logger.info(f"PAPER TRADE - SELL {amount} {symbol} at {price}")
                return {"id": "paper_trade", "status": "filled", "amount": amount, "price": price}
            
            # Place actual order on the exchange
            order = self.exchange.create_market_sell_order(symbol, amount)
            logger.info(f"MARKET SELL: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing market sell: {e}")
            return None
    
    def get_ohlcv(self, symbol='BTC/USDT', timeframe='1m', limit=100):
        """Get OHLCV data for a symbol"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return []
    
    def get_account_info(self):
        """Get account information"""
        try:
            if self.paper_trading:
                return {"paper_trading": True, "balance": self.config["trading"]["starting_balance"]}
            
            return self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return {}
