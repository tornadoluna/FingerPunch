from __future__ import annotations


def dirty_range(previous: str, current: str, limit: int) -> tuple[int, int]:
    start = 0
    shared = min(len(previous), len(current))
    while start < shared and previous[start] == current[start]:
        start += 1

    end = min(max(len(previous), len(current)), limit)
    return start, max(start, end)
