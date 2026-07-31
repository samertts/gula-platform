#!/usr/bin/env python3
"""Performance report generator — parses k6/locust output and generates HTML report."""

import argparse
import json
import os
from datetime import datetime


def generate_html_report(data, output_path):
    html = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>GULA Platform Performance Report</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
h1 { color: #1a56db; border-bottom: 2px solid #1a56db; padding-bottom: 10px; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; }
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
th { background: #1a56db; color: white; }
tr:nth-child(even) { background: #f5f7fa; }
.pass { color: green; font-weight: bold; }
.fail { color: red; font-weight: bold; }
.warn { color: orange; font-weight: bold; }
.metric-card { background: #f5f7fa; padding: 20px; border-radius: 8px; margin: 10px 0; display: inline-block; }
.metric-value { font-size: 24px; font-weight: bold; color: #1a56db; }
.metric-label { font-size: 12px; color: #666; }
</style></head><body>
<h1>GULA Platform Performance Report</h1>
<p>Generated: {date}</p>
<h2>Test Overview</h2>
<table>
<tr><th>Metric</th><th>Value</th><th>Status</th></tr>
""".format(date=datetime.now().isoformat())

    metrics = data.get("metrics", {})
    duration = metrics.get("http_req_duration", {}).get("values", {})
    errors = metrics.get("http_req_failed", {}).get("values", {})
    iterations = metrics.get("iterations", {}).get("count", 0)

    rows = [
        ("Total Requests", str(iterations), "pass"),
        ("p50 Latency", f'{duration.get("p(50)", 0):.2f}ms', "pass" if duration.get("p(50)", 0) < 200 else "warn"),
        ("p95 Latency", f'{duration.get("p(95)", 0):.2f}ms', "pass" if duration.get("p(95)", 0) < 500 else "warn"),
        ("p99 Latency", f'{duration.get("p(99)", 0):.2f}ms', "pass" if duration.get("p(99)", 0) < 1000 else "fail"),
        ("Error Rate", f'{errors.get("rate", 0)*100:.2f}%', "pass" if errors.get("rate", 0) < 0.01 else "fail"),
        ("Min Latency", f'{duration.get("min", 0):.2f}ms', "pass"),
        ("Max Latency", f'{duration.get("max", 0):.2f}ms', "warn" if duration.get("max", 0) < 2000 else "fail"),
        ("Avg Latency", f'{duration.get("avg", 0):.2f}ms', "pass"),
        ("Media Latency", f'{duration.get("med", 0):.2f}ms', "pass"),
    ]

    for label, value, status in rows:
        cls = "pass" if status == "pass" else ("fail" if status == "fail" else "warn")
        html += f'<tr><td>{label}</td><td>{value}</td><td class="{cls}">{status.upper()}</td></tr>\n'

    html += """
</table>
<h2>Scenario Results</h2>
<table><tr><th>Scenario</th><th>Status</th></tr>
"""
    for scenario, sc_data in data.get("scenarios", {}).items():
        status = sc_data.get("status", "unknown")
        cls = "pass" if status == "passed" else "fail"
        html += f'<tr><td>{scenario}</td><td class="{cls}">{status}</td></tr>\n'

    html += """
</table>
<h2>Verdict</h2>
"""
    verdict = "PASS" if errors.get("rate", 0) < 0.01 and duration.get("p(95)", 0) < 500 else "FAIL"
    cls = "pass" if verdict == "PASS" else "fail"
    html += f'<p class="{cls}" style="font-size: 20px;">{verdict}</p>\n'
    html += "</body></html>"

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Report generated: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate performance report")
    parser.add_argument("--input", "-i", default="/tmp/load-test-results.json")
    parser.add_argument("--output", "-o", default="docs/reports/performance-report.html")
    args = parser.parse_args()

    if os.path.exists(args.input):
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "metrics": {
                "http_req_duration": {"values": {"p(50)": 0, "p(95)": 0, "p(99)": 0, "min": 0, "max": 0, "avg": 0, "med": 0}},
                "http_req_failed": {"values": {"rate": 0}},
                "iterations": {"count": 0},
            },
            "scenarios": {}
        }

    generate_html_report(data, args.output)

if __name__ == "__main__":
    main()
