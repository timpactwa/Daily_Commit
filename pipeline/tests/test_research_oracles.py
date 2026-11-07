"""Independent stdlib/brute-force references for the authored corpus case tables."""
import bisect
from collections import Counter
import importlib
import itertools
import math

import pytest

from pipeline import build


def nested_total(items):
    stack = [items]
    total = 0
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(item)
        else:
            total += item
    return total


def bounded_index(nums, target, lo, hi):
    selected = nums[lo:hi + 1]
    return lo + selected.index(target) if target in selected else -1


def intersection(left, right):
    available = Counter(left) & Counter(right)
    return [value for i, value in enumerate(right) if right[:i + 1].count(value) <= available[value]]


def max_sum(nums):
    return max((sum(nums[i:j]) for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)), default=0)


def unique_length(text):
    return max((j - i for i in range(len(text) + 1) for j in range(i, len(text) + 1) if len(set(text[i:j])) == j - i), default=0)


def consecutive_length(nums):
    return max((end - start + 1 for start in nums for end in nums if end >= start and all(v in nums for v in range(start, end + 1))), default=0)


def sum_count(nums, target):
    return sum(sum(nums[i:j]) == target for i in range(len(nums)) for j in range(i + 1, len(nums) + 1))


ORACLES = {
    "prefix_sums": lambda nums: [0, *itertools.accumulate(nums)],
    "max_subarray": max_sum,
    "longest_unique_substring": unique_length,
    "upper_bound": bisect.bisect_right,
    "integer_sqrt": math.isqrt,
    "search_rotated": lambda nums, value: nums.index(value) if value in nums else -1,
    "nested_sum": nested_total,
    "grid_paths": lambda rows, cols: math.comb(rows + cols - 2, rows - 1) if rows > 0 and cols > 0 else 0,
    "recursive_search": bounded_index,
    "bubble_sort": sorted,
    "shell_sort": sorted,
    "counting_sort": sorted,
    "multiset_intersection": intersection,
    "longest_consecutive": consecutive_length,
    "subarray_sum_count": sum_count,
}


@pytest.mark.parametrize("name", ORACLES)
def test_case_tables_agree_with_independent_references(name):
    _, cases = build.load(name)
    reference = ORACLES[name]
    for args, expected in cases.CASES:
        assert reference(*args) == expected, (name, args)


@pytest.mark.parametrize("name", ["bubble_sort", "shell_sort", "counting_sort"])
def test_sorting_exhaustive_short_lists_preserve_input(name):
    function = getattr(importlib.import_module(f"pipeline.corpus.{name}"), name)
    for size in range(6):
        for values in itertools.product((-1, 0, 1), repeat=size):
            original = list(values)
            assert function(original) == sorted(values)
            assert original == list(values)


def test_sliding_window_and_prefix_count_against_exhaustive_brute_force():
    from pipeline.corpus.longest_unique_substring import longest_unique_substring
    from pipeline.corpus.subarray_sum_count import subarray_sum_count
    for size in range(6):
        for values in itertools.product((-1, 0, 1), repeat=size):
            for target in range(-2, 3):
                assert subarray_sum_count(list(values), target) == sum_count(values, target)
        for chars in itertools.product("abc", repeat=size):
            text = "".join(chars)
            assert longest_unique_substring(text) == unique_length(text)
