#!/usr/bin/env python3
"""
Results Management Script
- Keeps only the last 3 game results for fake trading
- Preserves all live trading results
"""
import os
import glob
import re
from datetime import datetime
import argparse
import shutil
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

def cleanup_game_results(results_dir="game_results", keep_last=3, dry_run=False):
    """
    Clean up game results directory keeping only the most recent ones
    
    Args:
        results_dir: Path to game results directory
        keep_last: Number of recent results to keep
        dry_run: If True, only show what would be deleted without deleting
    """
    # Ensure the directory exists
    if not os.path.isdir(results_dir):
        logger.warning(f"Directory {results_dir} does not exist. Nothing to clean up.")
        return
    
    # Get all report files
    html_files = glob.glob(os.path.join(results_dir, "game_report_*.html"))
    log_files = glob.glob(os.path.join(results_dir, "game_session_*.log"))
    png_files = glob.glob(os.path.join(results_dir, "game_*.png"))
    
    all_files = html_files + log_files + png_files
    
    # Group files by session (date/time)
    sessions = {}
    
    # Pattern for timestamps in filenames like game_report_20240228_143537.html
    timestamp_pattern = r'(\d{8}_\d{6})'
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        match = re.search(timestamp_pattern, filename)
        
        if match:
            timestamp_str = match.group(1)
            
            # Convert to datetime object for sorting
            try:
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if timestamp_str not in sessions:
                    sessions[timestamp_str] = {
                        'datetime': dt,
                        'files': []
                    }
                
                sessions[timestamp_str]['files'].append(file_path)
            except ValueError:
                logger.warning(f"Could not parse timestamp from file: {filename}")
    
    # Sort sessions by datetime (newest first)
    sorted_sessions = sorted(sessions.values(), key=lambda x: x['datetime'], reverse=True)
    
    # Keep the most recent sessions, delete the rest
    if len(sorted_sessions) <= keep_last:
        logger.info(f"Found {len(sorted_sessions)} sessions, which is <= {keep_last}. No cleanup needed.")
        return
    
    logger.info(f"Found {len(sorted_sessions)} game sessions, keeping the {keep_last} most recent.")
    
    for i, session in enumerate(sorted_sessions):
        if i < keep_last:
            logger.info(f"Keeping session from {session['datetime']}")
        else:
            # This session should be deleted
            logger.info(f"{'Would delete' if dry_run else 'Deleting'} session from {session['datetime']}")
            
            if not dry_run:
                for file_path in session['files']:
                    try:
                        os.remove(file_path)
                        logger.debug(f"Deleted: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Clean up old game results")
    parser.add_argument("--keep", type=int, default=3, help="Number of recent game results to keep")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()
    
    logger.info("Starting cleanup process")
    cleanup_game_results(keep_last=args.keep, dry_run=args.dry_run)
    logger.info("Cleanup complete")

if __name__ == "__main__":
    main()
