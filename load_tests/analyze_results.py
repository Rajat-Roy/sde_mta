"""
Analyze load test results and generate performance metrics graphs.

Reads CSV files from load_tests/results/ and generates:
- Response time graphs
- Request rate graphs
- Failure rate analysis
- Performance comparison tables

Usage:
    python load_tests/analyze_results.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
from pathlib import Path


def analyze_test_results():
    """Main analysis function."""
    results_dir = Path("load_tests/results")

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        print("Please run load tests first: ./load_tests/run_tests.sh")
        return

    # Find all CSV stats files
    stats_files = list(results_dir.glob("*_stats.csv"))

    if not stats_files:
        print("No result files found. Please run load tests first.")
        return

    print("="*70)
    print("LOAD TEST ANALYSIS")
    print("="*70)
    print()

    all_results = {}

    for stats_file in stats_files:
        test_name = stats_file.stem.replace("_stats", "")
        print(f"Analyzing: {test_name}")

        try:
            df = pd.read_csv(stats_file)

            # Calculate metrics
            metrics = {
                'Total Requests': df['Request Count'].sum(),
                'Total Failures': df['Failure Count'].sum(),
                'Failure Rate (%)': (df['Failure Count'].sum() / df['Request Count'].sum() * 100)
                                    if df['Request Count'].sum() > 0 else 0,
                'Avg Response Time (ms)': df['Average Response Time'].mean(),
                'Median Response Time (ms)': df['Median Response Time'].mean(),
                'P95 Response Time (ms)': df['95%'].mean() if '95%' in df.columns else None,
                'P99 Response Time (ms)': df['99%'].mean() if '99%' in df.columns else None,
                'Min Response Time (ms)': df['Min Response Time'].min(),
                'Max Response Time (ms)': df['Max Response Time'].max(),
                'Requests/sec': df['Requests/s'].mean() if 'Requests/s' in df.columns else None,
            }

            all_results[test_name] = metrics

            # Print summary
            print(f"  Total Requests: {metrics['Total Requests']:.0f}")
            print(f"  Failure Rate: {metrics['Failure Rate (%)']:.2f}%")
            print(f"  Avg Response Time: {metrics['Avg Response Time (ms)']:.0f} ms")
            print(f"  P95 Response Time: {metrics['P95 Response Time (ms)']:.0f} ms"
                  if metrics['P95 Response Time (ms)'] else "")
            print(f"  Requests/sec: {metrics['Requests/sec']:.2f}"
                  if metrics['Requests/sec'] else "")
            print()

        except Exception as e:
            print(f"  Error analyzing {test_name}: {e}")
            print()
            continue

    # Generate comparison graphs
    if all_results:
        generate_graphs(all_results, results_dir)
        generate_markdown_report(all_results, results_dir)

    print("="*70)
    print("Analysis complete! Check load_tests/results/ for graphs.")
    print("="*70)


def generate_graphs(results, output_dir):
    """Generate comparison graphs."""
    print("Generating graphs...")

    test_names = list(results.keys())

    # Response Time Comparison
    plt.figure(figsize=(12, 6))

    metrics_to_plot = ['Avg Response Time (ms)', 'Median Response Time (ms)',
                       'P95 Response Time (ms)', 'P99 Response Time (ms)']

    x = range(len(test_names))
    width = 0.2

    for i, metric in enumerate(metrics_to_plot):
        values = [results[test].get(metric, 0) for test in test_names]
        if any(v for v in values if v and v > 0):
            plt.bar([p + width * i for p in x], values, width, label=metric.replace(' (ms)', ''))

    plt.xlabel('Test Scenario')
    plt.ylabel('Response Time (ms)')
    plt.title('Response Time Comparison Across Load Tests')
    plt.xticks([p + width * 1.5 for p in x], test_names, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / 'response_time_comparison.png', dpi=300)
    plt.close()
    print("  ✓ Response time graph saved")

    # Throughput Comparison
    plt.figure(figsize=(10, 6))

    throughput = [results[test].get('Requests/sec', 0) for test in test_names]
    if any(throughput):
        plt.bar(test_names, throughput, color='steelblue')
        plt.xlabel('Test Scenario')
        plt.ylabel('Requests/sec')
        plt.title('Throughput Comparison')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_dir / 'throughput_comparison.png', dpi=300)
        plt.close()
        print("  ✓ Throughput graph saved")

    # Failure Rate Comparison
    plt.figure(figsize=(10, 6))

    failure_rates = [results[test].get('Failure Rate (%)', 0) for test in test_names]
    colors = ['green' if rate < 1 else 'orange' if rate < 5 else 'red'
              for rate in failure_rates]

    plt.bar(test_names, failure_rates, color=colors)
    plt.xlabel('Test Scenario')
    plt.ylabel('Failure Rate (%)')
    plt.title('Error Rate Comparison')
    plt.xticks(rotation=45, ha='right')
    plt.axhline(y=1, color='orange', linestyle='--', label='1% threshold')
    plt.axhline(y=5, color='red', linestyle='--', label='5% threshold')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / 'failure_rate_comparison.png', dpi=300)
    plt.close()
    print("  ✓ Failure rate graph saved")


def generate_markdown_report(results, output_dir):
    """Generate markdown performance report."""
    report_path = output_dir / 'PERFORMANCE_REPORT.md'

    with open(report_path, 'w') as f:
        f.write("# Load Test Performance Report\n\n")
        f.write("## Summary\n\n")
        f.write("This report contains performance metrics from load testing the District Marketplace.\n\n")

        f.write("## Test Scenarios\n\n")
        for test_name, metrics in results.items():
            f.write(f"### {test_name.replace('_', ' ').title()}\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")

            for metric_name, value in metrics.items():
                if value is not None:
                    if isinstance(value, float):
                        f.write(f"| {metric_name} | {value:.2f} |\n")
                    else:
                        f.write(f"| {metric_name} | {value} |\n")

            f.write("\n")

        f.write("## Graphs\n\n")
        f.write("![Response Time Comparison](response_time_comparison.png)\n\n")
        f.write("![Throughput Comparison](throughput_comparison.png)\n\n")
        f.write("![Failure Rate Comparison](failure_rate_comparison.png)\n\n")

        f.write("## Conclusions\n\n")
        f.write("### Performance Quality Attribute Proof\n\n")

        # Calculate averages
        avg_response = sum(r.get('Avg Response Time (ms)', 0) for r in results.values()) / len(results)
        avg_throughput = sum(r.get('Requests/sec', 0) for r in results.values()) / len(results)
        avg_failure = sum(r.get('Failure Rate (%)', 0) for r in results.values()) / len(results)

        f.write(f"**Average Response Time:** {avg_response:.0f} ms\n\n")
        f.write(f"**Average Throughput:** {avg_throughput:.2f} requests/sec\n\n")
        f.write(f"**Average Failure Rate:** {avg_failure:.2f}%\n\n")

        if avg_response < 500:
            f.write("✅ **Performance Target Met:** Average response time < 500ms\n\n")
        else:
            f.write("⚠️ **Performance Warning:** Average response time exceeds 500ms\n\n")

        if avg_failure < 1:
            f.write("✅ **Reliability Target Met:** Failure rate < 1%\n\n")
        elif avg_failure < 5:
            f.write("⚠️ **Reliability Warning:** Failure rate between 1-5%\n\n")
        else:
            f.write("❌ **Reliability Issue:** Failure rate > 5%\n\n")

    print(f"  ✓ Markdown report saved: {report_path}")


if __name__ == '__main__':
    # Install matplotlib if not available
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
    except ImportError:
        print("Installing matplotlib for graph generation...")
        os.system("pip install matplotlib pandas")
        import matplotlib
        matplotlib.use('Agg')

    analyze_test_results()
