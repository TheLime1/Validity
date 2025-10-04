#!/usr/bin/env python3
"""
Quick test to verify the proxy scraper workflow improvements
"""

from proxy_scraper import ProxyValidator
import os


def test_workflow():
    print("🧪 Testing Enhanced Proxy Scraper Workflow...")
    print("=" * 60)

    # Initialize validator
    validator = ProxyValidator()

    # Test 1: Dead proxy loading with cleanup
    print("\n1️⃣  Testing dead proxy loading and 30-day cleanup:")
    validator.load_dead_proxies()
    print(f"   ✅ Loaded {len(validator.dead_proxies)} dead proxies")
    print(
        f"   ✅ Dead proxies with timestamps: {len(validator.dead_proxies_with_dates)}")

    # Test 2: Check if data files exist
    print("\n2️⃣  Checking data files:")
    for proxy_type in ['http', 'socks5']:
        file_path = os.path.join(validator.data_dir, f"{proxy_type}.txt")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip()
                         and not line.startswith('#')]
            print(f"   📄 {proxy_type}.txt: {len(lines)} proxies")
        else:
            print(f"   📄 {proxy_type}.txt: File not found")

    # Test 3: Check log files
    print("\n3️⃣  Checking log files:")

    if os.path.exists(validator.proxy_log_file):
        import csv
        with open(validator.proxy_log_file, 'r') as f:
            reader = csv.reader(f)
            lines = list(reader)
        print(f"   📊 Validation log: {len(lines)-1} records")  # -1 for header
    else:
        print(f"   📊 Validation log: Not found (will be created on first run)")

    if os.path.exists(validator.dead_proxies_file):
        with open(validator.dead_proxies_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()
                     and not line.startswith('#')]
        print(f"   💀 Dead proxies: {len(lines)} entries")
    else:
        print(f"   💀 Dead proxies: Not found")

    # Test 4: Sources loading
    print("\n4️⃣  Testing sources loading:")
    sources = validator.load_sources()
    for proxy_type, source_list in sources.items():
        print(f"   🌐 {proxy_type.upper()}: {len(source_list)} sources")
        for i, source in enumerate(source_list, 1):
            print(f"      {i}. {source}")

    print("\n" + "=" * 60)
    print("✅ Workflow test completed!")
    print("\n💡 Workflow Summary:")
    print("   1. Load dead proxies (with 30-day cleanup)")
    print("   2. Validate existing data folder proxies")
    print("   3. Remove dead proxies from data files")
    print("   4. Fetch new proxies from sources")
    print("   5. Skip proxies in dead_proxies database")
    print("   6. Validate new proxies with detailed logging")
    print("   7. Save results with periodic auto-save")


if __name__ == "__main__":
    test_workflow()
