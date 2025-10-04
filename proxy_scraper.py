#!/usr/bin/env python3
"""
Proxy Scraper and Validator
Daily script to maintain up to 1000 alive proxies per type (HTTP/SOCKS5)
"""

import csv
import os
import requests
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class ProxyValidator:
    def __init__(self, max_proxies_per_type=1000, timeout=5, max_workers=50):
        self.max_proxies_per_type = max_proxies_per_type
        self.timeout = timeout
        self.max_workers = max_workers
        self.data_dir = "data"
        self.sources_file = "sources.csv"

        # Dead proxies tracking
        self.dead_proxies_file = os.path.join(
            self.data_dir, "dead_proxies.txt")
        self.dead_proxies = set()

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

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C and other termination signals"""
        self.log("\n⚠️  Shutdown signal received. Saving current progress...")
        self.shutdown_requested = True
        self.save_current_progress()
        self.log("✅ Progress saved. Exiting gracefully.")
        sys.exit(0)

    def load_dead_proxies(self):
        """Load previously identified dead proxies to skip them"""
        if not os.path.exists(self.dead_proxies_file):
            self.log("No dead proxies file found, creating new one")
            return

        try:
            with open(self.dead_proxies_file, 'r', encoding='utf-8') as f:
                self.dead_proxies = {
                    line.strip() for line in f if line.strip() and not line.startswith('#')}
            self.log(f"Loaded {len(self.dead_proxies)} dead proxies to skip")
        except Exception as e:
            self.log(f"Error loading dead proxies: {e}")

    def save_dead_proxy(self, proxy):
        """Add a dead proxy to the dead proxies set and file"""
        if proxy not in self.dead_proxies:
            self.dead_proxies.add(proxy)
            # Append to file immediately
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                with open(self.dead_proxies_file, 'a', encoding='utf-8') as f:
                    f.write(f"{proxy}\n")
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

    def is_proxy_alive(self, proxy, proxy_type):
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
                    response = requests.get(
                        test_url,
                        proxies=proxy_dict,
                        timeout=self.timeout,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    if response.status_code == 200:
                        return True
                except requests.RequestException:
                    continue

            # If we reach here, proxy is dead
            self.save_dead_proxy(proxy)
            return False
        except Exception:
            self.save_dead_proxy(proxy)
            return False

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

        # Filter out known dead proxies
        proxies_to_check = [
            p for p in existing_proxies if p not in self.dead_proxies]
        skipped_dead = len(existing_proxies) - len(proxies_to_check)

        if skipped_dead > 0:
            self.log(
                f"Skipping {skipped_dead} known dead {proxy_type} proxies")

        if not proxies_to_check:
            self.log(f"All existing {proxy_type} proxies are known to be dead")
            return alive_proxies

        self.log(
            f"Validating {len(proxies_to_check)} existing {proxy_type} proxies...")

        # Validate proxies with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.is_proxy_alive, proxy, proxy_type): proxy
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
                        self.log(f"✗ {proxy} is dead")
                except Exception as e:
                    self.log(f"✗ {proxy} validation error: {e}")
                    self.save_dead_proxy(proxy)

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
                    except:
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

        self.log(
            f"Validating {len(new_proxies)} new {proxy_type} proxies (skipped {len(proxies & self.dead_proxies)} known dead)...")
        alive_new_proxies = set()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.is_proxy_alive, proxy, proxy_type): proxy
                for proxy in new_proxies
            }

            for future in as_completed(future_to_proxy):
                if self.shutdown_requested:
                    break

                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        alive_new_proxies.add(proxy)
                        # Add to instance variable for periodic saving
                        if proxy_type == "http":
                            self.alive_proxies_http.add(proxy)
                        else:
                            self.alive_proxies_socks5.add(proxy)
                        self.log(f"✓ New {proxy} is alive")
                    else:
                        self.log(f"✗ New {proxy} is dead")
                except Exception as e:
                    self.log(f"✗ New {proxy} validation error: {e}")
                    self.save_dead_proxy(proxy)

        self.log(
            f"Found {len(alive_new_proxies)} alive new {proxy_type} proxies")
        return alive_new_proxies

    def save_proxies(self, proxies, proxy_type):
        """
        Save proxies to file, maintaining max limit
        """
        file_path = os.path.join(self.data_dir, f"{proxy_type}.txt")

        # Convert to list and limit to max proxies
        proxy_list = list(proxies)[:self.max_proxies_per_type]

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

                # Step 2: Fetch new proxies from sources (concurrently)
                all_new_proxies = set()
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
                            all_new_proxies.update(new_proxies)
                            self.log(
                                f"✓ Fetched {len(new_proxies)} proxies from {source_url}")
                        except Exception as e:
                            self.log(
                                f"✗ Error fetching from {source_url}: {e}")

                self.log(
                    f"Total {len(all_new_proxies)} unique {proxy_type} proxies fetched from all sources")

                # Step 3: Validate new proxies (with enhanced deduplication)
                alive_new = self.validate_new_proxies(
                    all_new_proxies, proxy_type, alive_existing)

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

        self.log("\n" + "="*50)
        self.log("Proxy validation and scraping completed!")
        self.log(
            f"📊 Final stats: {len(self.dead_proxies)} dead proxies tracked")
        self.log("="*50)


if __name__ == "__main__":
    validator = ProxyValidator()
    validator.run()
