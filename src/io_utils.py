import logging
import os
import pandas as pd
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

def read_tsv(path: str) -> pd.DataFrame:
    """
    Read a TSV file into a pandas DataFrame.
    Expected columns (case-sensitive): Condition, Sex, Age, Location, Measure, Unit,
    Forecast Scenario, Year, Value, Lower, Upper, Data Suite, DA
    """
    logger.info("Reading TSV: %s", path)
    df = pd.read_csv(path, sep="\t", dtype={"Year": int})
    return df

def parse_years_arg(years_arg: Optional[str]) -> Optional[List[int]]:
    """
    Parse a CLI years argument which can be:
      - comma separated years "2018,2019,2020"
      - a range "2018-2020"
      - None (means: do not filter by year)
    Returns a list of years or None.
    """
    if not years_arg:
        return None
    
    years_set = set()
    parts = [p.strip() for p in years_arg.split(",") if p.strip()]
    
    for part in parts:
        if "-" in part:
            # Handle range "start-end" or "end-start"
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str)
                end = int(end_str)
                # Handle reverse range
                if start > end:
                    start, end = end, start
                years_set.update(range(start, end + 1))
            except ValueError:
                logger.warning(f"Invalid year range format: {part}")
        else:
            # Handle single year
            try:
                years_set.add(int(part))
            except ValueError:
                logger.warning(f"Invalid year format: {part}")
                
    return sorted(list(years_set))

def format_years_list(years: List[int]) -> str:
    """
    Format a list of years into a concise string with ranges.
    e.g. [2018, 2019, 2020, 2022] -> "2018-2020, 2022"
    """
    if not years:
        return "N/A"
        
    years = sorted(list(set(years)))
    ranges = []
    
    if not years:
        return ""
        
    start = years[0]
    end = years[0]
    
    for i in range(1, len(years)):
        if years[i] == end + 1:
            end = years[i]
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = years[i]
            end = years[i]
            
    # Add the last range/year
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
        
    return ", ".join(ranges)

def parse_countries_arg(countries_arg: Optional[str]) -> Optional[List[str]]:
    """
    Parse CLI countries argument: comma-separated list or None.
    """
    if not countries_arg:
        return None
    return [c.strip() for c in countries_arg.split(",") if c.strip()]

def create_run_directory(base_dir: str = "runs") -> str:
    """
    Create a timestamped directory for the current run.
    Format: runs/<timestamp>
    """
    timestamp = str(int(time.time()))
    run_dir = os.path.join(base_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)
    logger.info("Created run directory: %s", run_dir)
    return run_dir

def export_high_high_by_condition(merged: pd.DataFrame, median_x: float, median_y: float, 
                                  out_dir: str = "Diseases", 
                                  whitelist: Optional[List[str]] = None) -> List[str]:
    """
    For each Condition in merged, export rows where Value_prev > median_x AND Value_daly > median_y.
    If whitelist is provided, ONLY export conditions in that list.
    Writes CSV files named high_high_<sanitised_condition>.csv in out_dir.
    Returns a list of exported filenames.
    """
    os.makedirs(out_dir, exist_ok=True)
    exported_files = []
    for cond, group in merged.groupby("Condition"):
        # If whitelist is active, skip if not in whitelist
        if whitelist is not None and cond not in whitelist:
            continue
            
        subset = group[(group["Value_prev"] > median_x) & (group["Value_daly"] > median_y)]
        if subset.empty:
            continue
        # Sanitize filename to avoid problematic characters
        safe_name = "".join(c for c in cond if c.isalnum() or c in (" ", "_", "-")).rstrip()
        filename = os.path.join(out_dir, f"high_high_{safe_name.replace(' ', '_')}.csv")
        subset.to_csv(filename, index=False)
        exported_files.append(filename)
        logger.info("Exported %d rows for '%s' to %s", len(subset), cond, filename)
    return exported_files

def generate_report(merged: pd.DataFrame, out_dir: str, plot_filename: str, 
                    median_x: float, median_y: float, top_n: Optional[int] = None,
                    top_conditions: Optional[List[str]] = None,
                    report_filename: str = "REPORT.md") -> str:
    """
    Generate a REPORT.md file summarizing the analysis.
    """
    report_path = os.path.join(out_dir, report_filename)
    filter_type = report_filename.split("_")[1].split(".")[0].capitalize()

    # Calculate some stats
    total_conditions = merged["Condition"].nunique()
    total_locations = merged["Location"].unique()
    years = sorted(merged["Year"].unique())
    year_range = format_years_list(years)
    
    # Identify High/High hits
    high_high = merged[(merged["Value_prev"] > median_x) & (merged["Value_daly"] > median_y)]
    high_high_hits = high_high.groupby("Condition").size().sort_values(ascending=False)
    
    # If top_n is used, we also want to list ALL conditions in the report, as they are the "Top N"
    all_hits = merged.groupby("Condition").size().sort_values(ascending=False)
    
    with open(report_path, "w") as f:
        f.write("# DALY vs Prevalence Analysis Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"**Total Conditions:** {total_conditions}\n")
        f.write(f"\n")
        f.write(f"**Locations:** {', '.join(total_locations)}\n")
        f.write(f"\n")
        f.write(f"**Years:** {year_range}\n")
        f.write(f"\n")
        if top_n:
            f.write(f"**Filter:** Top {top_n} diseases (Combined Score)\n")
        else:
            f.write(f"**Filter:** {filter_type}-filtered diseases (Combined Score)\n")
        f.write("\n")
        
        f.write(f"## {filter_type} Analysis Plot\n\n")
        f.write(f"![DALY vs Prevalence]({os.path.basename(plot_filename)})\n\n")
        f.write(f"- **X-Axis Intersect (Prevalence):** {median_x:.4f}\n")
        f.write(f"- **Y-Axis Intersect (DALY):** {median_y:.4f}\n\n")
        
        if top_n and top_conditions:
            f.write(f"## Top {top_n} Diseases\n\n")
            f.write("Diseases selected by combined DALY and Prevalence score.\n\n")
            f.write("| Condition | Data Points |\n")
            f.write("|---|---|\n")
            # Filter all_hits to only show top_conditions
            for cond in top_conditions:
                count = all_hits.get(cond, 0)
                f.write(f"| {cond} | {count} |\n")
            f.write("\n")
        
        # Show the results from all diseases above the user-defined filters or median filters
        if not top_n:
            f.write(f"## High Impact Diseases (High DALY & High Prevalence)\n\n")
            f.write("Diseases falling into the top-right quadrant (above both threshold filters).\n\n")
            
            if not high_high_hits.empty:
                f.write("| Condition | Data Points in High/High Quadrant |\n")
                f.write("|---|---|\n")
                for cond, count in high_high_hits.items():
                    f.write(f"| {cond} | {count} |\n")
            else:
                f.write("No diseases found in the high/high quadrant.\n")
            
        f.write("\n## Conclusions\n\n")
        f.write("The plot above visualizes the relationship between disease prevalence and DALYs. ")
        f.write("Diseases in the top-right quadrant represent the highest burden and highest prevalence, ")
        f.write("indicating priority areas for intervention.\n")

    # Generate PDF
    yr_rng = year_range.replace(" ", "").replace(",", ".")
    pdf_file = os.path.join(out_dir, f"{filter_type}_{'_'.join(total_locations)}_{yr_rng}_report.pdf")
    print(f"Generating PDF: {pdf_file}...")
    try:
        import subprocess
        subprocess.run(
            ["pandoc", report_path, "-o", pdf_file, "--pdf-engine=xelatex"],
            check=True
        )
        print(f"PDF generated successfully: {pdf_file}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        print("Ensure pandoc and xelatex are installed.")


    logger.info("Generated report: %s", report_path)
    return report_path
