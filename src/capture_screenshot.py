#!/usr/bin/env python3
"""
Screenshot capture utility for Bitcoin Trading Game
Requires: pip install selenium pillow webdriver-manager
"""

import os
import sys
import time
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

def capture_screenshot(html_file, output_dir='docs', filename=None):
    """
    Capture a screenshot of an HTML file using headless Chrome
    
    Args:
        html_file: Path to HTML file to capture
        output_dir: Directory to save screenshot to
        filename: Optional filename for the screenshot
        
    Returns:
        Path to saved screenshot
    """
    if not os.path.exists(html_file):
        print(f"Error: HTML file not found: {html_file}")
        return None
        
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1200,900")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    try:
        # Set up Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Convert to file URI for local file
        file_url = f"file://{os.path.abspath(html_file)}"
        driver.get(file_url)
        
        # Give time for all elements to load and render
        time.sleep(2)
        
        # Determine output filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trading_game_screenshot_{timestamp}.png"
        
        output_file = os.path.join(output_dir, filename)
        
        # Take screenshot
        driver.save_screenshot(output_file)
        print(f"Screenshot saved to: {output_file}")
        
        # Optionally, crop the image if needed
        img = Image.open(output_file)
        # Example crop: img = img.crop((0, 0, 1200, 900))
        img.save(output_file)
        
        return output_file
        
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

def find_latest_report():
    """Find the most recent game report HTML file"""
    report_dir = "game_results"
    if not os.path.exists(report_dir):
        print(f"Error: Game results directory not found: {report_dir}")
        return None
        
    html_files = [f for f in os.listdir(report_dir) if f.endswith('.html')]
    if not html_files:
        print(f"Error: No HTML reports found in {report_dir}")
        return None
        
    # Sort by modification time, most recent first
    html_files.sort(key=lambda f: os.path.getmtime(os.path.join(report_dir, f)), reverse=True)
    return os.path.join(report_dir, html_files[0])

def main():
    parser = argparse.ArgumentParser(description="Capture screenshot of Bitcoin Trading Game report")
    parser.add_argument("--file", help="Path to HTML file (defaults to most recent report)")
    parser.add_argument("--output", default="docs", help="Output directory for screenshot")
    parser.add_argument("--name", default="trading_game_screenshot.png", help="Output filename")
    args = parser.parse_args()
    
    html_file = args.file if args.file else find_latest_report()
    if not html_file:
        sys.exit(1)
        
    output_file = capture_screenshot(html_file, args.output, args.name)
    if output_file:
        print(f"Screenshot saved as {output_file}")
        print(f"You can reference it in your README.md with: ![Trading Game]({output_file})")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
