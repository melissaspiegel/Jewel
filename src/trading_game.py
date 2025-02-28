#!/usr/bin/env python3
"""
TRADING GAME - Play with fake money and real Bitcoin price data
No real trading involved - just for fun and learning!
"""
import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import logging
import random
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"game_results/game_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Import system paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from strategies.micro_strategy import MicroStrategy

# Import cleanup function
try:
    from cleanup import cleanup_game_results
    CLEANUP_AVAILABLE = True
except ImportError:
    logger.warning("Cleanup module not available - old results won't be automatically removed")
    CLEANUP_AVAILABLE = False

class TradingGame:
    """Trading game with fake money and real price data"""
    
    def __init__(self, starting_balance=100, use_real_prices=True):
        """Initialize the trading game"""
        self.starting_balance = starting_balance
        self.fake_money = starting_balance
        self.btc_holdings = 0
        self.fee = 0.001  # 0.1% trading fee
        self.current_price = 0
        self.last_buy_price = 0
        self.price_history = []
        self.balance_history = []
        self.use_real_prices = use_real_prices
        
        # Set win conditions
        self.win_percentage = 15  # Win when you make 15% profit
        self.time_limit = 60  # Game length in seconds
        
        # Load or create price data
        self.price_data = self.load_price_data()
        if use_real_prices:
            logger.info("🌐 Using REAL Bitcoin price data (but with FAKE money!)")
        else:
            logger.info("🎮 Using simulated price data")
        
        # Strategy parameters for the game
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
        
        # Initialize the game strategy
        self.strategy = MicroStrategy(
            self.strategy_params, 
            self.price_data, 
            balance=self.fake_money,
            btc_holdings=self.btc_holdings
        )
        
        # Display game instructions
        logger.info("=" * 60)
        logger.info("🎮 WELCOME TO THE BITCOIN TRADING GAME 🎮")
        logger.info("=" * 60)
        data_file = "data/btc_game_data.csv"
        
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
            
            # Add a slight upward bias to make the game more fun
            if random.random() < 0.55:  # 55% chance of going up
                price_change = abs(price_change)
            
            self.current_price += price_change
            
        self.price_history.append((datetime.now(), self.current_price))
        return self.current_price
    
    def execute_game_logic(self):
        """Run one step of the game logic"""
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
                # Force a profitable sell
                sell_price = max(
                    btc_price, 
                    self.strategy.last_buy_price * 1.03  # 3% profit target
                )
                self.strategy.sell_position(sell_price)
            else:
                # Force a buy at current price
                if self.strategy.balance >= 10:  # Ensure we have some money
                    self.strategy.trade_amount = self.strategy.balance * 0.95
                    self.strategy.buy_position(btc_price)
        else:
            # Normal strategy
            self.strategy.evaluate_orders(timestamp, current_data)
        
        # Update game state from strategy
        self.fake_money = self.strategy.balance
        self.btc_holdings = self.strategy.btc_holdings
        
        # Calculate total portfolio value
        total_value = self.fake_money + (self.btc_holdings * btc_price)
        profit_pct = (total_value / self.starting_balance - 1) * 100
        
        # Record balance history
        self.balance_history.append((datetime.now(), self.fake_money, self.btc_holdings, btc_price, total_value))
        
        # Log game status
        logger.info(f"💰 Game Status: ${self.fake_money:.2f} + {self.btc_holdings:.8f} BTC (${self.btc_holdings * btc_price:.2f}) = ${total_value:.2f}")
        logger.info(f"📈 BTC Price: ${btc_price:.2f} | Profit: {profit_pct:.2f}%")
        
        return profit_pct
    
    def generate_game_report(self):
        """Generate a game report with charts and statistics"""
        # Create results directory
        results_dir = "game_results"
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
        plt.title("Game Performance")
        plt.xlabel("Game Time")
        plt.ylabel("Value ($)")
        plt.legend()
        plt.grid(True)
        balance_chart = os.path.join(results_dir, f"game_performance_{timestamp}.png")
        plt.savefig(balance_chart)
        
        # Price chart
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(balance_df)), balance_df["price"])
        plt.title("Bitcoin Price During Game")
        plt.xlabel("Game Time")
        plt.ylabel("BTC Price ($)")
        plt.grid(True)
        price_chart = os.path.join(results_dir, f"game_price_{timestamp}.png")
        plt.savefig(price_chart)
        
        # Calculate final game statistics
        final_value = self.fake_money + (self.btc_holdings * self.current_price)
        profit = final_value - self.starting_balance
        profit_pct = (profit / self.starting_balance) * 100
        game_result = "WIN" if profit_pct >= self.win_percentage else "LOSE"
        
        # Generate HTML game report
        html_file = os.path.join(results_dir, f"game_report_{timestamp}.html")
        
        # Determine profit/loss class
        profit_class = "good" if profit >= 0 else "bad"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bitcoin Trading Game Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .lose {{ background-color: #e74c3c; }}
                .summary {{ background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .good {{ color: green; font-weight: bold; }}
                .bad {{ color: red; font-weight: bold; }}
                .charts {{ display: flex; flex-direction: column; margin: 20px 0; }}
                .chart {{ margin: 20px 0; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #333; }}
                .result {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
                .win {{ color: green; }}
                .lose {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header {game_result.lower()}">
                <h1>Bitcoin Trading Game Results</h1>
                <p>Game completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <div class="result {game_result.lower()}">
                    {"🏆 CONGRATULATIONS! YOU WIN!" if game_result == "WIN" else "❌ GAME OVER. YOU LOSE."}
                </div>
                <h2>Game Summary</h2>
                <p><strong>Starting Fake Money:</strong> ${self.starting_balance:.2f}</p>
                <p><strong>Final Cash:</strong> ${self.fake_money:.2f}</p>
                <p><strong>Final BTC Holdings:</strong> {self.btc_holdings:.8f} BTC (${self.btc_holdings * self.current_price:.2f})</p>
                <p><strong>Final Portfolio Value:</strong> ${final_value:.2f}</p>
                <p><strong>Profit/Loss:</strong> <span class="{profit_class}">${profit:.2f} ({profit_pct:.2f}%)</span></p>
                <p><strong>Win Target:</strong> {self.win_percentage}%</p>
            </div>
            
            <div class="charts">
                <div class="chart">
                    <h2>Portfolio Performance</h2>
                    <img src="game_performance_{timestamp}.png" alt="Game Performance" width="100%">
                </div>
                
                <div class="chart">
                    <h2>Bitcoin Price</h2>
                    <img src="game_price_{timestamp}.png" alt="Game Price" width="100%">
                </div>
            </div>
            
            <div class="summary">
                <h2>Game Statistics</h2>
                <p><strong>Game Duration:</strong> {len(self.balance_history)} rounds</p>
                <p><strong>Highest Portfolio Value:</strong> ${max([b[4] for b in self.balance_history]):.2f}</p>
                <p><strong>Lowest Portfolio Value:</strong> ${min([b[4] for b in self.balance_history]):.2f}</p>
                <p><strong>Bitcoin Price Range:</strong> ${min([b[3] for b in self.balance_history]):.2f} - ${max([b[3] for b in self.balance_history]):.2f}</p>
            </div>
            
            <div class="summary">
                <h2>Note</h2>
                <p>This was a game with fake money - no real cryptocurrency was traded!</p>
                <p>Data source: {"Real Bitcoin price data from CoinGecko API" if self.use_real_prices else "Simulated price data"}</p>
            </div>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(html_file, "w") as f:
            f.write(html)
        
        logger.info(f"🎮 Game report generated: {html_file}")
        return html_file
    
    def run_game(self):
        """Run the complete trading game"""
        # Display start message
        logger.info("🎮 GAME STARTING NOW! Good luck!")
        logger.info(f"🎯 Win target: Make {self.win_percentage}% profit")
        logger.info(f"⏱️ Time limit: {self.time_limit} seconds")
        
        # Start game timer
        start_time = time.time()
        end_time = start_time + self.time_limit
        
        # Update initial price
        self.current_price = self.update_price()
        logger.info(f"💲 Starting BTC price: ${self.current_price:.2f}")
        
        try:
            # Game loop
            while time.time() < end_time:
                # Execute game logic
                profit_pct = self.execute_game_logic()
                
                # Check win condition
                if profit_pct >= self.win_percentage:
                    logger.info(f"🎯 WIN! You reached your profit target of {self.win_percentage}%")
                    logger.info(f"🏆 GAME COMPLETE! You made ${profit_pct:.2f}% profit!")
                    break
                
                # Game tick delay
                time.sleep(1)
                
                # Show remaining time every 5 seconds
                time_remaining = int(end_time - time.time())
                if time_remaining % 5 == 0:
                    logger.info(f"⏱️ Time remaining: {time_remaining} seconds")
            
            # Check if time ran out
            if time.time() >= end_time:
                total_value = self.fake_money + (self.btc_holdings * self.current_price)
                profit_pct = (total_value / self.starting_balance - 1) * 100
                
                if profit_pct >= self.win_percentage:
                    logger.info(f"🎯 WIN! You reached your profit target of {self.win_percentage}%")
                else:
                    logger.info(f"⏱️ Time's up! You made {profit_pct:.2f}% profit")
                    logger.info(f"❌ You didn't reach the {self.win_percentage}% profit target!")
            
            # Generate final report
            report_file = self.generate_game_report()
            
            # Final game message
            logger.info("=" * 60)
            logger.info("🎮 GAME OVER! Thanks for playing! 🎮")
            logger.info(f"📊 Final report: {report_file}")
            logger.info("=" * 60)
            
            return profit_pct >= self.win_percentage
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Game stopped by player")
            self.generate_game_report()
            return False
        except Exception as e:
            logger.error(f"❌ Game error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Bitcoin Trading Game - Play with fake money!")
    parser.add_argument("--balance", type=float, default=100.0, help="Starting fake balance (default: $100)")
    parser.add_argument("--target", type=float, default=15.0, help="Win percentage target (default: 15%%)")
    parser.add_argument("--time", type=int, default=60, help="Game time limit in seconds (default: 60)")
    parser.add_argument("--simulated", action="store_true", help="Use simulated price data instead of real prices")
    args = parser.parse_args()
    
    # Create game instance
    game = TradingGame(
        starting_balance=args.balance,
        use_real_prices=not args.simulated
    )
    
    # Set custom game parameters
    game.win_percentage = args.target
    game.time_limit = args.time
    
    # Run the game
    game.run_game()

if __name__ == "__main__":
    main()
