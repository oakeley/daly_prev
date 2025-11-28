import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def plot_daly_vs_prev(merged: pd.DataFrame, out_png: str = "daly_vs_prev.png", show_legend: bool = True,
                      intersect_x: float = None, intersect_y: float = None) -> Tuple[float, float]:
    """
    Create a scatter plot with:
      - X: Value_prev (normalized)
      - Y: Value_daly (normalized)
    Colour by Location.
    Axis intersection is the medians of X and Y, or custom values if provided.
    Save PNG to out_png and return (intersect_x, intersect_y).
    """
    # Prepare data
    x = merged["Value_prev"]
    y = merged["Value_daly"]
    # Compute medians (skip NA) if not provided
    if intersect_x is None:
        intersect_x = float(np.nanmedian(x))
    if intersect_y is None:
        intersect_y = float(np.nanmedian(y))

    median_x = intersect_x
    median_y = intersect_y

    # Create a categorical mapping for locations to colors
    locations = merged["Location"].astype(str)
    unique_locs = sorted(locations.unique())
    color_map = {loc: i for i, loc in enumerate(unique_locs)}
    colors = locations.map(color_map)

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x, y, c=colors, cmap=None, alpha=0.8)
    # Do not use unicode or special markers in labels or annotations
    ax.set_xlabel("Prevalence (proportion, rate / 100000)")
    ax.set_ylabel("DALY (proportion, rate / 100000)")
    ax.set_title("DALY vs Prevalence")

    # Draw median lines (axis intersect)
    ax.axvline(median_x, linestyle="--", linewidth=1)
    ax.axhline(median_y, linestyle="--", linewidth=1)

    # Create a legend mapping colors -> locations in a simple, standards-based way
    if show_legend:
        from matplotlib.lines import Line2D
        # Build legend items from the categorical mapping
        handles = []
        labels = []
        # Get properties from the main scatter plot to ensure consistency
        cmap = scatter.get_cmap()
        # We need to normalize the index to get the color from the colormap
        norm = plt.Normalize(vmin=0, vmax=len(unique_locs)-1)
        
        for loc, idx in color_map.items():
            # Use Line2D as a proxy artist for the legend
            color = cmap(norm(idx))
            h = Line2D([0], [0], marker='o', color='w', label=loc,
                       markerfacecolor=color, markersize=10, alpha=0.8)
            handles.append(h)
            labels.append(loc)
        ax.legend(handles=handles, labels=labels, title="Location", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    logger.info("Saved plot to %s", out_png)
    return median_x, median_y
