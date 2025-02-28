#!/bin/bash
# Script to install TA-Lib on various platforms

set -e  # Exit on error

echo "==============================================="
echo "      TA-Lib Installation Helper Script"
echo "==============================================="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo "Detected OS: $OS"

# Try installing talib-binary first (works on many systems without compilation)
echo "Trying to install talib-binary package..."
pip install talib-binary
if [ $? -eq 0 ]; then
    echo "✅ Successfully installed talib-binary!"
    echo "You may need to use 'import talib.abstract as talib' in your code."
    exit 0
fi

# OS-specific instructions
if [ "$OS" == "macOS" ]; then
    echo "Installing TA-Lib on macOS..."
    
    if command -v brew &>/dev/null; then
        echo "Using Homebrew to install TA-Lib..."
        brew install ta-lib
        pip install TA-Lib
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        echo "Then run this script again."
        exit 1
    fi
    
elif [ "$OS" == "Linux" ]; then
    echo "Installing TA-Lib on Linux..."
    echo "This will require sudo access to install packages."
    
    sudo apt-get update
    sudo apt-get install -y build-essential wget
    
    # Check if ta-lib is already installed
    if [ -f "/usr/lib/libta_lib.so" ]; then
        echo "TA-Lib library already installed."
    else
        # Download and build TA-Lib
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib/
        ./configure --prefix=/usr
        make
        sudo make install
        cd ..
        rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
    fi
    
    # Install Python wrapper
    pip install TA-Lib
    
elif [ "$OS" == "Windows" ]; then
    echo "For Windows, please:"
    echo "1. Use conda: conda install -c conda-forge ta-lib"
    echo "2. Or download a wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib"
    echo "3. Then install with: pip install TA_Lib‑0.4.xx‑cpXX‑win_amd64.whl"
    exit 1
    
else
    echo "Unsupported OS. Please install TA-Lib manually."
    exit 1
fi

echo "TA-Lib installation complete!"
