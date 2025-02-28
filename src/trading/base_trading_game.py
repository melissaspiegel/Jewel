#!/usr/bin/env python3
"""
BASE TRADING GAME - Core functionality for trading games and real money trading
"""
import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import random
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"data/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Import system paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from strategies.micro_strategy import MicroStrategy

class BaseTradingGame:
    """Base class for trading games and real money trading"""
    
    def __init__(self, starting_balance=100, use_real_prices=True):
        """Initialize the trading game/trader"""
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.btc_holdings = 0
        self.fee = 0.001  # 0.1% trading fee
        self.current_price = 0
        self.last_buy_price = 0
        self.price_history = []
        self.balance_history = []
        self.use_real_prices = use_real_prices
        
        # Set win conditions (for game) or targets (for trading)
        self.profit_target = 15  # Target percentage profit
        self.time_limit = 60  # Session length in seconds
        
        # Load or create price data
        self.price_data = self.load_price_data()
        
        # Strategy parameters
        self.strategy_params = {
            "fast_ma_period": 4,
            "slow_ma_period": 12,
            "trend_ma_period": 30,
            "rsi_period": 10,
            "macd_fast": 8,
            "macd_slow": 18, 
            "macd_signal": 5,
            "bollinger_period": 15,
            "bollinger_stddev": 1.8
        }
        
        # Initialize the strategy
        self.strategy = MicroStrategy(
            self.strategy_params, 
            self.price_data, 
            balance=self.balance,
            btc_holdings=self.btc_holdings
        )
    
    def load_price_data(self):
        """Load Bitcoin price data"""
        # Try to use existing data file first
        data_file = "data/btc_price_data.csv"
        
        if os.path.exists(data_file):
            data = pd.read_csv(data_file)
            # Check if data is recent (within past 24 hours)
            if 'datetime' in data.columns:
                last_date = pd.to_datetime(data['datetime'].iloc[-1])
                if datetime.now() - last_date < timedelta(hours=24):
                    return data
        
        # Either file doesn't exist or data is old
        if self.use_real_prices:
            # Get real price data from CoinGecko API
            try:
                logger.info("🔄 Fetching real Bitcoin prices from CoinGecko...")
                # Get daily data for the past 30 days
                end_time = int(time.time())
                start_time = end_time - (30 * 24 * 60 * 60)  # 30 days ago
                
                url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
                params = {
                    "vs_currency": "usd",
                    "from": start_time,
                    "to": end_time
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                # Process the data
                prices = data.get('prices', [])
                
                # Create a DataFrame
                df = pd.DataFrame(prices, columns=['timestamp', 'close'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Add some reasonable approximations for OHLC data
                df['open'] = df['close'].shift(1)
                df['high'] = df['close'] * 1.005  # Approximate
                df['low'] = df['close'] * 0.995   # Approximate
                df['volume'] = 1000000  # Placeholder
                df['openinterest'] = -1  # Placeholder
                
                # Fill first row NaN values
                df.iloc[0, df.columns.get_loc('open')] = df.iloc[0, df.columns.get_loc('close')]
                
                # Save to file for future use
                os.makedirs(os.path.dirname(data_file), exist_ok=True)
                df.to_csv(data_file, index=False)
                
                return df
                
            except Exception as e:
                logger.error(f"Error fetching real price data: {e}")
                logger.info("Using simulated price data instead")
                self.use_real_prices = False
        
        # Create simulated price data
        logger.info("🎲 Generating simulated Bitcoin price data...")
        base_price = 60000
        num_days = 100
        
        # Generate synthetic price data with some realistic patterns
        dates = [datetime.now() - timedelta(days=i) for i in range(num_days, 0, -1)]
        
        # Create a slightly random walk with some trending
        prices = [base_price]
        for i in range(1, num_days):
            # Add some randomness with occasional trends
            change = np.random.normal(0, base_price * 0.01)
            # Add some trending behavior
            if i % 20 < 10:  # Uptrend for 10 days
                change += base_price * 0.003
            else:  # Downtrend for 10 days
                change -= base_price * 0.002
                
            new_price = max(100, prices[-1] + change)  # Ensure price doesn't go too low
            prices.append(new_price)
        
        df = pd.DataFrame({
            'datetime': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'close': [p * (1 + np.random.normal(0, 0.002)) for p in prices],
            'volume': [np.random.randint(5000000, 15000000) for _ in range(num_days)],
            'openinterest': [-1] * num_days
        })
        
        # Save simulated data
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        df.to_csv(data_file, index=False)
        
        return df
    
    def update_price(self):
        """Get or simulate the next Bitcoin price"""
        if self.use_real_prices:
            # Try to get real price from CoinGecko
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "bitcoin",
                    "vs_currencies": "usd",
                    "include_last_updated_at": True
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if "bitcoin" in data and "usd" in data["bitcoin"]:
                    price = float(data["bitcoin"]["usd"])
                    self.current_price = price
                    self.price_history.append((datetime.now(), price))
                    return price
                    
            except Exception as e:
                logger.warning(f"Couldn't get real price: {e}")
                logger.warning("Using simulated price movements instead")
                # Fall back to simulation if API fails
        
        # Simulate price movement
        if self.current_price == 0:
            # First price in the game - use the last price from the data
            self.current_price = self.price_data["close"].iloc[-1]
        else:
            # Simulate realistic price movement
            volatility = self.current_price * 0.001  # 0.1% volatility
            price_change = np.random.normal(0, volatility)
            
            # Add a slight bias
            if random.random() < 0.55:  # 55% chance of going up
                price_change = abs(price_change)
            
            self.current_price += price_change
            
        self.price_history.append((datetime.now(), self.current_price))
        return self.current_price
    
    def execute_trade(self, action, amount=None):
        """
        Execute a trade action (buy/sell)
        To be implemented by derived classes
        """
        raise NotImplementedError("This method must be implemented by derived classes")
    
    def execute_game_logic(self):
        """Run one step of the trading logic"""
        # Update price
        btc_price = self.update_price()
        
        # Update the strategy's price data
        latest_row = self.strategy.data.iloc[-1].copy()
        latest_row["datetime"] = datetime.now()
        latest_row["close"] = btc_price
        latest_row["open"] = self.strategy.data.iloc[-1]["close"]
        latest_row["high"] = max(btc_price, latest_row["open"] * 1.001)
        latest_row["low"] = min(btc_price, latest_row["open"] * 0.999)
        
        # Add new row to strategy data
        self.strategy.data = pd.concat([
            self.strategy.data,
            pd.DataFrame([latest_row])
        ])
        
        # Keep data size manageable
        if len(self.strategy.data) > 500:
            self.strategy.data = self.strategy.data.iloc[-500:]
        
        # Update strategy indicators
        self.strategy.populate_indicators()
        self.strategy.populate_signals()
        
        # Create current market data
        current_data = {
            "close": btc_price,
            "open_long": self.strategy.data.iloc[-1]["open_long"],
            "close_long": self.strategy.data.iloc[-1]["close_long"],
            "fastMA": self.strategy.data.iloc[-1]["fastMA"],
            "slowMA": self.strategy.data.iloc[-1]["slowMA"],
            "RSI": self.strategy.data.iloc[-1]["RSI"],
            "MACD": self.strategy.data.iloc[-1]["MACD"],
            "MACD_signal": self.strategy.data.iloc[-1]["MACD_signal"],
            "stoch_k": self.strategy.data.iloc[-1]["stoch_k"],
            "stoch_d": self.strategy.data.iloc[-1]["stoch_d"],
        }
        
        # Execute strategy
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Either use standard strategy or recovery strategy
        if self.strategy.balance < self.starting_balance * 0.95:
            # Recovery mode - when down more than 5%
            logger.info("💡 Using recovery strategy")
            if self.strategy.btc_holdings > 0:
                # Force a sell that aims for profit
                self.execute_trade('sell', self.btc_holdings)
            else:
                # Force a buy at current price
                if self.strategy.balance >= 10:  # Ensure we have some money
                    trade_amount = self.strategy.balance * 0.95
                    self.execute_trade('buy', trade_amount / btc_price)
        else:
            # Normal strategy
            action = self.strategy.evaluate_orders(timestamp, current_data)
            if action == 'buy':
                trade_amount = self.strategy.trade_amount / btc_price
                self.execute_trade('buy', trade_amount)
            elif action == 'sell':
                self.execute_trade('sell', self.btc_holdings)
        
        # Calculate total portfolio value
        total_value = self.balance + (self.btc_holdings * btc_price)
        profit_pct = (total_value / self.starting_balance - 1) * 100
        
        # Record balance history
        self.balance_history.append((datetime.now(), self.balance, self.btc_holdings, btc_price, total_value))
        
        # Log status
        self.log_status(total_value, profit_pct)
        
        return profit_pct
    
    def log_status(self, total_value, profit_pct):
        """Log the current status"""
        logger.info(f"💰 Status: ${self.balance:.2f} + {self.btc_holdings:.8f} BTC (${self.btc_holdings * self.current_price:.2f}) = ${total_value:.2f}")
        logger.info(f"📈 BTC Price: ${self.current_price:.2f} | Profit: {profit_pct:.2f}%")
    
    def generate_report(self):
        """Generate a report with charts and statistics"""
        # Create results directory
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert balance history to DataFrame
        balance_df = pd.DataFrame(
            self.balance_history,
            columns=["timestamp", "cash", "btc", "price", "total_value"]
        )
        
        # Create plots
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(balance_df)), balance_df["total_value"], label="Portfolio Value")
        plt.plot(range(len(balance_df)), balance_df["cash"], label="Cash")
        plt.axhline(y=self.starting_balance, color='r', linestyle='-', label="Starting Balance")
        plt.title("Performance")
        plt.xlabel("Time")
        plt.ylabel("Value ($)")
        plt.legend()
        plt.grid(True)
        balance_chart = os.path.join(results_dir, f"performance_{timestamp}.png")
        plt.savefig(balance_chart)
        
        # Price chart
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(balance_df)), balance_df["price"])
        plt.title("Bitcoin Price")
        plt.xlabel("Time")
        plt.ylabel("BTC Price ($)")
        plt.grid(True)
        price_chart = os.path.join(results_dir, f"price_{timestamp}.png")
        plt.savefig(price_chart)
        
        # Calculate final statistics
        final_value = self.balance + (self.btc_holdings * self.current_price)
        profit = final_value - self.starting_balance
        profit_pct = (profit / self.starting_balance) * 100
        result = "SUCCESS" if profit_pct >= self.profit_target else "MISSED TARGET"
        
        # Generate HTML report
        html_file = os.path.join(results_dir, f"report_{timestamp}.html")
        profit_class = "good" if profit >= 0 else "bad"
        
        # Get specific report details
        report_title = self.get_report_title()
        report_details = self.get_report_details()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .negative {{ background-color: #e74c3c; }}
                .summary {{ background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .good {{ color: green; font-weight: bold; }}
                .bad {{ color: red; font-weight: bold; }}
                .charts {{ display: flex; flex-direction: column; margin: 20px 0; }}
                .chart {{ margin: 20px 0; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #333; }}
                .result {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
                .success {{ color: green; }}
                .missed {{ color: orange; }}
                .failed {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header {result.lower()}">
                <h1>{report_title}</h1>
                <p>Completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <div class="result {result.lower()}">
                    {self.get_result_message(profit_pct)}
                </div>
                <h2>Summary</h2>
                <p><strong>Starting Balance:</strong> ${self.starting_balance:.2f}</p>
                <p><strong>Final Cash:</strong> ${self.balance:.2f}</p>
                <p><strong>Final BTC Holdings:</strong> {self.btc_holdings:.8f} BTC (${self.btc_holdings * self.current_price:.2f})</p>
                <p><strong>Final Portfolio Value:</strong> ${final_value:.2f}</p>
                <p><strong>Profit/Loss:</strong> <span class="{profit_class}">${profit:.2f} ({profit_pct:.2f}%)</span></p>
                <p><strong>Target:</strong> {self.profit_target}%</p>
            </div>
            
            <div class="charts">
                <div class="chart">
                    <h2>Portfolio Performance</h2>
                    <img src="performance_{timestamp}.png" alt="Performance" width="100%">
                </div>
                
                <div class="chart">
                    <h2>Bitcoin Price</h2>
                    <img src="price_{timestamp}.png" alt="Price" width="100%">
                </div>
            </div>
            
            <div class="summary">
                <h2>Statistics</h2>
                <p><strong>Duration:</strong> {len(self.balance_history)} rounds</p>
                <p><strong>Highest Portfolio Value:</strong> ${max([b[4] for b in self.balance_history]):.2f}</p>
                <p><strong>Lowest Portfolio Value:</strong> ${min([b[4] for b in self.balance_history]):.2f}</p>
                <p><strong>Bitcoin Price Range:</strong> ${min([b[3] for b in self.balance_history]):.2f} - ${max([b[3] for b in self.balance_history]):.2f}</p>
            </div>
            
            <div class="summary">
                <h2>Details</h2>
                <p>Data source: {"Real Bitcoin price data from CoinGecko API" if self.use_real_prices else "Simulated price data"}</p>
                {report_details}
            </div>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(html_file, "w") as f:
            f.write(html)
        
        logger.info(f"📊 Report generated: {html_file}")
        return html_file
    
    def get_report_title(self):
        """Return title for the report - to be overridden by subclasses"""
        return "Bitcoin Trading Report"
    
    def get_report_details(self):
        """Return additional details for the report - to be overridden by subclasses"""
        return ""
    
    def get_result_message(self, profit_pct):
        """Return result message based on profit percentage - to be overridden by subclasses"""
        if profit_pct >= self.profit_target:
            return f"🏆 SUCCESS! Target reached with {profit_pct:.2f}% profit!"
        elif profit_pct >= 0:
            return f"📈 POSITIVE! Made {profit_pct:.2f}% profit but didn't reach target of {self.profit_target}%"
        else:
            return f"📉 NEGATIVE! Lost {abs(profit_pct):.2f}%"
    
    def display_instructions(self):
        """Display instructions - to be overridden by subclasses"""
        pass
    
    def run(self):
        """Run the complete trading session"""
        # Display instructions
        self.display_instructions()
        
        # Start timer
        start_time = time.time()
        end_time = start_time + self.time_limit
        
        # Update initial price
        self.current_price = self.update_price()
        logger.info(f"💲 Starting BTC price: ${self.current_price:.2f}")
        
        try:
            # Main loop
            while time.time() < end_time:
                # Execute trading logic
                profit_pct = self.execute_game_logic()
                
                # Check target reached
                if profit_pct >= self.profit_target:
                    logger.info(f"🎯 Target reached! You made {profit_pct:.2f}% profit")
                    break
                
                # Tick delay
                time.sleep(1)
                
                # Show remaining time every 5 seconds
                time_remaining = int(end_time - time.time())
                if time_remaining % 5 == 0 and time_remaining > 0:
                    logger.info(f"⏱️ Time remaining: {time_remaining} seconds")
            
            # Check if time ran out
            if time.time() >= end_time:
                total_value = self.balance + (self.btc_holdings * self.current_price)
                profit_pct = (total_value / self.starting_balance - 1) * 100
                
                if profit_pct >= self.profit_target:
                    logger.info(f"🎯 Target reached with {profit_pct:.2f}% profit!")
                else:
                    logger.info(f"⏱️ Time's up! Made {profit_pct:.2f}% profit")
                    if self.profit_target > 0:
                        logger.info(f"Target was {self.profit_target}%")
            
            # Generate final report
            report_file = self.generate_report()
            
            # Final message
            logger.info("=" * 60)
            logger.info("🏁 SESSION COMPLETE!")
            logger.info(f"📊 Final report: {report_file}")
            logger.info("=" * 60)
            
            return profit_pct >= self.profit_target
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Stopped by user")
            self.generate_report()
            return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
