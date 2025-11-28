# DALY vs Prevalence Project

This project loads DALY and prevalence data, normalizes it, and produces a scatter plot of DALY vs Prevalence. It also exports data for the "high prevalence & high DALY" quadrant.

## Setup

1.  Set up a conda environment (or equivalent) running Python 3.11.
    ```bash
    conda create -n daly python=3.11
    conda activate daly
    conda install pip
    ```
2.  Install dependencies (if not already installed):
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main script from the project root:

```bash
python src/main.py
```

### Options

- `--daly`: Path to DALY TSV file (default: `data/daly_data_combined.tsv`)
- `--prev`: Path to Prevalence TSV file (default: `data/prev_data_combined.tsv`)
- `--countries`: Comma-separated list of countries to filter by.
- `--years`: Comma-separated list of years or a range, or a mixture of ranges and lists (e.g., `2010-2020`).
- `--out`: Output PNG filename (default: `daly_vs_prev_{filter}.png`).
- `--export-dir`: Directory for exported CSVs (default: `high_high_exports_{filter}`).
- `--intersect-prev INTERSECT_PREV`: Custom X-axis intersection (Prevalence). Overrides median.
- `--intersect-daly INTERSECT_DALY`: Custom Y-axis intersection (DALY). Overrides median.
- `--num NUM`: Filter to top N diseases by combined DALY and Prevalence score.


### Examples

```bash
# This will use all the data and perform a median intersect to define the top-right quadrant
python src/main.py

# Simple country and year filter, this will use the median intersect
python src/main.py --countries "China,France" --years "2019"

# Really messed up ranges, this will use the median intersect
python src/main.py --years "2018,2019-2030,2025,2033,2050-2040,2055"

# Filter for the top 15 diseases using all the data
# This will do two analyses first with the median intersect filters and second with the number of diseases filter
python src/main.py --num 15

# Change default axis intersect filter and specify the number of diseases to export
# This will do two analyses first with the intersect filters and second with the number of diseases filter
python src/main.py --intersect-prev 0.04 --intersect-daly 0.001 --num 15
```
