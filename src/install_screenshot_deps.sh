#!/bin/bash
# Install dependencies for the screenshot capture tool

pip install selenium pillow webdriver-manager

# Make the screenshot tool executable
chmod +x /Users/melissaspiegel/projects/micro/src/capture_screenshot.py

echo "Screenshot tool dependencies installed!"
echo "Run with: python src/capture_screenshot.py"
echo "Additional options: --file [html_file] --output [output_dir] --name [filename]"
