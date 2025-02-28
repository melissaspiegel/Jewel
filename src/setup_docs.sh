#!/bin/bash
# Create a docs directory to store images and other documentation assets

# Create the directory if it doesn't exist
mkdir -p /Users/melissaspiegel/projects/micro/docs

# Add a placeholder file to ensure directory gets committed to git
echo "# Documentation Assets" > /Users/melissaspiegel/projects/micro/docs/README.md
echo "This directory contains images and other documentation assets for the Micro Trading Game project." >> /Users/melissaspiegel/projects/micro/docs/README.md

echo "Docs directory created at /Users/melissaspiegel/projects/micro/docs"
echo "Save your screenshot as 'trading_game_screenshot.png' in this directory."

# Make script executable
chmod +x "$0"
