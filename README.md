# 🎮 Bitcoin Trading Game

A fun, educational simulation where you can practice Bitcoin trading strategies with fake money and real price data!


## 📝 Overview

This Bitcoin Trading Game is a risk-free way to experience cryptocurrency trading without using real money. The game uses either real Bitcoin price data from CoinGecko or simulated price movements to create an engaging trading experience.

### Key Features

- ✅ Trade with fake money - absolutely no real cryptocurrency involved
- ✅ Real Bitcoin price data from CoinGecko API (or optional simulated data)
- ✅ Time-limited gameplay (default: 60 seconds)
- ✅ Win by reaching a profit target (default: 15%)
- ✅ Built-in trading strategy with technical indicators
- ✅ Detailed game reports with performance charts
- ✅ Educational tool to understand trading concepts

## 🚀 Getting Started

### Prerequisites

- python3 3.7+
- pip for installing dependencies

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/melissaspiegel/jewel.git
   cd micro
   ```

2. Install required dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install numpy ccxt pandas
   ```

### Running the Game

Basic usage:
```bash
python3 src/trading_game.py
```

With custom settings:
```bash
python3 src/trading_game.py --balance 1000 --target 20 --time 120
```

### Command Line Options

- `--balance`: Starting fake balance (default: $100)
- `--target`: Win percentage target (default: 15%)
- `--time`: Game time limit in seconds (default: 60)
- `--simulated`: Use simulated price data instead of real prices

## 📊 Game Mechanics

1. **Setup**: Start with a fixed amount of fake money (default: $100)
2. **Goal**: Increase your portfolio value by the target percentage (default: 15%)
3. **Time Limit**: Complete the goal before the timer runs out (default: 60 seconds)
4. **Strategy**: The game uses MicroStrategy, an algorithmic trading system with:
   - Moving Average crossovers
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands
   - Stochastic Oscillator

## 📈 Game Reports

After each game, a detailed HTML report is generated in the `game_results` directory, including:
- Portfolio performance chart
- Bitcoin price chart during gameplay
- Profit/loss statistics
- Game outcome summary

## 🛠️ Project Structure

```
micro/
├── src/
│   ├── trading_game.py      # Main game logic
│   ├── strategies/
│   │   └── micro_strategy.py # Trading strategy implementation
├── data/                    # Price data storage
├── game_results/            # Generated game reports
└── README.md
```

## 📚 Educational Value

This game is designed to teach:
- Basic cryptocurrency trading concepts
- Technical analysis indicators
- Risk management principles
- Trading psychology in a risk-free environment

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- CoinGecko API for providing real-time Bitcoin price data
- TA-Lib for technical analysis indicators

---

**Note**: This is purely educational and for entertainment purposes. No real trading is performed and no real cryptocurrency is used.
