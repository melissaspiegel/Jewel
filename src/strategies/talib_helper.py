"""
Helper module for importing TA-Lib properly
Provides fallback to a simple polyfill implementation if TA-Lib is not available
"""

try:
    # Try standard installation first
    import talib
    print("Using standard TA-Lib installation")
    
except ImportError:
    try:
        # Try binary package
        import talib.abstract as talib
        print("Using talib.abstract from talib-binary package")
        
    except ImportError:
        # Fall back to our simple polyfill implementation
        print("TA-Lib not found, using polyfill implementation")
        print("WARNING: Results may differ from TA-Lib. Consider installing TA-Lib for better accuracy.")
        from strategies.talib_polyfill import *
        import strategies.talib_polyfill as talib
