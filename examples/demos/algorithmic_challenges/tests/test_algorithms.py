"""Tests for algorithmic challenges - designed to fail initially."""

import pytest
from src.algorithms import AlgorithmicChallenges


class TestKadaneAlgorithm:
    """Test cases for Kadane's algorithm (maximum subarray sum)."""
    
    def test_basic_array(self):
        algo = AlgorithmicChallenges()
        assert algo.kadane_algorithm([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
        # Explanation: [4,-1,2,1] has the largest sum = 6
    
    def test_single_element(self):
        algo = AlgorithmicChallenges()
        assert algo.kadane_algorithm([5]) == 5
    
    def test_all_negative(self):
        algo = AlgorithmicChallenges()
        # This will fail due to the bug!
        assert algo.kadane_algorithm([-5, -2, -8, -1, -4]) == -1
        # Should return -1 (the largest single element)
    
    def test_all_positive(self):
        algo = AlgorithmicChallenges()
        assert algo.kadane_algorithm([1, 2, 3, 4, 5]) == 15
    
    def test_empty_array(self):
        algo = AlgorithmicChallenges()
        assert algo.kadane_algorithm([]) == 0


class TestLongestIncreasingSubsequence:
    """Test cases for LIS algorithm."""
    
    def test_basic_sequence(self):
        algo = AlgorithmicChallenges()
        assert algo.longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18]) == 4
        # LIS: [2, 3, 7, 101]
    
    def test_decreasing_sequence(self):
        algo = AlgorithmicChallenges()
        assert algo.longest_increasing_subsequence([5, 4, 3, 2, 1]) == 1
    
    def test_all_same(self):
        algo = AlgorithmicChallenges()
        assert algo.longest_increasing_subsequence([7, 7, 7, 7]) == 1


class TestDijkstraAlgorithm:
    """Test cases for Dijkstra's shortest path."""
    
    def test_simple_path(self):
        algo = AlgorithmicChallenges()
        graph = {
            0: [(1, 4), (2, 1)],
            1: [(3, 1)],
            2: [(1, 2), (3, 5)],
            3: []
        }
        distance, path = algo.dijkstra_shortest_path(graph, 0, 3)
        assert distance == 4
        assert path == [0, 2, 1, 3]  # This will fail due to reversed path bug
    
    def test_no_path(self):
        algo = AlgorithmicChallenges()
        graph = {
            0: [(1, 1)],
            1: [],
            2: []
        }
        distance, path = algo.dijkstra_shortest_path(graph, 0, 2)
        assert distance == float('inf')
        assert path == []


class TestMergeIntervals:
    """Test cases for merge intervals."""
    
    def test_overlapping_intervals(self):
        algo = AlgorithmicChallenges()
        # This will fail due to not sorting first!
        assert algo.merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    
    def test_touching_intervals(self):
        algo = AlgorithmicChallenges()
        # This will fail due to wrong comparison (< instead of <=)
        assert algo.merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    
    def test_unsorted_intervals(self):
        algo = AlgorithmicChallenges()
        # This will definitely fail!
        assert algo.merge_intervals([[1, 4], [0, 2], [3, 5]]) == [[0, 5]]


class TestThreeSum:
    """Test cases for 3Sum problem."""
    
    def test_basic_case(self):
        algo = AlgorithmicChallenges()
        result = algo.three_sum([-1, 0, 1, 2, -1, -4])
        expected = [[-1, -1, 2], [-1, 0, 1]]
        # This will fail due to duplicates!
        assert sorted(result) == sorted(expected)
    
    def test_no_solution(self):
        algo = AlgorithmicChallenges()
        assert algo.three_sum([1, 2, 3]) == []
    
    def test_all_zeros(self):
        algo = AlgorithmicChallenges()
        result = algo.three_sum([0, 0, 0, 0])
        # Should return only one [0, 0, 0], but will have duplicates
        assert len(result) == 1


class TestKnapsack:
    """Test cases for 0/1 Knapsack."""
    
    def test_basic_knapsack(self):
        algo = AlgorithmicChallenges()
        weights = [1, 3, 4, 5]
        values = [1, 4, 5, 7]
        capacity = 7
        # This will fail due to multiple bugs in the implementation
        assert algo.knapsack_01(weights, values, capacity) == 9
    
    def test_zero_capacity(self):
        algo = AlgorithmicChallenges()
        assert algo.knapsack_01([1, 2], [1, 2], 0) == 0


class TestTopologicalSort:
    """Test cases for topological sort."""
    
    def test_valid_ordering(self):
        algo = AlgorithmicChallenges()
        # Course 1 depends on 0, Course 3 depends on 1 and 2
        prerequisites = [[1, 0], [3, 1], [3, 2]]
        result = algo.topological_sort(4, prerequisites)
        assert len(result) == 4  # Should include all courses
        # Verify ordering constraints
        assert result.index(0) < result.index(1)
        assert result.index(1) < result.index(3)
        assert result.index(2) < result.index(3)
    
    def test_with_cycle(self):
        algo = AlgorithmicChallenges()
        # Circular dependency: 0 -> 1 -> 2 -> 0
        prerequisites = [[1, 0], [2, 1], [0, 2]]
        result = algo.topological_sort(3, prerequisites)
        # Should detect cycle and not return all courses
        assert len(result) < 3


class TestCoinChange:
    """Test cases for coin change problem."""
    
    def test_basic_case(self):
        algo = AlgorithmicChallenges()
        # This will fail due to wrong array size and indices
        assert algo.coin_change([1, 2, 5], 11) == 3  # 5 + 5 + 1
    
    def test_impossible_case(self):
        algo = AlgorithmicChallenges()
        assert algo.coin_change([2], 3) == -1
    
    def test_zero_amount(self):
        algo = AlgorithmicChallenges()
        assert algo.coin_change([1, 2, 5], 0) == 0
