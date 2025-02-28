#!/usr/bin/env python3
"""
TA-Lib Installation Helper

This script helps users install the TA-Lib technical analysis library
which is required for the trading game to function correctly.
"""

import os
import sys
import platform
import subprocess
import webbrowser

def print_header():
    """Print a nice header"""
    print("\n" + "=" * 70)
    print("TA-Lib Installation Helper for Bitcoin Trading Game".center(70))
    print("=" * 70)
    print("\nThis script will help you install TA-Lib, which is required for the trading game.\n")

def detect_platform():
    """Detect the operating system"""
    system = platform.system().lower()
    print(f"Detected operating system: {system}")
    
    if system == 'darwin':
        return 'macos'
    elif system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'

def try_install_talib_binary():
    """Try to install talib-binary package"""
    try:
        print("Attempting to install talib-binary package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "talib-binary"])
        return True
    except subprocess.CalledProcessError:
        print("Failed to install talib-binary package.")
        return False

def install_macos():
    """Install TA-Lib on macOS"""
    print("\nInstalling TA-Lib on macOS\n")
    
    # First try the binary package
    if try_install_talib_binary():
        print("Successfully installed talib-binary!")
        return True
    
    # Check if Homebrew is installed
    try:
        subprocess.check_call(["brew", "--version"])
        has_homebrew = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_homebrew = False
    
    if has_homebrew:
        try:
            print("Installing TA-Lib using Homebrew...")
            subprocess.check_call(["brew", "install", "ta-lib"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "TA-Lib"])
            return True
        except subprocess.CalledProcessError:
            print("Failed to install using Homebrew.")
    else:
        print("Homebrew is not installed. You can install it with:")
        print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    
    # Try conda as a fallback
    try:
        subprocess.check_call(["conda", "--version"])
        print("Installing TA-Lib using conda...")
        subprocess.check_call(["conda", "install", "-c", "conda-forge", "ta-lib", "-y"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Conda not found. Consider installing Anaconda/Miniconda for easier TA-Lib installation.")
    
    return False

def install_windows():
    """Install TA-Lib on Windows"""
    print("\nInstalling TA-Lib on Windows\n")
    
    # First try the binary package
    if try_install_talib_binary():
        print("Successfully installed talib-binary!")
        return True
    
    # Try conda
    try:
        subprocess.check_call(["conda", "--version"])
        print("Installing TA-Lib using conda...")
        subprocess.check_call(["conda", "install", "-c", "conda-forge", "ta-lib", "-y"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Conda not found.")
    
    # Offer wheel installation instructions
    print("\nFor Windows, you may need to install from a pre-built wheel:")
    print("1. Download the appropriate wheel for your Python version from:")
    print("   https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
    print(f"2. Install with pip: pip install TA_Lib-0.4.x-cpXX-cpXX-win_amd64.whl")
    
    # Open wheel download page
    try:
        webbrowser.open("https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
    except:
        pass
        
    return False

def install_linux():
    """Install TA-Lib on Linux"""
    print("\nInstalling TA-Lib on Linux\n")
    
    # First try the binary package
    if try_install_talib_binary():
        print("Successfully installed talib-binary!")
        return True
    
    # Try conda
    try:
        subprocess.check_call(["conda", "--version"])
        print("Installing TA-Lib using conda...")
        subprocess.check_call(["conda", "install", "-c", "conda-forge", "ta-lib", "-y"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Conda not found.")
    
    # Offer source compilation instructions
    print("\nOn Linux, you may need to compile TA-Lib from source:")
    print("""
    sudo apt-get update
    sudo apt-get install build-essential
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    pip install TA-Lib
    """)
    
    return False

def create_helper_module():
    """Create a helper module to import talib properly"""
    helper_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategies", "talib_helper.py")
    
    with open(helper_file, "w") as f:
        f.write("""
# Helper module for importing TA-Lib properly
try:
    import talib
except ImportError:
    try:
        import talib.abstract as talib
    except ImportError:
        raise ImportError(
            "TA-Lib not found. Please run the install_talib.py script or install manually."
        )

# Export the talib module
""")
    
    print(f"\nCreated talib_helper.py in strategies directory.")
    print("You can now use 'from strategies.talib_helper import talib' in your code.")

def modify_strategy_import():
    """Modify the strategy file to use the helper module"""
    strategy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategies", "micro_strategy.py")
    
    try:
        with open(strategy_file, "r") as f:
            content = f.read()
        
        # Replace direct talib import with helper import
        if "import talib" in content:
            content = content.replace(
                "import talib", 
                "try:\n    import talib\nexcept ImportError:\n    from strategies.talib_helper import talib")
            
            with open(strategy_file, "w") as f:
                f.write(content)
                
            print("Updated micro_strategy.py to handle missing talib module gracefully.")
    except:
        print("Could not modify strategy file.")

def main():
    """Main installation function"""
    print_header()
    platform_type = detect_platform()
    success = False
    
    if platform_type == 'macos':
        success = install_macos()
    elif platform_type == 'windows':
        success = install_windows()
    elif platform_type == 'linux':
        success = install_linux()
    else:
        print("Unknown platform. Please install TA-Lib manually.")
    
    # Create helper module regardless of installation success
    create_helper_module()
    modify_strategy_import()
    
    print("\n" + "=" * 70)
    if success:
        print("TA-Lib installation appears successful! Try running the trading game now.")
    else:
        print("Could not automatically install TA-Lib.")
        print("Please see the detailed instructions in docs/talib_installation.md")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
