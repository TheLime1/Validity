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

2. Generate random headers (optional but recommended):

```bash
python generate_headers.py
```

3. Run the proxy scraper:

```bash
python proxy_scraper.py
```

4. Analyze source quality (after running scraper):

```bash
python analyze_proxy_quality.py --days 7 --save --performance
```

The scraper will:

- **Load dead proxies database** and clean entries older than 30 days
- **Validate existing proxies** in data folder first
- **Remove dead proxies** from data files and add them to dead_proxies.txt
- **Fetch new proxies** from sources concurrently
- **Skip proxies** already in dead_proxies database
- **Validate new proxies** using random headers
- **Log detailed validation** results for quality analysis
- **Save up to 1000 alive proxies** per type with periodic auto-save

## Quality Analysis

The quality analyzer provides detailed statistics about each proxy source:

- **Alive/Dead percentages** per source
- **Response time analysis** for alive proxies
- **Quality scores** and source rankings
- **Performance metrics** and recommendations

View analysis for different time periods:
```bash
python analyze_proxy_quality.py --days 1   # Last 24 hours
python analyze_proxy_quality.py --days 30  # Last month
```

## Output

The validated proxies are saved in the `data/` folder:

- `data/http.txt` - Valid HTTP proxies
- `data/socks5.txt` - Valid SOCKS5 proxies

## Sources

All proxy sources are publicly available and listed in `sources.csv` for transparency.
