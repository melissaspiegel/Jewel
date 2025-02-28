# Installing TA-Lib for the Bitcoin Trading Game

TA-Lib (Technical Analysis Library) is required for the trading indicators in this project. It can be challenging to install because it requires compiling C/C++ code.

## macOS Installation

### Method 1: Using Homebrew (Recommended for macOS)

1. Install Homebrew if you don't have it:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install TA-Lib using Homebrew:
   ```bash
   brew install ta-lib
   ```

3. Install the Python wrapper:
   ```bash
   pip install TA-Lib
   ```

### Method 2: Using conda (Alternative)

If you use Anaconda or Miniconda:

```bash
conda install -c conda-forge ta-lib
```

## Windows Installation

### Method 1: Using pre-built wheels

Download the appropriate wheel file for your Python version from:
https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

Then install it with pip:
```bash
pip install TA_Lib‑0.4.21‑cp39‑cp39‑win_amd64.whl  # Adjust filename based on your Python version
```

### Method 2: Using conda (Recommended for Windows)

```bash
conda install -c conda-forge ta-lib
```

## Linux Installation

### Ubuntu/Debian:

```bash
# Install the C library
sudo apt-get update
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# Install the Python wrapper
pip install TA-Lib
```

### Alternative Method for All Platforms

If you're facing issues with the above methods, you can use a simpler solution by installing the `talib-binary` package which typically works on most platforms without compilation:

```bash
pip install talib-binary
```

Then modify the import in your code:

```python
try:
    import talib
except ImportError:
    # Try the binary package instead
    import talib.abstract as talib
```

## Troubleshooting

If you encounter issues, please visit the [TA-Lib documentation](https://github.com/mrjbq7/ta-lib) for more information.
