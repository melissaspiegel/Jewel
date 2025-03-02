import pandas as pd
import talib
import logging

# Logger Setup
log = logging.getLogger(__name__)

class MicroStrategy:
    """Optimized Strategy for small accounts ($100)"""

    def __init__(self, params, data, balance=100, btc_holdings=0, fee=0.001):
        self.params = params
        self.data = data.copy()
        
        # Add necessary columns
        self.data["fastMA"] = pd.NA
        self.data["slowMA"] = pd.NA
        self.data["RSI"] = pd.NA
        self.data["MACD"] = pd.NA
        self.data["MACD_signal"] = pd.NA
        self.data["upper_band"] = pd.NA
        self.data["middle_band"] = pd.NA
        self.data["lower_band"] = pd.NA
        self.data["open_long"] = False  # Initialize as False
        self.data["close_long"] = False  # Initialize as False
        self.data["stoch_k"] = pd.NA
        self.data["stoch_d"] = pd.NA
        
        # No cooldown for micro strategy - we need to trade frequently
        self.cooldown_counter = 0
        self.cooldown_period = 0
        
        # Store balance and BTC holdings
        self.balance = balance  # Start with $100
        self.btc_holdings = btc_holdings
        self.trade_amount = balance * 0.95  # Use 95% of balance for each trade
        self.fee = fee
        self.last_buy_price = 0
        
        # Aggressive take-profit & stop-loss for micro accounts
        self.take_profit_threshold = 1.025  # 2.5% profit target
        self.stop_loss_threshold = 0.985  # 1.5% stop loss
        
        self.populate_indicators()
        self.populate_signals()

    def populate_indicators(self):
        """Calculate technical indicators optimized for micro trading"""
        fast_period = self.params.get("fast_ma_period", 4)
        slow_period = self.params.get("slow_ma_period", 12)
        rsi_period = self.params.get("rsi_period", 10)
        macd_fast = self.params.get("macd_fast", 8)
        macd_slow = self.params.get("macd_slow", 18)
        macd_signal = self.params.get("macd_signal", 5)
        bollinger_period = self.params.get("bollinger_period", 15)
        bollinger_stddev = self.params.get("bollinger_stddev", 1.8)

        # Calculate indicators
        self.data["fastMA"] = talib.SMA(self.data["close"], timeperiod=fast_period)
        self.data["slowMA"] = talib.SMA(self.data["close"], timeperiod=slow_period)
        self.data["RSI"] = talib.RSI(self.data["close"], timeperiod=rsi_period)
        self.data["MACD"], self.data["MACD_signal"], _ = talib.MACD(
            self.data["close"], fastperiod=macd_fast, slowperiod=macd_slow, signalperiod=macd_signal
        )
        self.data["upper_band"], self.data["middle_band"], self.data["lower_band"] = talib.BBANDS(
            self.data["close"], timeperiod=bollinger_period, nbdevup=bollinger_stddev, nbdevdn=bollinger_stddev, matype=0
        )
        
        # Stochastic oscillator for better entry/exit timing
        self.data["stoch_k"], self.data["stoch_d"] = talib.STOCH(
            self.data["high"], self.data["low"], self.data["close"], 
            fastk_period=10, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0
        )
            
        # Forward-fill for these columns
        for col in ["slowMA", "RSI", "MACD", "MACD_signal", "upper_band", "middle_band", "lower_band", "stoch_k", "stoch_d"]:
            self.data[col] = self.data[col].ffill()

        # Backward-fill for all columns (including fastMA)
        for col in ["fastMA", "slowMA", "RSI", "MACD", "MACD_signal", "upper_band", "middle_band", "lower_band", "stoch_k", "stoch_d"]:
            self.data[col] = self.data[col].bfill()

    def populate_signals(self):
        """Define trading signals optimized for micro accounts"""
        # More aggressive entry conditions for micro accounts
        self.data["open_long"] = (
            # MA crossover with RSI filter
            ((self.data["fastMA"] > self.data["slowMA"]) & (self.data["RSI"] < 52)) |
            # Strong MACD signal
            ((self.data["MACD"] > self.data["MACD_signal"] * 1.1) & (self.data["RSI"] < 55)) |
            # Oversold condition
            ((self.data["RSI"] < 35) & (self.data["MACD"] > self.data["MACD_signal"])) |
            # Bollinger Band bounce
            ((self.data["close"] < self.data["lower_band"] * 1.01) & (self.data["stoch_k"] < 30)) |
            # Stochastic crossover in oversold region
            ((self.data["stoch_k"] < 30) & (self.data["stoch_k"] > self.data["stoch_d"]))
        )
        
        # Quick exit conditions to secure profits
        if self.last_buy_price > 0:
            # Have an active position - check for take profit/stop loss
            take_profit_price = self.last_buy_price * self.take_profit_threshold
            stop_loss_price = self.last_buy_price * self.stop_loss_threshold
            
            self.data["close_long"] = (
                # Take profit at 2.5%
                (self.data["close"] >= take_profit_price) |
                # Stop loss at 1.5%
                (self.data["close"] <= stop_loss_price) |
                # MA crossover
                ((self.data["fastMA"] < self.data["slowMA"]) & (self.data["RSI"] > 55)) |
                # Overbought condition
                (self.data["RSI"] > 65) |
                # MACD bearish crossover
                ((self.data["MACD"] < self.data["MACD_signal"]) & (self.data["close"] > self.data["middle_band"])) |
                # Upper band touch
                (self.data["close"] > self.data["upper_band"] * 0.98) |
                # Stochastic overbought
                ((self.data["stoch_k"] > 70) & (self.data["stoch_k"] < self.data["stoch_d"]))
            )
        else:
            self.data["close_long"] = (
                # MA crossover
                ((self.data["fastMA"] < self.data["slowMA"]) & (self.data["RSI"] > 55)) |
                # Overbought condition
                (self.data["RSI"] > 65) |
                # MACD bearish crossover
                ((self.data["MACD"] < self.data["MACD_signal"]) & (self.data["close"] > self.data["middle_band"])) |
                # Upper band touch
                (self.data["close"] > self.data["upper_band"] * 0.98) |
                # Stochastic overbought
                ((self.data["stoch_k"] > 70) & (self.data["stoch_k"] < self.data["stoch_d"]))
            )

    def evaluate_orders(self, timestamp, latest_row):
        """Evaluate buy/sell conditions for micro accounts"""
        log.debug(f"📊 MICRO BALANCE: ${self.balance:.2f}, BTC: {self.btc_holdings:.8f}")

        try:
            current_price = latest_row["close"]
            
            # Update trade amount based on current balance - aggressive for small accounts
            self.trade_amount = min(self.balance * 0.95, self.balance)  # Use most of balance but never more than we have
            
            # Check if we need to close an existing position
            if self.btc_holdings > 0:
                entry_price = self.last_buy_price if self.last_buy_price > 0 else current_price
                take_profit_price = entry_price * self.take_profit_threshold
                stop_loss_price = entry_price * self.stop_loss_threshold
                
                # Take profit
                if current_price >= take_profit_price:
                    log.info(f"🎯 MICRO TAKE PROFIT: Selling at ${current_price:.2f}")
                    self.sell_position(current_price)
                    return
                    
                # Stop loss
                if current_price <= stop_loss_price:
                    log.info(f"🛑 MICRO STOP LOSS: Selling at ${current_price:.2f}")
                    self.sell_position(current_price)
                    return
                
                # Check for sell signal    
                if latest_row.get("close_long", False):
                    self.sell_position(current_price)
                    return
                    
            # Check for new buy signal if we have available funds
            elif self.balance >= 10 and latest_row.get("open_long", False):
                self.buy_position(current_price)
                return
                
        except Exception as e:
            log.error(f"Error in evaluate_orders: {e}")

    def buy_position(self, price):
        """Execute a buy order with micro-optimized position sizing"""
        if self.balance <= 0 or price <= 0:
            log.warning(f"Cannot buy with invalid balance ${self.balance:.2f} or price ${price:.2f}")
            return
            
        btc_bought = (self.trade_amount / price) * (1 - self.fee)
        self.btc_holdings += btc_bought
        self.balance -= self.trade_amount
        self.last_buy_price = price
        log.info(f"🟢 MICRO BUY: {btc_bought:.8f} BTC at ${price:.2f}, Balance: ${self.balance:.2f}")

    def sell_position(self, price):
        """Execute a sell order with profit calculation"""
        if self.btc_holdings <= 0 or price <= 0:
            log.warning(f"Cannot sell with invalid holdings {self.btc_holdings:.8f} or price ${price:.2f}")
            return
            
        sale_value = self.btc_holdings * price * (1 - self.fee)
        profit = 0
        if self.last_buy_price > 0:
            profit = sale_value - (self.btc_holdings * self.last_buy_price)
            profit_pct = (profit / (self.btc_holdings * self.last_buy_price)) * 100
            log.info(f"💰 MICRO PROFIT: ${profit:.2f} ({profit_pct:.2f}%)")
                
        self.balance += sale_value
        log.info(f"🔴 MICRO SELL: {self.btc_holdings:.8f} BTC at ${price:.2f}, Balance: ${self.balance:.2f}")
        self.btc_holdings = 0
