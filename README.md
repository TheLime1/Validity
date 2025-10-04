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

### 🤖 Automated (Recommended)

The repository includes **two GitHub Actions** for different use cases:

#### **🕐 Full Validation (Every 12 Hours)**
- **Schedule**: 6:00 AM and 6:00 PM UTC (automatic)
- **Duration**: 30 minutes per run with automatic shutdown
- **Scope**: Complete validation of all sources and proxy types
- **Auto-commit**: Results automatically committed to repository

#### **⚡ Quick Test (Manual)**
- **Trigger**: Manual only (Actions tab → "Quick Proxy Test")
- **Duration**: 3 minutes (customizable: 1-10 minutes)
- **Scope**: Limited validation for immediate results
- **Use case**: Quick proxy refresh, testing, or immediate needs

**Manual Trigger Options:**

1. **Quick Test (3 minutes):**
   - Go to **Actions** tab → **"Quick Proxy Test (3 minutes)"**
   - Click **"Run workflow"**
   - Optionally customize duration (1-10 minutes)
   - Choose proxy types: HTTP, SOCKS5, or both

2. **Full Validation:**
   - Go to **Actions** tab → **"Automated Proxy Validation"**
   - Click **"Run workflow"**
   - Optionally customize duration (default: 30 minutes)

### 🔧 Manual Setup

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

The quality analyzer (`analyze_proxy_quality.py`) provides detailed statistics about each proxy source with comprehensive analysis options.

### Parameters & Usage

#### Basic Usage
```bash
python analyze_proxy_quality.py
```

#### All Available Parameters

| Parameter         | Type   | Default                         | Description                                        |
| ----------------- | ------ | ------------------------------- | -------------------------------------------------- |
| `--days`          | int    | 7                               | Number of days to analyze (1-365)                  |
| `--save`          | flag   | False                           | Save quality report to CSV file                    |
| `--performance`   | flag   | False                           | Show top 10 fastest performing proxies             |
| `--worst-sources` | flag   | False                           | Show detailed worst sources analysis by proxy type |
| `--log-file`      | string | `data/proxy_validation_log.csv` | Path to proxy validation log file                  |

#### Detailed Examples

**1. Basic Quality Report (Last 7 Days)**
```bash
python analyze_proxy_quality.py
```
Shows source rankings, alive/dead percentages, response times, and worst sources by type.

**2. Extended Analysis Period**
```bash
python analyze_proxy_quality.py --days 30
```
Analyze proxy performance over the last 30 days for trend analysis.

**3. Quick Daily Check**
```bash
python analyze_proxy_quality.py --days 1
```
View today's proxy validation results only.

**4. Performance Analysis**
```bash
python analyze_proxy_quality.py --performance
```
Shows the 10 fastest responding proxies with their response times and sources.

**5. Worst Sources Analysis**
```bash
python analyze_proxy_quality.py --worst-sources
```
Detailed analysis of the 5 worst performing sources for each proxy type (HTTP, SOCKS4, SOCKS5) with performance warnings:
- 🚨 **CRITICAL**: <10% success rate (remove immediately)  
- ⚠️ **WARNING**: <20% success rate (consider replacement)

**6. Comprehensive Analysis with Export**
```bash
python analyze_proxy_quality.py --days 14 --save --performance --worst-sources
```
Complete analysis with:
- 14-day data analysis
- CSV export to `data/source_quality_report.csv`
- Top performing proxies list
- Detailed worst sources breakdown

**7. Custom Log File Analysis**
```bash
python analyze_proxy_quality.py --log-file "custom/path/logs.csv" --days 7
```
Analyze a different validation log file.

### Output Features

#### Main Quality Report Includes:
- **Source Rankings**: Sorted by quality score (alive percentage)
- **Detailed Metrics**: Total tested, alive/dead counts, response times
- **Proxy Types**: Which types each source provides
- **Overall Statistics**: Aggregate performance across all sources
- **Worst Sources by Type**: Bottom 5 sources for each proxy type
- **Smart Recommendations**: Data-driven suggestions for source management

#### CSV Export Format
When using `--save`, generates `data/source_quality_report.csv` with:
```csv
source_url,total_tested,alive_count,dead_count,alive_percent,quality_score,analysis_date
```

#### Performance Analysis Shows:
```
🚀 TOP PERFORMING PROXIES (Last 7 days):
#1  192.168.1.100:8080  |  245ms | http   | https://source1.com
#2  10.0.0.50:1080      |  289ms | socks5 | https://source2.com
```

#### Worst Sources Analysis Example:
```
📍 HTTP PROXIES - Bottom 5 Sources:
#1 https://bad-source.com
   📊 Total Tested: 1,000
   ✅ Alive: 12
   💯 Success Rate: 1.2%
   🚨 CRITICAL: Consider removing this source immediately
```

### Use Cases

**Daily Monitoring**
```bash
python analyze_proxy_quality.py --days 1 --performance
```

**Weekly Review**
```bash
python analyze_proxy_quality.py --save --worst-sources
```

**Monthly Source Audit**
```bash
python analyze_proxy_quality.py --days 30 --save --performance --worst-sources
```

**Source Quality Investigation**
```bash
python analyze_proxy_quality.py --days 7 --worst-sources
```

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
