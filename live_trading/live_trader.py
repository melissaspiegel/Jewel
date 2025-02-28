#!/usr/bin/env python3
"""
Live Trading Implementation for Micro Strategy
USE EXTREME CAUTION - THIS CAN TRADE WITH REAL MONEY

IMPORTANT: 
- This is provided for educational purposes only
- Start with paper trading mode enabled in config.json
- Trading cryptocurrency involves significant risk of financial loss
- Use at your own risk
"""
import os
import sys
import time
import json
import logging
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime, timedelta
import argparse
import traceback
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/live_trader_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Fix path for importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.strategies.micro_strategy import MicroStrategy
from exchange_handler import ExchangeHandler

class LiveTrader:
    """Live trading implementation of the MicroStrategy"""
    
    def __init__(self, config_path="config/config.json"):
        """Initialize live trader with config"""
        self.config_path = config_path
        self.config = self._load_config()
        self.exchange = ExchangeHandler(config_path)
        self.trading_pair = self.config["advanced"]["trading_pairs"][0]
        self.check_interval = self.config["advanced"]["check_interval_seconds"]
        self.paper_trading = self.config["advanced"]["paper_trading_mode"]
        self.trading_enabled = self.config["risk_management"]["trading_enabled"]
        
        # Performance tracking
        self.start_balance = self.exchange.get_balance()
        self.current_balance = self.start_balance
        self.trades_today = 0
        self.max_daily_trades = self.config["risk_management"]["max_daily_trades"]
        
        # Strategy setup
        self.price_data = self._initialize_price_data()
        self.strategy_params = {
            "fast_ma_period": 4,
            "slow_ma_period": 12,
            "rsi_period": 10,
            "macd_fast": 8,
            "macd_slow": 18,
            "macd_signal": 5,
            "bollinger_period": 15,
            "bollinger_stddev": 1.8
        }
        
        # Initialize strategy
        self.strategy = MicroStrategy(
            self.strategy_params,
            self.price_data,
            balance=self.current_balance,
            btc_holdings=0,
            fee=self.config["trading"]["fee_percentage"] / 100
        )
        
        # Important warnings
        self._display_warnings()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _display_warnings(self):
        """Display important warnings and confirmations"""
        logger.info("=" * 80)
        logger.info("LIVE TRADING SYSTEM - INITIALIZATION")
        logger.info("=" * 80)
        
        if not self.paper_trading and self.trading_enabled:
            logger.warning("‼️ WARNING: LIVE TRADING WITH REAL MONEY IS ENABLED ‼️")
            logger.warning("‼️ SIGNIFICANT RISK OF FINANCIAL LOSS ‼️")
            logger.warning("=" * 80)
            
            # Add extra confirmation step
            user_confirm = input("Type 'CONFIRM' to proceed with REAL trading, or anything else to use paper trading: ")
            if user_confirm != "CONFIRM":
                logger.info("Switching to paper trading mode")
                self.paper_trading = True
                self.config["advanced"]["paper_trading_mode"] = True
                # Save the updated config
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
        
        mode = "PAPER TRADING (no real money)" if self.paper_trading else "LIVE TRADING (REAL MONEY)"
        logger.info(f"Running in {mode} mode")
        logger.info(f"Trading pair: {self.trading_pair}")
        logger.info(f"Starting balance: {self.current_balance}")
        logger.info(f"Checking market every {self.check_interval} seconds")
        logger.info(f"Max daily trades: {self.max_daily_trades}")
        
        take_profit = self.config["trading"]["take_profit_percentage"]
        stop_loss = self.config["trading"]["stop_loss_percentage"]
        logger.info(f"Take profit: {take_profit}% | Stop loss: {stop_loss}%")
        logger.info("=" * 80)
    
    def _initialize_price_data(self):
        """Get initial historical price data"""
        logger.info(f"Initializing price data for {self.trading_pair}")
        try:
            # Get OHLCV data from exchange
            ohlcv = self.exchange.get_ohlcv(
                symbol=self.trading_pair,
                timeframe='1m',  
                limit=200  # Get last 200 candles
            )
            
            if not ohlcv or len(ohlcv) < 100:
                logger.error(f"Insufficient historical data: {len(ohlcv)} candles")
                raise ValueError("Not enough historical data to start trading")
                
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            logger.info(f"Loaded {len(df)} historical price candles")
            return df
            
        except Exception as e:
            logger.error(f"Error initializing price data: {e}")
            raise
    
    def update_price_data(self):
        """Update price data with latest candle"""
        try:
            # Get latest OHLCV candle
            latest_ohlcv = self.exchange.get_ohlcv(
                symbol=self.trading_pair,
                timeframe='1m',
                limit=1
            )
            
            if not latest_ohlcv or len(latest_ohlcv) == 0:
                logger.warning("No new price data received")
                return
            
            # Convert to DataFrame row
            latest = pd.DataFrame([latest_ohlcv[0]], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            latest['datetime'] = pd.to_datetime(latest['timestamp'], unit='ms')
            
            # Check if this is a new candle or updating existing one
            if len(self.price_data) > 0 and latest['timestamp'].iloc[0] == self.price_data['timestamp'].iloc[-1]:
                # Update last row
                self.price_data.iloc[-1] = latest.iloc[0]
            else:
                # Add new row
                self.price_data = pd.concat([self.price_data, latest])
            
            # Keep dataframe at manageable size
            if len(self.price_data) > 300:
                self.price_data = self.price_data.iloc[-300:]
                
            return self.price_data.iloc[-1]["close"]
            
        except Exception as e:
            logger.error(f"Error updating price data: {e}")
            return None
    
    def _check_risk_limits(self):
        """Check if we've exceeded our risk limits"""
        # Check if we've exceeded max trades for the day
        if self.trades_today >= self.max_daily_trades:
            logger.warning(f"Reached maximum daily trades: {self.trades_today}/{self.max_daily_trades}")
            return False
            
        # Check if we've exceeded max daily drawdown
        starting_balance = self.start_balance
        current_balance = self.exchange.get_balance()
        daily_change_pct = ((current_balance / starting_balance) - 1) * 100
        
        max_drawdown = -abs(self.config["risk_management"]["max_daily_drawdown_percent"])
        if daily_change_pct <= max_drawdown:
            logger.warning(f"Exceeded max daily drawdown: {daily_change_pct:.2f}% (limit: {max_drawdown}%)")
            return False
            
        return True
    
    def run_trading_loop(self):
        """Main trading loop"""
        logger.info("Starting trading loop")
        
        try:
            while True:
                # Check if we should still be trading based on risk limits
                if not self._check_risk_limits():
                    logger.warning("Risk limits exceeded. Pausing trading.")
                    time.sleep(300)  # Wait 5 minutes before checking again
                    continue
                
                # Get latest price
                current_price = self.update_price_data()
                if not current_price:
                    logger.warning("Could not get current price. Skipping cycle.")
                    time.sleep(self.check_interval)
                    continue
                
                logger.info(f"Current {self.trading_pair} price: ${current_price:.2f}")
                
                # Update strategy with new price data
                self.strategy.data = self.price_data.copy()
                self.strategy.populate_indicators()
                self.strategy.populate_signals()
                
                # Get trading signals
                latest_row = self.strategy.data.iloc[-1]
                buy_signal = latest_row.get("open_long", False)
                sell_signal = latest_row.get("close_long", False)
                
                # Execute trades based on signals
                if self.strategy.btc_holdings > 0 and sell_signal:
                    self._execute_sell(current_price)
                    
                elif self.strategy.balance > 10 and buy_signal:
                    self._execute_buy(current_price)
                
                # Wait for next check interval
                logger.info(f"Waiting {self.check_interval} seconds until next check")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping trading loop - user interrupt")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            logger.error(traceback.format_exc())
    
    def _execute_buy(self, price):
        """Execute a buy order"""
        if not self.trading_enabled:
            logger.info(f"BUY SIGNAL at ${price:.2f} (Trading disabled)")
            return
            
        symbol = self.trading_pair
        trade_amount_usd = self.strategy.balance * 0.95  # Use 95% of balance
        
        # Calculate the amount of crypto to buy
        crypto_amount = trade_amount_usd / price
        
        logger.info(f"BUY SIGNAL: {crypto_amount:.8f} {symbol} at ${price:.2f}")
        
        try:
            # Place the order through the exchange handler
            order = self.exchange.place_market_buy(symbol, crypto_amount)
            
            if order:
                # Update strategy state
                self.strategy.buy_position(price)
                self.trades_today += 1
                logger.info(f"Buy order executed: {order}")
            else:
                logger.error("Failed to execute buy order")
                
        except Exception as e:
            logger.error(f"Error executing buy: {e}")
    
    def _execute_sell(self, price):
        """Execute a sell order"""
        if not self.trading_enabled:
            logger.info(f"SELL SIGNAL at ${price:.2f} (Trading disabled)")
            return
            
        symbol = self.trading_pair
        crypto_amount = self.strategy.btc_holdings
        
        logger.info(f"SELL SIGNAL: {crypto_amount:.8f} {symbol} at ${price:.2f}")
        
        try:
            # Place the order through the exchange handler
            order = self.exchange.place_market_sell(symbol, crypto_amount)
            
            if order:
                # Update strategy state
                self.strategy.sell_position(price)
                self.trades_today += 1
                logger.info(f"Sell order executed: {order}")
            else:
                logger.error("Failed to execute sell order")
                
        except Exception as e:
            logger.error(f"Error executing sell: {e}")

    def archive_trading_records(self, max_log_size_mb=10):
        """Archive trading logs when they get too large instead of deleting them
        
        Args:
            max_log_size_mb: Maximum log size in MB before rotation
        """
        try:
            log_dir = "logs"
            current_log = os.path.join(log_dir, f"live_trader_{datetime.now().strftime('%Y%m%d')}.log")
            
            # Check if log file exists and is larger than max_size
            if os.path.exists(current_log) and os.path.getsize(current_log) > (max_log_size_mb * 1024 * 1024):
                # Create archives directory if it doesn't exist
                archive_dir = os.path.join(log_dir, "archives")
                os.makedirs(archive_dir, exist_ok=True)
                
                # Create timestamped archive filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_file = os.path.join(archive_dir, f"live_trader_{timestamp}.log")
                
                # Copy current log to archive
                shutil.copy2(current_log, archive_file)
                
                # Create a new log file (truncate the current one)
                with open(current_log, 'w') as f:
                    f.write(f"Log rotated at {datetime.now()}, previous log archived to {archive_file}\n")
                    
                logger.info(f"Log file archived to {archive_file}")
                
        except Exception as e:
            logger.error(f"Error archiving trading records: {e}")

def main():
    parser = argparse.ArgumentParser(description="Live Trading Bot for MicroStrategy")
    parser.add_argument("--config", type=str, default="config/config.json", help="Path to config file")
    args = parser.parse_args()
    
    try:
        # Initialize and run the live trader
        trader = LiveTrader(args.config)
        trader.run_trading_loop()
    except Exception as e:
        logger.error(f"Critical error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
