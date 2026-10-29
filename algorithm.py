"""Divide-and-conquer maximum-subarray solution for StockYield."""
from dataclasses import dataclass, field
import math


@dataclass
class Result:
    profit: float
    buy_day: int | None
    sell_day: int | None
    buy_price: float | None
    sell_price: float | None
    trace: list[str] = field(default_factory=list)


def daily_changes(prices):
    if len(prices) < 2:
        raise ValueError("At least two prices are required.")
    values = [float(p) for p in prices]
    if any(not math.isfinite(p) or p <= 0 for p in values):
        raise ValueError("Prices must be finite positive numbers.")
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def _crossing(a, lo, mid, hi, trace):
    total = 0.0
    best_left = float("-inf")
    min_index = mid
    for i in range(mid, lo - 1, -1):
        total += a[i]
        if total > best_left:
            best_left, min_index = total, i
    total = 0.0
    best_right = float('-inf')
    max_index = mid + 1
    for j in range(mid + 1, hi + 1):
        total += a[j]
        if total > best_right:
            best_right, max_index = total, j
    trace.append(f"  CROSS [{lo + 1}:{hi + 1}] -> gain {best_left + best_right:.2f}")
    return best_left + best_right, min_index, max_index


def _solve(a, lo, hi, trace, depth=0):
    pad = "  " * depth
    if lo == hi:
        trace.append(f"{pad}BASE change day {lo + 1}: {a[lo]:+.2f}")
        return a[lo], lo, hi
    mid = (lo + hi) // 2
    trace.append(f"{pad}DIVIDE changes [{lo + 1}:{hi + 1}] at {mid + 1}")
    left = _solve(a, lo, mid, trace, depth + 1)
    right = _solve(a, mid + 1, hi, trace, depth + 1)
    cross = _crossing(a, lo, mid, hi, trace)
    best = max((left, right, cross), key=lambda x: x[0])
    trace.append(f"{pad}COMBINE [{lo + 1}:{hi + 1}] -> {best[0]:.2f}")
    return best


def max_profit(prices):
    values = [float(p) for p in prices]
    changes = daily_changes(values)
    trace = [f"Input: {len(values)} closing prices / {len(changes)} daily changes", "Recursively find the maximum subarray of daily price changes."]
    gain, left, right = _solve(changes, 0, len(changes) - 1, trace)
    if gain <= 0:
        trace.append("RESULT: no profitable buy-before-sell trade.")
        return Result(0.0, None, None, None, None, trace)
    buy_day, sell_day = left + 1, right + 2
    profit = values[sell_day - 1] - values[buy_day - 1]
    trace.append(f"RESULT: buy Day {buy_day} at {values[buy_day - 1]:.2f}; sell Day {sell_day} at {values[sell_day - 1]:.2f}; profit {profit:.2f}")
    trace.append("Time complexity: O(n log n); auxiliary recursion space: O(log n).")
    return Result(profit, buy_day, sell_day, values[buy_day - 1], values[sell_day - 1], trace)


def brute_force(prices):
    values = [float(p) for p in prices]
    if len(values) < 2:
        raise ValueError("At least two prices are required.")
    best = 0.0
    best_pair = (None, None)
    for i in range(len(values) - 1):
        for j in range(i + 1, len(values)):
            gain = values[j] - values[i]
            if gain > best:
                best, best_pair = gain, (i + 1, j + 1)
    return best, best_pair
