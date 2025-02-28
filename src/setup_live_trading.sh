#!/bin/bash

# Create directory structure for live trading
mkdir -p /Users/melissaspiegel/projects/micro/live_trading/strategies
mkdir -p /Users/melissaspiegel/projects/micro/live_trading/config
mkdir -p /Users/melissaspiegel/projects/micro/live_trading/logs
mkdir -p /Users/melissaspiegel/projects/micro/live_trading/data

# Copy and adapt strategy
cp /Users/melissaspiegel/projects/micro/src/strategies/micro_strategy.py /Users/melissaspiegel/projects/micro/live_trading/strategies/

# Set permissions
chmod +x /Users/melissaspiegel/projects/micro/live_trading/*.py

echo "Live trading directory structure created at /Users/melissaspiegel/projects/micro/live_trading/"
