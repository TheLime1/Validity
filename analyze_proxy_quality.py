#!/usr/bin/env python3
"""
Proxy Source Quality Analyzer
Analyzes proxy validation logs to calculate quality metrics per source
"""

import csv
import os
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import argparse


class ProxyQualityAnalyzer:
    def __init__(self, log_file="data/proxy_validation_log.csv"):
        """Initialize analyzer with log file path"""
        self.log_file = log_file
        self.data = None

    def load_data(self):
        """Load proxy validation data from CSV log"""
        if not os.path.exists(self.log_file):
            print(f"❌ Log file not found: {self.log_file}")
            print("Run proxy_scraper.py first to generate validation logs.")
            return False

        try:
            self.data = pd.read_csv(self.log_file)
            print(f"✅ Loaded {len(self.data)} validation records")
            return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def get_date_range_data(self, days=7):
        """Filter data for the last N days"""
        if self.data is None:
            return None

        cutoff_date = datetime.now() - timedelta(days=days)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])

        recent_data = self.data[self.data['timestamp'] >= cutoff_date]
        print(
            f"📅 Analyzing data from last {days} days ({len(recent_data)} records)")
        return recent_data

    def analyze_source_quality(self, days=7):
        """Analyze quality metrics per source"""
        data = self.get_date_range_data(days)
        if data is None or len(data) == 0:
            print("No data available for analysis")
            return None

        # Group by source and calculate metrics
        source_stats = {}

        for source_url in data['source_url'].unique():
            if source_url == 'existing':
                continue  # Skip existing proxies

            source_data = data[data['source_url'] == source_url]

            total_tested = len(source_data)
            alive_count = len(source_data[source_data['status'] == 'alive'])
            dead_count = len(source_data[source_data['status'] == 'dead'])
            error_count = len(source_data[source_data['status'] == 'error'])

            # Calculate percentages
            alive_percent = (alive_count / total_tested *
                             100) if total_tested > 0 else 0
            dead_percent = (dead_count / total_tested *
                            100) if total_tested > 0 else 0
            error_percent = (error_count / total_tested *
                             100) if total_tested > 0 else 0

            # Calculate average response time for alive proxies
            alive_proxies = source_data[
                (source_data['status'] == 'alive') &
                (source_data['response_time_ms'].notna()) &
                (source_data['response_time_ms'] != '')
            ]

            avg_response_time = 0
            if len(alive_proxies) > 0:
                response_times = pd.to_numeric(
                    alive_proxies['response_time_ms'], errors='coerce')
                avg_response_time = response_times.mean()

            # Determine proxy types from this source
            proxy_types = source_data['proxy_type'].unique().tolist()

            source_stats[source_url] = {
                'total_tested': total_tested,
                'alive_count': alive_count,
                'dead_count': dead_count,
                'error_count': error_count,
                'alive_percent': round(alive_percent, 2),
                'dead_percent': round(dead_percent, 2),
                'error_percent': round(error_percent, 2),
                'avg_response_time_ms': round(avg_response_time, 2) if avg_response_time else 0,
                'proxy_types': proxy_types,
                # Simple quality score = alive %
                'quality_score': round(alive_percent, 2)
            }

        return source_stats

    def print_quality_report(self, days=7):
        """Print a formatted quality report"""
        stats = self.analyze_source_quality(days)
        if not stats:
            return

        print(f"\n{'='*80}")
        print(f"🔍 PROXY SOURCE QUALITY REPORT (Last {days} days)")
        print(f"{'='*80}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Sort sources by quality score (alive percentage)
        sorted_sources = sorted(
            stats.items(), key=lambda x: x[1]['quality_score'], reverse=True)

        for i, (source_url, metrics) in enumerate(sorted_sources, 1):
            print(f"#{i} SOURCE: {source_url}")
            print(f"   📊 Total Tested: {metrics['total_tested']:,}")
            print(
                f"   ✅ Alive: {metrics['alive_count']:,} ({metrics['alive_percent']:.1f}%)")
            print(
                f"   ❌ Dead: {metrics['dead_count']:,} ({metrics['dead_percent']:.1f}%)")
            print(
                f"   ⚠️  Errors: {metrics['error_count']:,} ({metrics['error_percent']:.1f}%)")
            print(
                f"   ⚡ Avg Response: {metrics['avg_response_time_ms']:.0f}ms")
            print(f"   🏷️  Types: {', '.join(metrics['proxy_types'])}")
            print(f"   🌟 Quality Score: {metrics['quality_score']:.1f}%")
            print()

        # Overall statistics
        total_tested = sum(s['total_tested'] for s in stats.values())
        total_alive = sum(s['alive_count'] for s in stats.values())
        total_dead = sum(s['dead_count'] for s in stats.values())

        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Proxies Tested: {total_tested:,}")
        print(
            f"   Total Alive: {total_alive:,} ({(total_alive/total_tested*100):.1f}%)")
        print(
            f"   Total Dead: {total_dead:,} ({(total_dead/total_tested*100):.1f}%)")
        print(f"   Sources Analyzed: {len(stats)}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        best_source = sorted_sources[0] if sorted_sources else None
        worst_source = sorted_sources[-1] if sorted_sources else None

        if best_source and worst_source:
            print(
                f"   🏆 Best Source: {best_source[0]} ({best_source[1]['quality_score']:.1f}% alive)")
            print(
                f"   🚨 Worst Source: {worst_source[0]} ({worst_source[1]['quality_score']:.1f}% alive)")

            if worst_source[1]['quality_score'] < 20:
                print(f"   ⚠️  Consider removing sources with <20% alive rate")

        print(f"{'='*80}")

    def save_quality_report(self, output_file="data/source_quality_report.csv", days=7):
        """Save quality report to CSV file"""
        stats = self.analyze_source_quality(days)
        if not stats:
            return

        # Convert to list of dictionaries for CSV
        report_data = []
        for source_url, metrics in stats.items():
            row = {
                'source_url': source_url,
                'total_tested': metrics['total_tested'],
                'alive_count': metrics['alive_count'],
                'dead_count': metrics['dead_count'],
                'error_count': metrics['error_count'],
                'alive_percent': metrics['alive_percent'],
                'dead_percent': metrics['dead_percent'],
                'error_percent': metrics['error_percent'],
                'avg_response_time_ms': metrics['avg_response_time_ms'],
                'proxy_types': ', '.join(metrics['proxy_types']),
                'quality_score': metrics['quality_score'],
                'analysis_date': datetime.now().isoformat(),
                'days_analyzed': days
            }
            report_data.append(row)

        # Sort by quality score
        report_data.sort(key=lambda x: x['quality_score'], reverse=True)

        # Save to CSV
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if report_data:
                writer = csv.DictWriter(f, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)

        print(f"💾 Quality report saved to: {output_file}")

    def analyze_proxy_performance(self, days=7):
        """Analyze individual proxy performance"""
        data = self.get_date_range_data(days)
        if data is None or len(data) == 0:
            return

        print(f"\n🚀 TOP PERFORMING PROXIES (Last {days} days):")
        print("-" * 60)

        # Get alive proxies with response times
        alive_data = data[
            (data['status'] == 'alive') &
            (data['response_time_ms'].notna()) &
            (data['response_time_ms'] != '')
        ].copy()

        if len(alive_data) == 0:
            print("No alive proxies with response time data found.")
            return

        alive_data['response_time_ms'] = pd.to_numeric(
            alive_data['response_time_ms'], errors='coerce')

        # Top 10 fastest proxies
        fastest_proxies = alive_data.nsmallest(10, 'response_time_ms')

        for i, (_, proxy_data) in enumerate(fastest_proxies.iterrows(), 1):
            print(f"#{i:2d} {proxy_data['proxy']:18s} | "
                  f"{proxy_data['response_time_ms']:4.0f}ms | "
                  f"{proxy_data['proxy_type']:6s} | "
                  f"{proxy_data['source_url']}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze proxy source quality")
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to analyze (default: 7)')
    parser.add_argument('--save', action='store_true',
                        help='Save report to CSV file')
    parser.add_argument('--performance', action='store_true',
                        help='Show top performing proxies')
    parser.add_argument('--log-file', default='data/proxy_validation_log.csv',
                        help='Path to proxy validation log file')

    args = parser.parse_args()

    analyzer = ProxyQualityAnalyzer(args.log_file)

    if not analyzer.load_data():
        return

    # Print main quality report
    analyzer.print_quality_report(args.days)

    # Save report if requested
    if args.save:
        analyzer.save_quality_report(days=args.days)

    # Show performance analysis if requested
    if args.performance:
        analyzer.analyze_proxy_performance(args.days)


if __name__ == "__main__":
    main()
