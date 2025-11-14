#!/usr/bin/env python3
"""
Proxy Scraper and Validator
Daily script to maintain up to 1000 alive proxies per type (HTTP/SOCKS5)

Features:
- ALWAYS performs git pull at startup to get latest changes
- Optional git push on exit with --push flag
- Multi-threaded validation with auto-save
- Dead proxy tracking and cleanup
"""

import argparse
import csv
import multiprocessing
import os
import random
import re
import requests
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta


class ProxyValidator:
    # Maximum CSV file size in bytes (95MB to stay under GitHub's 100MB limit with buffer)
    MAX_CSV_SIZE = 95 * 1024 * 1024  # 95MB in bytes
    
    def __init__(self, timeout=3, max_workers=None, batch_size=50, push_on_exit=False):
        self.timeout = timeout
        # Dynamic worker adjustment based on system capabilities
        if max_workers is None:
            self.max_workers = min(
                150, max(25, multiprocessing.cpu_count() * 8))
        else:
            self.max_workers = max_workers
        self.batch_size = batch_size  # Equal amount to take from each source per batch
        self.data_dir = "data"
        self.sources_file = "sources.csv"
        self.push_on_exit = push_on_exit  # Flag to determine if we should git push on exit

        # Dead proxies tracking with timestamps
        self.dead_proxies_file = os.path.join(
            self.data_dir, "dead_proxies.txt")
        self.dead_proxies = set()  # Set of proxy IPs for fast lookup
        self.dead_proxies_with_dates = {}  # Dict with proxy -> timestamp mapping

        # Detailed logging for quality analysis with rotation support
        self.proxy_log_base = os.path.join(
            self.data_dir, "proxy_validation_log")
        self.proxy_log_file = None  # Will be set by _init_proxy_log()
        self.proxy_log_lock = threading.Lock()
        self._init_proxy_log()

        # Source tracking for quality analysis
        self.proxy_sources = {}  # proxy -> source_url mapping

        # Periodic saving
        self.alive_proxies_http = set()
        self.alive_proxies_socks5 = set()
        self.last_save_time = time.time()
        self.save_interval = 10  # Save every 10 seconds
        self.shutdown_requested = False

        # Lock for thread-safe operations
        self.save_lock = threading.Lock()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self.signal_handler)

        # Test URLs for validation
        self.test_urls = [
            "http://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "http://icanhazip.com"
        ]

    def log(self, message):
        """Simple logging with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def git_pull_first(self):
        """Pull latest changes from remote repository before starting"""
        try:
            self.log("⬇️  Pulling latest changes from remote repository...")

            # First, fetch the latest changes
            subprocess.run(['git', 'fetch'],
                           cwd=os.path.dirname(os.path.abspath(__file__)),
                           capture_output=True, text=True, check=True)

            # Then pull to merge changes
            result = subprocess.run(['git', 'pull'],
                                    cwd=os.path.dirname(
                                        os.path.abspath(__file__)),
                                    capture_output=True, text=True, check=True)

            if "Already up to date" in result.stdout:
                self.log("✅ Repository is already up to date.")
            else:
                self.log(
                    "✅ Successfully pulled latest changes from remote repository!")
                # Show what was updated if there were changes
                if result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines[:3]:  # Show first 3 lines of output
                        if line.strip():
                            self.log(f"   {line.strip()}")

        except subprocess.CalledProcessError as e:
            self.log(f"❌ Git pull failed: {e}")
            if e.stderr:
                error_msg = e.stderr.strip()
                self.log(f"   Error details: {error_msg}")
                # Check for common git pull issues
                if "uncommitted changes" in error_msg.lower():
                    self.log(
                        "   💡 Tip: You have uncommitted changes. Use --push to auto-commit, or commit/stash them manually.")
                elif "merge conflict" in error_msg.lower():
                    self.log(
                        "   💡 Tip: Resolve merge conflicts manually before running the script.")
            self.log("⚠️  Continuing with local version...")
        except Exception as e:
            self.log(f"❌ Unexpected error during git pull: {e}")
            self.log("⚠️  Continuing with local version...")

    def git_push_changes(self):
        """Add all changes and push to git repository if --push flag is enabled"""
        if not self.push_on_exit:
            return

        try:
            self.log("🔄 Adding changes to git...")
            # Add all changes
            result = subprocess.run(['git', 'add', '.'],
                                    cwd=os.path.dirname(
                                        os.path.abspath(__file__)),
                                    capture_output=True, text=True, check=True)

            # Check if there are any changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'],
                                    cwd=os.path.dirname(
                                        os.path.abspath(__file__)),
                                    capture_output=True, text=True, check=True)

            if result.stdout.strip():  # If there are changes
                # Commit with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"Auto-update proxy data - {timestamp}"

                self.log(f"📝 Committing changes: {commit_msg}")
                subprocess.run(['git', 'commit', '-m', commit_msg],
                               cwd=os.path.dirname(os.path.abspath(__file__)),
                               capture_output=True, text=True, check=True)

                # Push to remote
                self.log("⬆️  Pushing changes to remote repository...")
                subprocess.run(['git', 'push'],
                               cwd=os.path.dirname(os.path.abspath(__file__)),
                               capture_output=True, text=True, check=True)

                self.log("✅ Successfully pushed changes to git repository!")
            else:
                self.log("ℹ️  No changes to commit.")

        except subprocess.CalledProcessError as e:
            self.log(f"❌ Git operation failed: {e}")
            if e.stderr:
                self.log(f"   Error details: {e.stderr.strip()}")
        except Exception as e:
            self.log(f"❌ Unexpected error during git operations: {e}")

    def log_performance_config(self):
        """Log the current performance configuration"""
        cpu_count = multiprocessing.cpu_count()
        self.log("🔧 Performance Configuration:")
        self.log(f"   CPU Cores: {cpu_count}")
        self.log(
            f"   Max Workers: {self.max_workers} (dynamic: {cpu_count * 8}, capped: 25-150)")
        self.log(f"   Timeout: {self.timeout}s (optimized for speed)")
        self.log(
            f"   Batch Size: {self.batch_size} (smaller = more frequent rotation)")

        # Performance tier classification
        if self.max_workers >= 120:
            tier = "HIGH-PERFORMANCE"
        elif self.max_workers >= 75:
            tier = "BALANCED"
        else:
            tier = "CONSERVATIVE"
        self.log(f"   Performance Tier: {tier}")

    def _get_active_log_file(self):
        """Get the current active log file or create a new one if needed"""
        # Find existing log files
        log_files = []
        for file in os.listdir(self.data_dir):
            if file.startswith("proxy_validation_log") and file.endswith(".csv"):
                log_files.append(file)
        
        if not log_files:
            # No existing log files, create the first one
            return os.path.join(self.data_dir, "proxy_validation_log.csv")
        
        # Sort log files to get the latest one
        log_files.sort()
        latest_log = os.path.join(self.data_dir, log_files[-1])
        
        # Check if the latest log file is under the size limit
        if os.path.exists(latest_log):
            file_size = os.path.getsize(latest_log)
            if file_size < self.MAX_CSV_SIZE:
                return latest_log
        
        # Need to create a new log file
        # Extract number from last file or start at 1
        import re
        match = re.search(r'proxy_validation_log_(\d+)\.csv', log_files[-1])
        if match:
            next_num = int(match.group(1)) + 1
        else:
            # First file was proxy_validation_log.csv, next is _1.csv
            next_num = 1
        
        return os.path.join(self.data_dir, f"proxy_validation_log_{next_num}.csv")

    def _init_proxy_log(self):
        """Initialize the detailed proxy validation log CSV file with rotation support"""
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Clean up old log entries (30+ days)
        self._cleanup_old_log_entries()
        
        # Get the active log file
        self.proxy_log_file = self._get_active_log_file()

        # Create CSV header if file doesn't exist
        if not os.path.exists(self.proxy_log_file):
            with open(self.proxy_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'proxy', 'proxy_type', 'source_url',
                    'status', 'response_time_ms', 'test_url_used'
                ])

    def _cleanup_old_log_entries(self):
        """Remove log entries older than 30 days from all log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # Find all log files
            log_files = []
            for file in os.listdir(self.data_dir):
                if file.startswith("proxy_validation_log") and file.endswith(".csv"):
                    log_files.append(os.path.join(self.data_dir, file))
            
            if not log_files:
                return
            
            total_removed = 0
            files_to_delete = []
            
            for log_file in log_files:
                try:
                    # Read the CSV file
                    rows_to_keep = []
                    header = None
                    removed_count = 0
                    
                    with open(log_file, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        
                        if header:
                            rows_to_keep.append(header)
                        
                        for row in reader:
                            if len(row) == 0:
                                continue
                            
                            try:
                                # Parse timestamp (first column)
                                timestamp_str = row[0]
                                entry_date = datetime.fromisoformat(timestamp_str)
                                
                                # Keep entries newer than 30 days
                                if entry_date >= cutoff_date:
                                    rows_to_keep.append(row)
                                else:
                                    removed_count += 1
                            except (ValueError, IndexError):
                                # Keep rows with invalid timestamps (better safe than sorry)
                                rows_to_keep.append(row)
                    
                    # If file has only header or no valid entries, mark for deletion
                    if len(rows_to_keep) <= 1:
                        files_to_delete.append(log_file)
                        total_removed += removed_count
                    # Otherwise rewrite the file with cleaned data
                    elif removed_count > 0:
                        with open(log_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerows(rows_to_keep)
                        total_removed += removed_count
                        
                except Exception as e:
                    self.log(f"Error cleaning log file {log_file}: {e}")
            
            # Delete empty log files (but keep at least one)
            if len(files_to_delete) < len(log_files):
                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                        self.log(f"Removed empty log file: {os.path.basename(file_path)}")
                    except Exception as e:
                        self.log(f"Error removing log file {file_path}: {e}")
            
            if total_removed > 0:
                self.log(f"Cleaned {total_removed} log entries older than 30 days")
                
        except Exception as e:
            self.log(f"Error during log cleanup: {e}")

    def log_proxy_validation(self, proxy, proxy_type, source_url, status, response_time_ms=None, test_url=None):
        """Log detailed proxy validation results to CSV file with automatic rotation"""
        with self.proxy_log_lock:
            try:
                # Check if current log file exceeds size limit
                if os.path.exists(self.proxy_log_file):
                    file_size = os.path.getsize(self.proxy_log_file)
                    if file_size >= self.MAX_CSV_SIZE:
                        # Rotate to a new log file
                        self.proxy_log_file = self._get_active_log_file()
                        
                        # Create new file with header
                        if not os.path.exists(self.proxy_log_file):
                            with open(self.proxy_log_file, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow([
                                    'timestamp', 'proxy', 'proxy_type', 'source_url',
                                    'status', 'response_time_ms', 'test_url_used'
                                ])
                            self.log(f"Rotated to new log file: {os.path.basename(self.proxy_log_file)}")
                
                # Append to the current log file
                with open(self.proxy_log_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        proxy,
                        proxy_type,
                        source_url or 'existing',
                        status,
                        response_time_ms or '',
                        test_url or ''
                    ])
            except Exception as e:
                self.log(f"Error logging proxy validation: {e}")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C and other termination signals"""
        self.log("\n⚠️  Shutdown signal received. Saving current progress...")
        self.shutdown_requested = True
        self.save_current_progress()
        self.git_push_changes()  # Push changes if --push flag is enabled
        self.log("✅ Progress saved. Exiting gracefully.")
        sys.exit(0)

    def load_dead_proxies(self):
        """Load previously identified dead proxies and clean old entries (30+ days)"""
        if not os.path.exists(self.dead_proxies_file):
            self.log("No dead proxies file found, creating new one")
            return

        try:
            current_time = datetime.now()
            cutoff_date = current_time - timedelta(days=30)

            valid_dead_proxies = []
            old_proxies_count = 0

            with open(self.dead_proxies_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse line format: "proxy,timestamp" or just "proxy" (legacy)
                    if ',' in line:
                        proxy, timestamp_str = line.split(',', 1)
                        try:
                            proxy_date = datetime.fromisoformat(timestamp_str)
                            if proxy_date >= cutoff_date:
                                # Keep proxy (not older than 30 days)
                                self.dead_proxies.add(proxy)
                                self.dead_proxies_with_dates[proxy] = proxy_date
                                valid_dead_proxies.append(
                                    f"{proxy},{timestamp_str}")
                            else:
                                old_proxies_count += 1
                        except ValueError:
                            # Invalid timestamp, treat as legacy format
                            self.dead_proxies.add(proxy)
                            # Add current timestamp for legacy entries
                            current_timestamp = current_time.isoformat()
                            self.dead_proxies_with_dates[proxy] = current_time
                            valid_dead_proxies.append(
                                f"{proxy},{current_timestamp}")
                    else:
                        # Legacy format without timestamp
                        self.dead_proxies.add(line)
                        current_timestamp = current_time.isoformat()
                        self.dead_proxies_with_dates[line] = current_time
                        valid_dead_proxies.append(
                            f"{line},{current_timestamp}")

            # Rewrite the file with only valid (not old) dead proxies
            if old_proxies_count > 0:
                self._rewrite_dead_proxies_file(valid_dead_proxies)
                self.log(
                    f"Cleaned {old_proxies_count} dead proxies older than 30 days")

            self.log(f"Loaded {len(self.dead_proxies)} dead proxies to skip")

        except Exception as e:
            self.log(f"Error loading dead proxies: {e}")

    def _rewrite_dead_proxies_file(self, valid_entries):
        """Rewrite the dead proxies file with only valid entries"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.dead_proxies_file, 'w', encoding='utf-8') as f:
                f.write("# Dead Proxies Database with Timestamps\n")
                f.write("# Format: proxy_ip:port,timestamp\n")
                f.write("# Auto-cleanup: Entries older than 30 days are removed\n")
                f.write(f"# Last cleaned: {datetime.now().isoformat()}\n\n")
                for entry in valid_entries:
                    f.write(f"{entry}\n")
        except Exception as e:
            self.log(f"Error rewriting dead proxies file: {e}")

    def save_dead_proxy(self, proxy):
        """Add a dead proxy to the dead proxies set and file with timestamp"""
        if proxy not in self.dead_proxies:
            self.dead_proxies.add(proxy)
            current_time = datetime.now()
            self.dead_proxies_with_dates[proxy] = current_time

            # Append to file immediately with timestamp
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                with open(self.dead_proxies_file, 'a', encoding='utf-8') as f:
                    f.write(f"{proxy},{current_time.isoformat()}\n")
            except Exception as e:
                self.log(f"Error saving dead proxy {proxy}: {e}")

    def save_current_progress(self):
        """Save current progress to files"""
        with self.save_lock:
            if self.alive_proxies_http:
                self.save_proxies(self.alive_proxies_http, "http")
            if self.alive_proxies_socks5:
                self.save_proxies(self.alive_proxies_socks5, "socks5")
            self.log(
                f"💾 Progress saved at {datetime.now().strftime('%H:%M:%S')}")

    def periodic_save_worker(self):
        """Background thread that saves progress every 10 seconds"""
        while not self.shutdown_requested:
            time.sleep(1)
            if time.time() - self.last_save_time >= self.save_interval:
                self.save_current_progress()
                self.last_save_time = time.time()

    def is_proxy_alive(self, proxy, proxy_type, source_url=None):
        """Check if a proxy is alive by making a test request"""
        if self.shutdown_requested:
            return False

        # Skip if proxy is already known to be dead
        if proxy in self.dead_proxies:
            return False

        try:
            proxy_dict = {}
            if proxy_type == "http":
                proxy_dict = {"http": f"http://{proxy}",
                              "https": f"http://{proxy}"}
            elif proxy_type == "socks5":
                proxy_dict = {"http": f"socks5://{proxy}",
                              "https": f"socks5://{proxy}"}

            # Try multiple test URLs for better reliability
            for test_url in self.test_urls[:2]:  # Use first 2 URLs
                if self.shutdown_requested:
                    return False
                try:
                    start_time = time.time()
                    response = requests.get(
                        test_url,
                        proxies=proxy_dict,
                        timeout=self.timeout,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    response_time_ms = int((time.time() - start_time) * 1000)

                    if response.status_code == 200:
                        # Log successful validation
                        self.log_proxy_validation(
                            proxy, proxy_type, source_url, 'alive',
                            response_time_ms, test_url
                        )
                        return True
                except requests.RequestException:
                    continue

            # If we reach here, proxy is dead
            self.log_proxy_validation(
                proxy, proxy_type, source_url, 'dead'
            )
            self.save_dead_proxy(proxy)
            return False
        except Exception:
            self.log_proxy_validation(
                proxy, proxy_type, source_url, 'error'
            )
            self.save_dead_proxy(proxy)
            return False

    def remove_proxy_from_data_file(self, proxy, proxy_type):
        """Remove a dead proxy from the active data file"""
        file_path = os.path.join(self.data_dir, f"{proxy_type}.txt")

        if not os.path.exists(file_path):
            return

        try:
            # Read all lines
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Filter out the dead proxy and rewrite file
            updated_lines = []
            removed = False
            for line in lines:
                stripped_line = line.strip()
                if stripped_line == proxy:
                    removed = True
                    continue  # Skip this line (remove the proxy)
                updated_lines.append(line)

            if removed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
                self.log(f"Removed dead proxy {proxy} from {proxy_type}.txt")

        except Exception as e:
            self.log(
                f"Error removing proxy {proxy} from {proxy_type} file: {e}")

    def validate_existing_proxies(self, proxy_type):
        """
        Validate existing proxies in data folder and remove dead ones
        Returns set of alive proxies
        """
        file_path = os.path.join(self.data_dir, f"{proxy_type}.txt")
        alive_proxies = set()

        if not os.path.exists(file_path):
            self.log(f"No existing {proxy_type} file found, creating new one")
            return alive_proxies

        # Read existing proxies
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_proxies = [
                line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not existing_proxies:
            self.log(f"No existing {proxy_type} proxies to validate")
            return alive_proxies

        # Filter out known dead proxies (skip testing them)
        proxies_to_check = [
            p for p in existing_proxies if p not in self.dead_proxies]
        skipped_dead = len(existing_proxies) - len(proxies_to_check)

        # Scramble testing order for better load distribution
        random.shuffle(proxies_to_check)
        self.log(
            f"🎲 Scrambled {len(proxies_to_check)} existing {proxy_type} proxies for random testing order")

        # Remove known dead proxies from the data file
        if skipped_dead > 0:
            self.log(
                f"Found {skipped_dead} known dead {proxy_type} proxies in data file")
            for proxy in existing_proxies:
                if proxy in self.dead_proxies:
                    self.remove_proxy_from_data_file(proxy, proxy_type)

        if not proxies_to_check:
            self.log(f"All existing {proxy_type} proxies are known to be dead")
            return alive_proxies

        self.log(
            f"Validating {len(proxies_to_check)} existing {proxy_type} proxies...")

        # Validate proxies with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.is_proxy_alive, proxy, proxy_type, 'existing'): proxy
                for proxy in proxies_to_check
            }

            for future in as_completed(future_to_proxy):
                if self.shutdown_requested:
                    break

                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        alive_proxies.add(proxy)
                        self.log(f"✓ {proxy} is alive")
                    else:
                        self.log(
                            f"✗ {proxy} is dead - removing from data file")
                        # Remove dead proxy from data file
                        self.remove_proxy_from_data_file(proxy, proxy_type)
                except Exception as e:
                    self.log(f"✗ {proxy} validation error: {e}")
                    self.save_dead_proxy(proxy)
                    self.remove_proxy_from_data_file(proxy, proxy_type)

        self.log(
            f"Found {len(alive_proxies)} alive {proxy_type} proxies out of {len(proxies_to_check)} checked")
        return alive_proxies

    def fetch_proxies_from_source(self, url, proxy_type):
        """
        Fetch proxies from a source URL and clean them
        Returns set of clean proxy addresses
        """
        try:
            self.log(f"Fetching {proxy_type} proxies from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            proxies = set()
            for line in response.text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Remove protocol prefixes
                if line.startswith('http://'):
                    line = line[7:]
                elif line.startswith('https://'):
                    line = line[8:]
                elif line.startswith('socks5://'):
                    line = line[9:]
                elif line.startswith('socks4://'):
                    line = line[9:]

                # Basic validation: should contain IP:PORT format
                if ':' in line and len(line.split(':')) == 2:
                    try:
                        ip, port = line.split(':')
                        # Basic IP format check
                        if ip.count('.') == 3 and port.isdigit():
                            proxies.add(line)
                            # Track source for this proxy
                            self.proxy_sources[line] = url
                    except Exception:
                        continue

            self.log(
                f"Extracted {len(proxies)} {proxy_type} proxies from source")
            return proxies

        except Exception as e:
            self.log(f"Error fetching from {url}: {e}")
            return set()

    def validate_new_proxies(self, proxies, proxy_type, existing_proxies):
        """
        Validate new proxies and return alive ones not in existing set
        Enhanced with dead proxy checking and periodic saving
        """
        # Enhanced deduplication: remove existing proxies AND known dead proxies
        new_proxies = proxies - existing_proxies - self.dead_proxies

        if not new_proxies:
            self.log(
                f"No new {proxy_type} proxies to validate (after deduplication)")
            return set()

        # Convert to list and scramble testing order
        new_proxies_list = list(new_proxies)
        random.shuffle(new_proxies_list)
        self.log(
            f"🎲 Scrambled {len(new_proxies_list)} new {proxy_type} proxies for random testing order")

        self.log(
            f"Validating {len(new_proxies_list)} new {proxy_type} proxies (skipped {len(proxies & self.dead_proxies)} known dead)...")
        alive_new_proxies = set()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.is_proxy_alive, proxy, proxy_type, self.proxy_sources.get(proxy)): proxy
                for proxy in new_proxies_list
            }

            for future in as_completed(future_to_proxy):
                if self.shutdown_requested:
                    break

                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        # Double-check for duplicates even among alive proxies
                        is_duplicate = False
                        if proxy_type == "http" and proxy in self.alive_proxies_http:
                            is_duplicate = True
                        elif proxy_type == "socks5" and proxy in self.alive_proxies_socks5:
                            is_duplicate = True

                        if not is_duplicate:
                            alive_new_proxies.add(proxy)
                            # Add to instance variable for periodic saving
                            if proxy_type == "http":
                                self.alive_proxies_http.add(proxy)
                            else:
                                self.alive_proxies_socks5.add(proxy)
                            self.log(f"✓ New {proxy} is alive")
                        else:
                            self.log(
                                f"⚠ Skipped duplicate alive proxy: {proxy}")
                    else:
                        self.log(f"✗ New {proxy} is dead")
                except Exception as e:
                    self.log(f"✗ New {proxy} validation error: {e}")
                    self.save_dead_proxy(proxy)

        self.log(
            f"Found {len(alive_new_proxies)} alive new {proxy_type} proxies")
        return alive_new_proxies

    def validate_new_proxies_fair_rotation(self, proxies_by_source, proxy_type, existing_proxies):
        """
        Validate new proxies using fair rotation system:
        1. Take equal amounts from each source
        2. Scramble the batch
        3. Test the batch
        4. Repeat until all sources exhausted
        """
        # Organize proxies by source and filter out existing/dead
        source_queues = {}
        total_new_proxies = 0

        for source_url, proxies in proxies_by_source.items():
            # Enhanced deduplication: remove existing proxies AND known dead proxies
            new_proxies = proxies - existing_proxies - self.dead_proxies
            if new_proxies:
                source_queues[source_url] = list(new_proxies)
                # Shuffle each source's proxies
                random.shuffle(source_queues[source_url])
                total_new_proxies += len(new_proxies)
                self.log(
                    f"📍 {source_url}: {len(new_proxies)} new proxies (after deduplication)")

        if not source_queues:
            self.log(
                f"No new {proxy_type} proxies to validate (after deduplication)")
            return set()

        self.log(
            f"🔄 Fair rotation validation: {total_new_proxies} new {proxy_type} proxies from {len(source_queues)} sources")
        self.log(
            f"📦 Batch size: {self.batch_size} proxies per source per round")

        alive_new_proxies = set()
        round_number = 1

        # Continue until all source queues are empty
        while any(source_queues.values()):
            if self.shutdown_requested:
                break

            # Collect equal amounts from each source for this batch
            current_batch = []
            sources_in_batch = []

            for source_url in list(source_queues.keys()):
                if not source_queues[source_url]:
                    continue  # Skip empty sources

                # Take up to batch_size proxies from this source
                batch_from_source = source_queues[source_url][:self.batch_size]
                source_queues[source_url] = source_queues[source_url][self.batch_size:]

                current_batch.extend(batch_from_source)
                sources_in_batch.append((source_url, len(batch_from_source)))

                # Remove source if depleted
                if not source_queues[source_url]:
                    del source_queues[source_url]

            if not current_batch:
                break

            # Scramble the batch for fair testing order
            random.shuffle(current_batch)

            self.log(
                f"🎲 Round {round_number}: Testing {len(current_batch)} scrambled proxies")
            for source_url, count in sources_in_batch:
                self.log(f"   📤 {count} from {source_url}")

            # Test the scrambled batch concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_proxy = {
                    executor.submit(self.is_proxy_alive, proxy, proxy_type, self.proxy_sources.get(proxy)): proxy
                    for proxy in current_batch
                }

                batch_alive = 0
                for future in as_completed(future_to_proxy):
                    if self.shutdown_requested:
                        break

                    proxy = future_to_proxy[future]
                    try:
                        if future.result():
                            alive_new_proxies.add(proxy)
                            batch_alive += 1
                            # Add to instance variable for periodic saving
                            if proxy_type == "http":
                                self.alive_proxies_http.add(proxy)
                            else:
                                self.alive_proxies_socks5.add(proxy)
                            self.log(f"✓ {proxy} is alive")
                        else:
                            self.log(f"✗ {proxy} is dead")
                    except Exception as e:
                        self.log(f"✗ {proxy} validation error: {e}")
                        self.save_dead_proxy(proxy)

            self.log(
                f"✅ Round {round_number} completed: {batch_alive}/{len(current_batch)} alive")
            round_number += 1

        self.log(
            f"🏁 Fair rotation completed: Found {len(alive_new_proxies)} alive new {proxy_type} proxies")
        return alive_new_proxies

    def save_proxies(self, proxies, proxy_type):
        """
        Save all valid proxies to file (no limit)
        """
        file_path = os.path.join(self.data_dir, f"{proxy_type}.txt")

        # Convert to list - no limit, save all valid proxies
        proxy_list = list(proxies)

        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(
                f"# Validated {proxy_type.upper()} proxies - Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total proxies: {len(proxy_list)}\n")
            f.write("# Format: IP:PORT\n\n")

            for proxy in proxy_list:
                f.write(f"{proxy}\n")

        self.log(
            f"Saved {len(proxy_list)} {proxy_type} proxies to {file_path}")

    def load_sources(self):
        """
        Load proxy sources from CSV file
        """
        sources = {"http": [], "socks5": []}

        try:
            with open(self.sources_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    proxy_type = row['type'].lower()
                    if proxy_type in sources:
                        sources[proxy_type].append(row['link'])
        except Exception as e:
            self.log(f"Error loading sources: {e}")

        return sources

    def run(self):
        """
        Main execution function with enhanced features
        """
        self.log("Starting proxy validation and scraping...")

        # Always pull latest changes first (mandatory)
        self.git_pull_first()
        self.log("")

        # Log performance configuration
        self.log_performance_config()
        self.log("")

        # Load dead proxies to skip them
        self.load_dead_proxies()

        # Start periodic save thread
        save_thread = threading.Thread(
            target=self.periodic_save_worker, daemon=True)
        save_thread.start()
        self.log("🔄 Auto-save every 10 seconds enabled (Ctrl+C to save and exit)")

        # Load sources
        sources = self.load_sources()

        try:
            for proxy_type in ["http", "socks5"]:
                if self.shutdown_requested:
                    break

                self.log(f"\n{'='*50}")
                self.log(f"Processing {proxy_type.upper()} proxies")
                self.log(f"{'='*50}")

                # Step 1: Validate existing proxies
                alive_existing = self.validate_existing_proxies(proxy_type)

                # Update instance variables
                if proxy_type == "http":
                    self.alive_proxies_http.update(alive_existing)
                else:
                    self.alive_proxies_socks5.update(alive_existing)

                # Step 2: Fetch new proxies from sources (concurrently) and organize by source
                proxies_by_source = {}
                self.log(
                    f"Fetching {proxy_type} proxies from {len(sources[proxy_type])} sources concurrently...")

                with ThreadPoolExecutor(max_workers=len(sources[proxy_type])) as executor:
                    future_to_source = {
                        executor.submit(self.fetch_proxies_from_source, source_url, proxy_type): source_url
                        for source_url in sources[proxy_type]
                    }

                    for future in as_completed(future_to_source):
                        if self.shutdown_requested:
                            break
                        source_url = future_to_source[future]
                        try:
                            new_proxies = future.result()
                            proxies_by_source[source_url] = new_proxies
                            self.log(
                                f"✓ Fetched {len(new_proxies)} proxies from {source_url}")
                        except Exception as e:
                            self.log(
                                f"✗ Error fetching from {source_url}: {e}")

                total_fetched = sum(len(proxies)
                                    for proxies in proxies_by_source.values())
                self.log(
                    f"Total {total_fetched} {proxy_type} proxies fetched from {len(proxies_by_source)} sources")

                # Step 3: Validate new proxies using fair rotation system
                alive_new = self.validate_new_proxies_fair_rotation(
                    proxies_by_source, proxy_type, alive_existing)

                # Step 4: Combine and limit proxies
                all_alive_proxies = alive_existing | alive_new

                # Step 5: Save to file
                self.save_proxies(all_alive_proxies, proxy_type)

                self.log(
                    f"Completed {proxy_type} processing: {len(all_alive_proxies)} total alive proxies")
                self.log(
                    f"Dead proxies database now contains: {len(self.dead_proxies)} entries")

        except KeyboardInterrupt:
            self.log("\n⚠️  Keyboard interrupt received!")
        finally:
            # Final save
            self.save_current_progress()
            # Push changes if --push flag is enabled
            self.git_push_changes()

        self.log("\n" + "="*50)
        self.log("Proxy validation and scraping completed!")
        self.log(
            f"📊 Final stats: {len(self.dead_proxies)} dead proxies tracked")
        self.log("="*50)


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Proxy Scraper and Validator - Daily script to maintain up to 1000 alive proxies per type (HTTP/SOCKS5)"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Automatically git add and push changes when the program finishes or is interrupted with Ctrl+C"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="Timeout in seconds for proxy validation (default: 3)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of worker threads (default: auto-calculated based on CPU)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of proxies to take from each source per batch (default: 50)"
    )

    args = parser.parse_args()

    # Create validator with parsed arguments
    validator = ProxyValidator(
        timeout=args.timeout,
        max_workers=args.max_workers,
        batch_size=args.batch_size,
        push_on_exit=args.push
    )

    if args.push:
        validator.log(
            "🔄 Git push enabled - changes will be automatically pushed on exit")

    validator.run()


if __name__ == "__main__":
    main()
