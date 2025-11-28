import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="DALY vs Prevalence plotting and quadrant export tool.")
    parser.add_argument("--daly", default="data/daly_data_combined.tsv", help="Path to DALY TSV.")
    parser.add_argument("--prev", default="data/prev_data_combined.tsv", help="Path to prevalence TSV.")
    parser.add_argument("--countries", default=None, help="Comma-separated list of countries to include (default: all).")
    parser.add_argument("--years", default=None, help="Years filter: comma-separated (e.g. 2018,2019) or range (e.g. 2010-2020).")
    parser.add_argument("--out", default="daly_vs_prev.png", help="Output PNG filename for the scatter.")
    parser.add_argument("--export-dir", default="high_high_exports", help="Directory to write high/high CSV exports.")
    parser.add_argument("--intersect-prev", type=float, default=None, help="Custom X-axis intersection (Prevalence). Overrides median.")
    parser.add_argument("--intersect-daly", type=float, default=None, help="Custom Y-axis intersection (DALY). Overrides median.")
    parser.add_argument("--num", type=int, default=None, help="Filter to top N diseases by combined DALY and Prevalence score.")
    return parser.parse_args()
