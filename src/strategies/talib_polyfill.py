"""
TA-Lib Polyfill - Simple implementation of technical indicators without TA-Lib dependency
For users who can't install the TA-Lib library
"""
import numpy as np
import pandas as pd

def SMA(data, timeperiod=30):
    """Simple Moving Average"""
    return pd.Series(data).rolling(window=timeperiod).mean().values

def EMA(data, timeperiod=30):
    """Exponential Moving Average"""
    return pd.Series(data).ewm(span=timeperiod, adjust=False).mean().values

def RSI(data, timeperiod=14):
    """Relative Strength Index"""
    delta = pd.Series(data).diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    ma_up = up.rolling(window=timeperiod).mean()
    ma_down = down.rolling(window=timeperiod).mean()
    
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.values

def BBANDS(data, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0):
    """Bollinger Bands"""
    middle_band = pd.Series(data).rolling(window=timeperiod).mean()
    std_dev = pd.Series(data).rolling(window=timeperiod).std()
    
    upper_band = middle_band + (std_dev * nbdevup)
    lower_band = middle_band - (std_dev * nbdevdn)
    
    return upper_band.values, middle_band.values, lower_band.values

def MACD(data, fastperiod=12, slowperiod=26, signalperiod=9):
    """Moving Average Convergence/Divergence"""
    fast_ema = pd.Series(data).ewm(span=fastperiod, adjust=False).mean()
    slow_ema = pd.Series(data).ewm(span=slowperiod, adjust=False).mean()
    
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signalperiod, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line.values, signal_line.values, histogram.values

def STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0):
    """Stochastic Oscillator"""
    highest_high = pd.Series(high).rolling(window=fastk_period).max()
    lowest_low = pd.Series(low).rolling(window=fastk_period).min()
    
    # Fast K
    fastk = 100 * ((pd.Series(close) - lowest_low) / (highest_high - lowest_low))
    
    # Slow K is the EMA of Fast K
    slowk = fastk.rolling(window=slowk_period).mean()
    
    # Slow D is the EMA of Slow K
    slowd = slowk.rolling(window=slowd_period).mean()
    
    return slowk.values, slowd.values
