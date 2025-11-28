import pandas as pd
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def normalize_rates(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    """
    Divide specified numeric columns (Value/Lower/Upper) by 100000 in-place and return df.
    Assumes columns exist and are numeric.
    """
    df = df.copy()
    for col in value_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce") / 100000.0
    return df

def filter_df(df: pd.DataFrame, countries: Optional[List[str]], years: Optional[List[int]]) -> pd.DataFrame:
    """
    Filter by countries and years if provided.
    """
    df_out = df
    if countries:
        df_out = df_out[df_out["Location"].isin(countries)]
    if years:
        df_out = df_out[df_out["Year"].isin(years)]
    return df_out

def calculate_auto_intersects(merged: pd.DataFrame, n: int) -> Tuple[float, float, List[str]]:
    """
    Calculate optimal DALY and Prevalence intersects to capture the Top N diseases.
    Top N is determined by combined score (Max DALY + Max Prev).
    Returns (intersect_prev, intersect_daly, top_conditions_list).
    """
    if n is None or n <= 0:
        raise ValueError("N must be positive")

    # Calculate max values per condition
    daly_max = merged.groupby("Condition")["Value_daly"].max()
    prev_max = merged.groupby("Condition")["Value_prev"].max()
    
    # Calculate combined score (assuming already normalized)
    # Normalize relative to max for fair scoring
    d_norm = daly_max / daly_max.max() if daly_max.max() > 0 else daly_max
    p_norm = prev_max / prev_max.max() if prev_max.max() > 0 else prev_max
    
    score = d_norm + p_norm
    top_conditions = score.sort_values(ascending=False).head(n).index.tolist()
    
    # Calculate thresholds
    # We want the thresholds to be just below the minimums of the Top N set
    # to ensure they are included in the High/High quadrant.
    # However, we must ensure we don't pick a threshold that is too low if one disease is an outlier.
    # Strategy: Take the minimum of the Max_DALY and Max_Prev among the Top N.
    
    top_subset = merged[merged["Condition"].isin(top_conditions)]
    
    # We need the minimum of the MAXIMUMS for each condition
    # i.e. for each condition, find its max point. Then find the min of those max points.
    
    min_max_daly = daly_max.loc[top_conditions].min()
    min_max_prev = prev_max.loc[top_conditions].min()
    
    # Apply a small buffer (0.99) to ensure the points sit inside the quadrant
    intersect_daly = min_max_daly * 0.99
    intersect_prev = min_max_prev * 0.99
    
    logger.info(f"Auto-calculated intersects for Top {n}: Prev={intersect_prev:.5f}, DALY={intersect_daly:.5f}")
    
    return intersect_prev, intersect_daly, top_conditions

def filter_top_n_diseases(daly: pd.DataFrame, prev: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Filter both dataframes to include only the top N diseases.
    Ranking is based on the sum of normalized max DALY and normalized max Prevalence for each condition.
    Score = Max(DALY) + Max(Prev)
    """
    if n is None or n <= 0:
        return daly, prev
        
    # Calculate max values per condition
    daly_max = daly.groupby("Condition")["Value"].max()
    prev_max = prev.groupby("Condition")["Value"].max()
    
    # Align indices (conditions)
    # Only consider conditions present in both
    common_conditions = daly_max.index.intersection(prev_max.index)
    daly_max = daly_max.loc[common_conditions]
    prev_max = prev_max.loc[common_conditions]
    
    # Calculate combined score
    d_norm = daly_max / daly_max.max() if daly_max.max() > 0 else daly_max
    p_norm = prev_max / prev_max.max() if prev_max.max() > 0 else prev_max
    
    score = d_norm + p_norm
    
    top_conditions = score.sort_values(ascending=False).head(n).index
    
    logger.info(f"Filtering to top {n} diseases by combined score.")
    
    daly_filtered = daly[daly["Condition"].isin(top_conditions)]
    prev_filtered = prev[prev["Condition"].isin(top_conditions)]
    
    return daly_filtered, prev_filtered

def merge_daly_prev(daly: pd.DataFrame, prev: pd.DataFrame) -> pd.DataFrame:
    """
    Merge DALY and prevalence DataFrames.

    Merge key: Condition, Sex, Age, Location, Year
    Keep only rows where both DALY and prevalence exist for the same key.
    Suffixes: _daly, _prev
    """
    key = ["Condition", "Sex", "Age", "Location", "Year"]
    # Ensure keys exist
    for k in key:
        if k not in daly.columns or k not in prev.columns:
            raise KeyError(f"Missing merge key column: {k}")
    merged = pd.merge(
        daly,
        prev,
        on=key,
        how="inner",
        suffixes=("_daly", "_prev"),
    )
    return merged
