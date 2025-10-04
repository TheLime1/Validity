"""
Headers utility module for proxy validation
Provides random header selection functionality
"""

import json
import random
import os


class HeaderManager:
    def __init__(self, headers_file="data/headers.json"):
        """Initialize with headers file path"""
        self.headers_file = headers_file
        self.headers_cache = None
        self._load_headers()
    
    def _load_headers(self):
        """Load headers from JSON file into memory"""
        try:
            if os.path.exists(self.headers_file):
                with open(self.headers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.headers_cache = data.get('headers', [])
                    print(f"✅ Loaded {len(self.headers_cache)} headers from {self.headers_file}")
            else:
                print(f"⚠️  Headers file not found: {self.headers_file}")
                self._create_fallback_headers()
        except Exception as e:
            print(f"❌ Error loading headers: {e}")
            self._create_fallback_headers()
    
    def _create_fallback_headers(self):
        """Create basic fallback headers if file loading fails"""
        self.headers_cache = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            }
        ]
        print(f"🔄 Using {len(self.headers_cache)} fallback headers")
    
    def get_random_header(self):
        """Get a random header from the loaded headers"""
        if not self.headers_cache:
            self._create_fallback_headers()
        
        return random.choice(self.headers_cache).copy()
    
    def get_multiple_random_headers(self, count=10):
        """Get multiple random headers for batch operations"""
        if not self.headers_cache:
            self._create_fallback_headers()
        
        return [random.choice(self.headers_cache).copy() for _ in range(count)]
    
    def reload_headers(self):
        """Reload headers from file (useful if file was updated)"""
        self._load_headers()
    
    def get_stats(self):
        """Get statistics about loaded headers"""
        if not self.headers_cache:
            return {"total": 0, "unique_user_agents": 0}
        
        user_agents = {h.get("User-Agent", "") for h in self.headers_cache}
        return {
            "total": len(self.headers_cache),
            "unique_user_agents": len(user_agents),
            "file_path": self.headers_file
        }


# Global instance for easy use
header_manager = HeaderManager()

# Convenience functions
def get_random_header():
    """Get a random header - convenience function"""
    return header_manager.get_random_header()

def get_random_headers(count=10):
    """Get multiple random headers - convenience function"""
    return header_manager.get_multiple_random_headers(count)


if __name__ == "__main__":
    # Test the header manager
    print("🧪 Testing Header Manager...")
    
    # Get stats
    stats = header_manager.get_stats()
    print(f"📊 Stats: {stats}")
    
    # Get a random header
    header = get_random_header()
    print(f"\n🎲 Random header sample:")
    for key, value in header.items():
        print(f"  {key}: {value}")
    
    # Get multiple headers
    headers = get_random_headers(3)
    print(f"\n🎲 Got {len(headers)} random headers")
    
    print("✅ Header Manager test completed!")