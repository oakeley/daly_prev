#!/usr/bin/env python3
"""
main.py

Command-line tool to:
- Load DALY and prevalence TSVs
- Normalize rates (divide Value/Lower/Upper by 100000)
- Merge datasets by Condition, Sex, Age, Location, Year
- Produce a DALY vs Prevalence PNG scatter (colour by Location)
- Export "high prevalence & high DALY" quadrant CSVs per Condition

Coding style: PEP8, typing, logging, explicit docstrings. No unicode icons.
"""

from __future__ import annotations

import logging
import sys
import os

# Add src to path to allow imports if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.cli import parse_args
from src.io_utils import read_tsv, parse_countries_arg, parse_years_arg, export_high_high_by_condition
from src.processing import normalize_rates, filter_df, merge_daly_prev
from src.plotter import plot_daly_vs_prev

# Logging configuration (suitable for command-line tools)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    args = parse_args()

    countries = parse_countries_arg(args.countries)
    years = parse_years_arg(args.years)

    # Create timestamped run directory
    from src.io_utils import create_run_directory, generate_report
    run_dir = create_run_directory(base_dir="runs")
    
    # Load data
    try:
        daly = read_tsv(args.daly)
        prev = read_tsv(args.prev)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return

    # Filter by requested countries/years BEFORE normalization or after (here before)
    if countries:
        logger.info("Filtering countries: %s", ", ".join(countries))
    if years:
        logger.info("Filtering years: %s", ", ".join(str(y) for y in years))
    daly = filter_df(daly, countries, years)
    prev = filter_df(prev, countries, years)



    # Normalize rate columns (Value, Lower, Upper)
    daly = normalize_rates(daly, ["Value", "Lower", "Upper"])
    prev = normalize_rates(prev, ["Value", "Lower", "Upper"])

    # Merge DALY and prevalence
    merged = merge_daly_prev(daly, prev)
    if merged.empty:
        logger.warning("No merged rows after joining DALY and prevalence. Exiting.")
        return

    # Helper function to run analysis
    def run_analysis(df, intersect_x, intersect_y, suffix, mode_title, top_n=None, top_conditions=None):
        logger.info(f"Running Analysis: {mode_title} (Prev>{intersect_x:.5f}, DALY>{intersect_y:.5f})")
        
        # Plot
        plot_filename = os.path.join(run_dir, f"daly_vs_prev_{suffix}.png")
        plot_daly_vs_prev(df, out_png=plot_filename, show_legend=True,
                          intersect_x=intersect_x, intersect_y=intersect_y)
        
        # Export High/High
        export_dir = os.path.join(run_dir, f"high_high_exports_{suffix}")
        export_high_high_by_condition(df, intersect_x, intersect_y, out_dir=export_dir, whitelist=top_conditions)
        
        # Generate Report Section (or append)
        # For simplicity, we will generate separate reports or one combined report.
        # Let's generate a specific report for this mode.
        report_filename = f"REPORT_{suffix.upper()}.md"
        generate_report(df, run_dir, plot_filename, intersect_x, intersect_y, 
                        top_n=top_n, top_conditions=top_conditions, report_filename=report_filename)

    # Calculate Global Medians (for defaults)
    import numpy as np
    median_x = float(np.nanmedian(merged["Value_prev"]))
    median_y = float(np.nanmedian(merged["Value_daly"]))

    # Determine Standard Intersects
    # If manual args provided, use them. Otherwise, use medians.
    std_intersect_x = args.intersect_prev if args.intersect_prev is not None else median_x
    std_intersect_y = args.intersect_daly if args.intersect_daly is not None else median_y
    
    # Determine suffix/title for Standard Analysis
    if args.intersect_prev is not None and args.intersect_daly is not None:
        std_suffix = "manual"
        std_title = "Manual Intersects"
    else:
        std_suffix = "median"
        std_title = "Median Intersects"

    # Run Standard Analysis (Always)
    run_analysis(merged, std_intersect_x, std_intersect_y, std_suffix, std_title)
    
    # Run Auto Analysis (if --num is provided)
    if args.num:
        from src.processing import calculate_auto_intersects
        # Calculate auto intersects based on Top N
        auto_prev, auto_daly, top_conditions = calculate_auto_intersects(merged, args.num)
        
        run_analysis(merged, auto_prev, auto_daly, f"Top_{args.num}", f"Top {args.num} Auto-Thresholds", 
                     top_n=args.num, top_conditions=top_conditions)

if __name__ == "__main__":
    main()
