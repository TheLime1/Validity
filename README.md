# Validity

**Note: This repository was archived by the owner on Dec 22, 2023. It is now back alive!**

Validity is now a dedicated proxy validator tool that checks and exports valid proxies from public sources.

## Features

- Validates HTTP and SOCKS5 proxies from multiple public sources
- Outputs clean proxy lists in separate files
- Automatic duplicate removal using efficient set-based deduplication
- Regular validation checks with multi-threading for speed
- Maintains maximum 1000 proxies per type
- Daily script designed to keep only alive proxies

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the proxy scraper:
```bash
python proxy_scraper.py
```

The script will:
- First validate existing proxies in the data folder
- Remove dead proxies
- Fetch new proxies from sources
- Validate new proxies
- Save up to 1000 alive proxies per type

## Output

The validated proxies are saved in the `data/` folder:

- `data/http.txt` - Valid HTTP proxies
- `data/socks5.txt` - Valid SOCKS5 proxies

## Sources

All proxy sources are publicly available and listed in `sources.csv` for transparency.
