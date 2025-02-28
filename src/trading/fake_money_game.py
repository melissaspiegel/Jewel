#!/usr/bin/env python3
"""
FAKE MONEY TRADING GAME - Play with fake money and real Bitcoin price data
No real trading involved - just for fun and learning!
"""
import logging
from datetime import datetime
from .base_trading_game import BaseTradingGame

logger = logging.getLogger(__name__)

class FakeMoneyGame(BaseTradingGame):
    """Trading game with fake money and real or simulated price data"""
    
    def __init__(self, starting_balance=100, use_real_prices=True):
        """Initialize the fake money trading game"""
        super().__init__(starting_balance, use_real_prices)
        
        # Rename variables to be more game-like
        self.fake_money = self.balance
        self.win_percentage = self.profit_target
    
    def execute_trade(self, action, amount):
        """Execute a simulated trade with fake money"""
        if action == 'buy':
            # Calculate costs including fees
            cost = amount * self.current_price
            fee_cost = cost * self.fee
            total_cost = cost + fee_cost
            
            if total_cost <= self.balance:
                self.balance -= total_cost
                self.btc_holdings += amount
                self.strategy.balance = self.balance
                self.strategy.btc_holdings = self.btc_holdings
                self.strategy.last_buy_price = self.current_price
                
                logger.info(f"🔵 BUY: {amount:.8f} BTC at ${self.current_price:.2f} = ${cost:.2f} + ${fee_cost:.2f} fee")
                return True
            else:
                logger.warning(f"⚠️ Not enough funds to buy! Need ${total_cost:.2f}, have ${self.balance:.2f}")
                return False
        
        elif action == 'sell':
            if amount <= 0:
                return False
                
            # Calculate proceeds after fees
            proceeds = amount * self.current_price
            fee_cost = proceeds * self.fee
            net_proceeds = proceeds - fee_cost
            
            self.balance += net_proceeds
            self.btc_holdings -= amount
            self.strategy.balance = self.balance
            self.strategy.btc_holdings = self.btc_holdings
            
            logger.info(f"🔴 SELL: {amount:.8f} BTC at ${self.current_price:.2f} = ${proceeds:.2f} - ${fee_cost:.2f} fee")
            return True
        
        return False
    
    def get_report_title(self):
        """Return title for the report"""
        return "Bitcoin Trading Game Results"
    
    def get_report_details(self):
        """Return additional details for the report"""
        return "<p>This was a game with fake money - no real cryptocurrency was traded!</p>"
    
    def get_result_message(self, profit_pct):
        """Return result message based on profit percentage"""
        if profit_pct >= self.profit_target:
            return f"🏆 CONGRATULATIONS! YOU WIN! Made {profit_pct:.2f}% profit!"
        else:
            return f"❌ GAME OVER. You made {profit_pct:.2f}% profit but didn't reach target of {self.profit_target}%"
    
    def display_instructions(self):
        """Display game instructions"""
        logger.info("=" * 60)
        logger.info("🎮 WELCOME TO THE BITCOIN TRADING GAME 🎮")
        logger.info("=" * 60)
        logger.info("This is a GAME with FAKE money - no real trading!")
        logger.info(f"Starting with ${self.balance:.2f} fake dollars")
        logger.info(f"Goal: Make ${self.profit_target}% profit before time runs out!")
        logger.info("=" * 60)
        
    # Alias run_game to run for backward compatibility
    def run_game(self):
        """Run the game (alias for run)"""
        return self.run()
