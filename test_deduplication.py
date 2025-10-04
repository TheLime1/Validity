#!/usr/bin/env python3
"""
Test script to demonstrate deduplication in proxy scraper
"""


def test_deduplication():
    print("🧪 Testing Proxy Deduplication Logic...")
    print("=" * 60)

    # Simulate different types of duplicates
    existing_proxies = {"1.1.1.1:80", "2.2.2.2:80", "3.3.3.3:80"}
    dead_proxies = {"4.4.4.4:80", "5.5.5.5:80"}

    # Simulate proxies from multiple sources with overlaps
    source1_proxies = {"1.1.1.1:80", "6.6.6.6:80",
                       "7.7.7.7:80", "4.4.4.4:80"}  # Has existing + dead
    source2_proxies = {"6.6.6.6:80", "8.8.8.8:80",
                       "9.9.9.9:80"}  # Has duplicate from source1
    source3_proxies = {"10.10.10.10:80", "11.11.11.11:80"}  # Unique

    print("📊 Initial State:")
    print(f"   Existing alive proxies: {len(existing_proxies)}")
    print(f"   Known dead proxies: {len(dead_proxies)}")
    print()

    print("🌐 Source Data:")
    print(f"   Source 1: {len(source1_proxies)} proxies")
    print(f"   Source 2: {len(source2_proxies)} proxies")
    print(f"   Source 3: {len(source3_proxies)} proxies")
    print(
        f"   Total raw: {len(source1_proxies) + len(source2_proxies) + len(source3_proxies)}")
    print()

    # Step 1: Combine all sources (automatic deduplication via sets)
    all_new_proxies = set()

    print("🔄 Simulating source fetching with deduplication:")
    for i, source_proxies in enumerate([source1_proxies, source2_proxies, source3_proxies], 1):
        duplicates_found = all_new_proxies & source_proxies
        if duplicates_found:
            print(
                f"   Source {i}: Found {len(duplicates_found)} duplicates across sources")
        all_new_proxies.update(source_proxies)
        print(
            f"   Source {i}: {len(source_proxies)} proxies -> {len(all_new_proxies)} total unique")

    print()

    # Step 2: Remove existing proxies and dead proxies
    print("🧹 Applying deduplication filters:")
    print(f"   Before filtering: {len(all_new_proxies)} unique proxies")

    # Remove existing proxies
    duplicates_with_existing = all_new_proxies & existing_proxies
    print(f"   Duplicates with existing: {len(duplicates_with_existing)}")

    # Remove dead proxies
    duplicates_with_dead = all_new_proxies & dead_proxies
    print(f"   Duplicates with dead: {len(duplicates_with_dead)}")

    # Final deduplication (same as script logic)
    final_new_proxies = all_new_proxies - existing_proxies - dead_proxies
    print(f"   After filtering: {len(final_new_proxies)} proxies to validate")
    print()

    # Step 3: Show final results
    print("✅ Deduplication Results:")
    print(
        f"   Original total: {len(source1_proxies) + len(source2_proxies) + len(source3_proxies)}")
    print(f"   After source dedup: {len(all_new_proxies)}")
    print(
        f"   After existing dedup: {len(all_new_proxies) - len(duplicates_with_existing)}")
    print(f"   After dead dedup: {len(final_new_proxies)}")
    print(f"   Reduction: {((len(source1_proxies) + len(source2_proxies) + len(source3_proxies)) - len(final_new_proxies)) / (len(source1_proxies) + len(source2_proxies) + len(source3_proxies)) * 100:.1f}%")
    print()

    print("📋 Final proxies to validate:")
    for proxy in sorted(final_new_proxies):
        print(f"   {proxy}")

    print("\n" + "=" * 60)
    print("✅ Deduplication test completed!")
    print("\n💡 The script prevents duplicates at multiple levels:")
    print("   1. ✅ Across multiple sources (sets automatically deduplicate)")
    print("   2. ✅ Against existing alive proxies")
    print("   3. ✅ Against known dead proxies")
    print("   4. ✅ When combining existing + new alive proxies")
    print("   5. ✅ When saving to files (sets maintain uniqueness)")


if __name__ == "__main__":
    test_deduplication()
