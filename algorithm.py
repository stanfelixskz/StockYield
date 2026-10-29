"""
Historical Stock Yield Optimization - Divide-and-Conquer core.

Problem: given daily closing prices, find the buy day and sell day (buy before
sell) that give the maximum profit (yield).

Approach: convert prices to daily changes, then solve the Maximum Subarray
Problem on the changes using Divide-and-Conquer:
    DIVIDE  : split the range at the midpoint
    CONQUER : solve the left half and the right half recursively
    COMBINE : find the best subarray that crosses the midpoint, then take the
              largest of (left, right, crossing)

Recurrence: T(n) = 2T(n/2) + O(n)  ->  O(n log n)
"""
from dataclasses import dataclass, field


@dataclass
class Result:
    buy_day: int | None      # 1-based day number, None if no profitable trade
    sell_day: int | None
    buy_price: float | None
    sell_price: float | None
    profit: float
    trace: list[str] = field(default_factory=list)


def daily_changes(prices):
    """Day-to-day price differences: changes[i] = prices[i+1] - prices[i]."""
    return [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]


def _max_crossing(a, lo, mid, hi):
    """COMBINE step: best subarray that must include a[mid] and a[mid+1]."""
    best_left, total, left_idx = float("-inf"), 0, mid
    for i in range(mid, lo - 1, -1):          # grow leftwards from the middle
        total += a[i]
        if total > best_left:
            best_left, left_idx = total, i

    best_right, total, right_idx = float("-inf"), 0, mid + 1
    for j in range(mid + 1, hi + 1):          # grow rightwards from the middle
        total += a[j]
        if total > best_right:
            best_right, right_idx = total, j

    return left_idx, right_idx, best_left + best_right


def _max_subarray(a, lo, hi, trace, depth=0):
    """Returns (start_index, end_index, sum) of the max subarray in a[lo..hi]."""
    indent = "  " * depth
    if lo == hi:                               # BASE CASE: a single element
        trace.append(f"{indent}[{lo}..{hi}] base case -> sum {a[lo]:+.2f}")
        return lo, hi, a[lo]

    mid = (lo + hi) // 2                       # DIVIDE
    trace.append(f"{indent}[{lo}..{hi}] divide at mid={mid}")

    l = _max_subarray(a, lo, mid, trace, depth + 1)        # CONQUER left
    r = _max_subarray(a, mid + 1, hi, trace, depth + 1)    # CONQUER right
    c = _max_crossing(a, lo, mid, hi)                      # COMBINE

    best = max((l, "left"), (r, "right"), (c, "crossing"), key=lambda t: t[0][2])
    trace.append(
        f"{indent}[{lo}..{hi}] combine: left={l[2]:+.2f}, right={r[2]:+.2f}, "
        f"crossing={c[2]:+.2f} -> best is {best[1]} ({best[0][2]:+.2f})"
    )
    return best[0]


def max_profit(prices):
    """Find the best buy/sell days using divide-and-conquer."""
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices.")
    changes = daily_changes(prices)
    trace: list[str] = []
    start, end, total = _max_subarray(changes, 0, len(changes) - 1, trace)

    if total <= 0:                             # prices only fall: don't trade
        return Result(None, None, None, None, 0.0, trace)

    buy_idx, sell_idx = start, end + 1         # change i spans price i -> i+1
    return Result(buy_idx + 1, sell_idx + 1, prices[buy_idx], prices[sell_idx],
                  total, trace)


def brute_force(prices):
    """O(n^2) checker used only for testing."""
    best = 0.0
    for i in range(len(prices)):
        for j in range(i + 1, len(prices)):
            best = max(best, prices[j] - prices[i])
    return best
