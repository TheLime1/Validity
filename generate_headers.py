#!/usr/bin/env python3
"""
Random Headers Generator
Generates 1000 realistic browser headers for proxy validation
"""

import json
import os
import random
from datetime import datetime


def generate_random_headers():
    """Generate 1000 random realistic browser headers"""

    # Common user agents from different browsers and platforms
    user_agents = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

        # Chrome macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",

        # Firefox macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",

        # Safari macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",

        # Edge Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60",

        # Chrome Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",

        # Firefox Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",

        # Mobile browsers
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]

    # Common accept headers
    accept_headers = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "application/json,text/plain,*/*",
        "*/*",
    ]

    # Accept-Language options
    accept_languages = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.8,es;q=0.6",
        "en-US,en;q=0.9,fr;q=0.8",
        "en-US,en;q=0.9,de;q=0.8",
        "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "fr-FR,fr;q=0.9,en;q=0.8",
        "de-DE,de;q=0.9,en;q=0.8",
        "es-ES,es;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9,en;q=0.8",
    ]

    # Accept-Encoding options
    accept_encodings = [
        "gzip, deflate, br",
        "gzip, deflate",
        "gzip",
        "br",
    ]

    # Connection options
    connections = ["keep-alive", "close"]

    # DNT options
    dnt_options = ["1", "0"]

    # Upgrade-Insecure-Requests
    upgrade_insecure = ["1", "0"]

    # Sec-Fetch options
    sec_fetch_dest = ["document", "empty", "image", "script", "style"]
    sec_fetch_mode = ["navigate", "cors", "no-cors", "same-origin"]
    sec_fetch_site = ["none", "same-origin", "same-site", "cross-site"]

    headers_list = []

    for i in range(1000):
        # Create a random header set
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": random.choice(accept_headers),
            "Accept-Language": random.choice(accept_languages),
            "Accept-Encoding": random.choice(accept_encodings),
            "Connection": random.choice(connections),
        }

        # Randomly add optional headers
        if random.random() > 0.3:  # 70% chance
            headers["DNT"] = random.choice(dnt_options)

        if random.random() > 0.4:  # 60% chance
            headers["Upgrade-Insecure-Requests"] = random.choice(
                upgrade_insecure)

        if random.random() > 0.5:  # 50% chance
            headers["Sec-Fetch-Dest"] = random.choice(sec_fetch_dest)
            headers["Sec-Fetch-Mode"] = random.choice(sec_fetch_mode)
            headers["Sec-Fetch-Site"] = random.choice(sec_fetch_site)

        if random.random() > 0.7:  # 30% chance
            headers["Cache-Control"] = random.choice(["no-cache", "max-age=0"])

        if random.random() > 0.8:  # 20% chance
            headers["Pragma"] = "no-cache"

        if random.random() > 0.6:  # 40% chance
            headers["Sec-Ch-Ua"] = '"Google Chrome";v="118", "Chromium";v="118", "Not=A?Brand";v="99"'
            headers["Sec-Ch-Ua-Mobile"] = "?0"
            headers["Sec-Ch-Ua-Platform"] = random.choice(
                ['"Windows"', '"macOS"', '"Linux"'])

        headers_list.append(headers)

    return headers_list


def save_headers_to_files(headers_list, data_dir="data"):
    """Save headers to both JSON and TXT formats"""

    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Save as JSON for programmatic use
    json_file = os.path.join(data_dir, "headers.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_headers": len(headers_list),
            "headers": headers_list
        }, f, indent=2, ensure_ascii=False)

    # Save as TXT for human reading
    txt_file = os.path.join(data_dir, "headers.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"# Random Headers Database\n")
        f.write(
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total headers: {len(headers_list)}\n")
        f.write(f"# Purpose: Randomize HTTP headers for proxy validation\n\n")

        for i, headers in enumerate(headers_list, 1):
            f.write(f"# Header Set {i}\n")
            for key, value in headers.items():
                f.write(f"{key}: {value}\n")
            f.write("\n")

    print(f"✅ Generated {len(headers_list)} random headers")
    print(f"📄 Saved to: {json_file}")
    print(f"📄 Saved to: {txt_file}")

    return json_file, txt_file


def load_random_header(json_file="data/headers.json"):
    """Helper function to load a random header from the generated file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return random.choice(data['headers'])
    except Exception as e:
        print(f"Error loading headers: {e}")
        # Fallback header
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }


if __name__ == "__main__":
    print("🔄 Generating 1000 random headers...")
    headers = generate_random_headers()
    save_headers_to_files(headers)

    print("\n🧪 Testing random header loading...")
    sample_header = load_random_header()
    print("Sample header:")
    for key, value in sample_header.items():
        print(f"  {key}: {value}")

    print("\n✅ Headers generation completed!")
