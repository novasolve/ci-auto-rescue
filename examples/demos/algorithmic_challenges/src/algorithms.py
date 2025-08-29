"""Advanced algorithms with subtle bugs for Nova CI-Rescue demo."""

from typing import List, Tuple, Optional, Dict, Set
from collections import deque, defaultdict
import heapq


class AlgorithmicChallenges:
    """Collection of classic algorithms with intentional bugs."""

    def kadane_algorithm(self, nums: List[int]) -> int:
        """
        Kadane's algorithm for maximum subarray sum.
        BUG: Doesn't handle all-negative arrays correctly.
        """
        if not nums:
            return 0

        max_current = max_global = 0  # BUG: Should initialize to nums[0]

        for num in nums:
            max_current = max(num, max_current + num)
            max_global = max(max_global, max_current)

        return max_global

    def longest_increasing_subsequence(self, nums: List[int]) -> int:
        """
        Dynamic programming solution for LIS.
        BUG: Off-by-one error in the DP logic.
        """
        if not nums:
            return 0

        n = len(nums)
        dp = [1] * n

        for i in range(1, n):
            for j in range(i):  # BUG: Should be range(0, i)
                if nums[j] < nums[i]:
                    dp[i] = max(dp[i], dp[j])  # BUG: Should be dp[j] + 1

        return max(dp)

    def dijkstra_shortest_path(self, graph: Dict[int, List[Tuple[int, int]]],
                              start: int, end: int) -> Tuple[int, List[int]]:
        """
        Dijkstra's algorithm for shortest path.
        BUG: Doesn't handle negative weights properly and has path reconstruction bug.
        """
        distances = defaultdict(lambda: float('inf'))
        distances[start] = 0
        heap = [(0, start)]
        visited = set()
        parent = {}

        while heap:
            curr_dist, node = heapq.heappop(heap)

            if node == end:
                # Reconstruct path
                path = []
                current = end
                while current != start:  # BUG: Will fail if no path exists
                    path.append(current)
                    current = parent[current]
                path.append(start)
                return curr_dist, path  # BUG: Path is in wrong order

            visited.add(node)  # BUG: Should check before processing neighbors

            for neighbor, weight in graph.get(node, []):
                if neighbor not in visited:
                    new_dist = curr_dist + weight
                    if new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        parent[neighbor] = node
                        heapq.heappush(heap, (new_dist, neighbor))

        return float('inf'), []

    def merge_intervals(self, intervals: List[List[int]]) -> List[List[int]]:
        """
        Merge overlapping intervals.
        BUG: Doesn't handle edge cases correctly.
        """
        if not intervals:
            return []

        # BUG: Not sorting the intervals first
        merged = [intervals[0]]

        for i in range(1, len(intervals)):
            current = intervals[i]
            last_merged = merged[-1]

            # BUG: Wrong comparison for overlapping intervals
            if current[0] < last_merged[1]:  # Should be <=
                merged[-1][1] = max(last_merged[1], current[1])
            else:
                merged.append(current)

        return merged

    def three_sum(self, nums: List[int]) -> List[List[int]]:
        """
        Find all unique triplets that sum to zero.
        BUG: Duplicate handling and edge cases.
        """
        if len(nums) < 3:
            return []

        nums.sort()
        result = []

        for i in range(len(nums) - 2):
            # BUG: Not skipping duplicates for i
            left, right = i + 1, len(nums) - 1

            while left < right:
                total = nums[i] + nums[left] + nums[right]

                if total == 0:
                    result.append([nums[i], nums[left], nums[right]])
                    left += 1
                    right -= 1
                    # BUG: Not skipping duplicates for left and right
                elif total < 0:
                    left += 1
                else:
                    right -= 1

        return result

    def knapsack_01(self, weights: List[int], values: List[int], capacity: int) -> int:
        """
        0/1 Knapsack problem using dynamic programming.
        BUG: Incorrect DP table initialization and update logic.
        """
        n = len(weights)
        if n == 0 or capacity == 0:
            return 0

        # BUG: Wrong dimensions for DP table
        dp = [[0] * capacity for _ in range(n)]  # Should be capacity + 1

        for i in range(n):
            for w in range(capacity):  # Should start from 1
                if weights[i] <= w:
                    # BUG: Wrong indices in the recurrence relation
                    dp[i][w] = max(dp[i-1][w], values[i] + dp[i-1][w-weights[i]])
                else:
                    dp[i][w] = dp[i-1][w]

        return dp[n-1][capacity-1]  # BUG: Wrong indices

    def topological_sort(self, num_courses: int, prerequisites: List[List[int]]) -> List[int]:
        """
        Topological sort using Kahn's algorithm.
        BUG: Cycle detection and edge case handling.
        """
        graph = defaultdict(list)
        in_degree = [0] * num_courses

        # Build graph
        for course, prereq in prerequisites:
            graph[prereq].append(course)
            in_degree[course] += 1

        # Find all nodes with no incoming edges
        queue = deque()
        for i in range(num_courses):
            if in_degree[i] == 0:
                queue.append(i)

        result = []
        while queue:
            node = queue.popleft()
            result.append(node)

            # BUG: Not checking if node exists in graph
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # BUG: Not checking if all courses are included (cycle detection)
        return result

    def coin_change(self, coins: List[int], amount: int) -> int:
        """
        Minimum coins needed to make amount.
        BUG: Initialization and boundary conditions.
        """
        if amount == 0:
            return 0

        # BUG: Wrong initialization value
        dp = [amount + 1] * amount  # Should be amount + 1 size
        dp[0] = 0

        for i in range(1, amount):  # BUG: Should go to amount + 1
            for coin in coins:
                if coin <= i:
                    # BUG: Not checking if dp[i-coin] is valid
                    dp[i] = min(dp[i], 1 + dp[i - coin])

        return dp[amount - 1] if dp[amount - 1] != amount + 1 else -1  # BUG: Wrong index
