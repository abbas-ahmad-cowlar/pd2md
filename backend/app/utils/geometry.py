"""
Geometry utilities for spatial analysis.

Functions for clustering, gap detection, and spatial reasoning used
throughout the pipeline for column detection, reading order, etc.
"""

from __future__ import annotations

from backend.app.models.document import BBox


def horizontal_overlap(a: BBox, b: BBox) -> float:
    """Fraction of horizontal overlap between two bboxes (0.0 to 1.0).
    
    Returns the overlap width divided by the narrower box's width.
    """
    overlap = min(a.x1, b.x1) - max(a.x0, b.x0)
    if overlap <= 0:
        return 0.0
    min_width = min(a.width, b.width)
    if min_width == 0:
        return 0.0
    return overlap / min_width


def vertical_overlap(a: BBox, b: BBox) -> float:
    """Fraction of vertical overlap between two bboxes (0.0 to 1.0)."""
    overlap = min(a.y1, b.y1) - max(a.y0, b.y0)
    if overlap <= 0:
        return 0.0
    min_height = min(a.height, b.height)
    if min_height == 0:
        return 0.0
    return overlap / min_height


def are_on_same_line(a: BBox, b: BBox, tolerance_ratio: float = 0.5) -> bool:
    """Check if two bboxes are on the same horizontal line.
    
    Uses vertical overlap — if they share > tolerance_ratio of their
    height, they're considered on the same line.
    """
    return vertical_overlap(a, b) > tolerance_ratio


def merge_bboxes(boxes: list[BBox]) -> BBox:
    """Return the smallest bbox containing all given bboxes."""
    if not boxes:
        return BBox(0, 0, 0, 0)
    return BBox(
        x0=min(b.x0 for b in boxes),
        y0=min(b.y0 for b in boxes),
        x1=max(b.x1 for b in boxes),
        y1=max(b.y1 for b in boxes),
    )


def gap_between(a: BBox, b: BBox) -> float:
    """Horizontal gap between two bboxes (negative if overlapping)."""
    return b.x0 - a.x1


def cluster_by_y(
    items: list[tuple[float, any]],
    tolerance: float,
) -> list[list[any]]:
    """Cluster items by their y-coordinate into groups.
    
    Args:
        items: list of (y_coordinate, item) tuples, sorted by y ascending
        tolerance: maximum y-distance to be in the same cluster
        
    Returns:
        List of clusters, where each cluster is a list of items
    """
    if not items:
        return []

    clusters: list[list] = []
    current_cluster: list = [items[0][1]]
    current_y = items[0][0]

    for y, item in items[1:]:
        if abs(y - current_y) <= tolerance:
            current_cluster.append(item)
        else:
            clusters.append(current_cluster)
            current_cluster = [item]
            current_y = y

    clusters.append(current_cluster)
    return clusters
