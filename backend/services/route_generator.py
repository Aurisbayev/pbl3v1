"""
A* route generation using scenic-adjusted edge costs.
"""

import heapq

from .scenic_scorer import ScenicScorer


class RouteGenerator:

    def __init__(self, graph):

        self.graph = graph
        self.scorer = ScenicScorer()


    def heuristic(self, node, goal):
        """
        Straight-line (Euclidean) heuristic.

        Node format:
        {
            "x": ...
            "y": ...
        }
        """

        dx = node["x"] - goal["x"]
        dy = node["y"] - goal["y"]

        return (dx * dx + dy * dy) ** 0.5


    def generate_route(self, start, goal):

        open_set = []

        heapq.heappush(open_set, (0, start))

        came_from = {}

        g_score = {
            start: 0
        }

        f_score = {
            start: self.heuristic(
                self.graph.nodes[start],
                self.graph.nodes[goal]
            )
        }

        while open_set:

            _, current = heapq.heappop(open_set)

            if current == goal:
                return self.reconstruct_path(
                    came_from,
                    current
                )

            for neighbor, edge in self.graph.neighbors(current):

                cost = self.scorer.adjusted_cost(edge)

                tentative = g_score[current] + cost

                if neighbor not in g_score or tentative < g_score[neighbor]:

                    came_from[neighbor] = current

                    g_score[neighbor] = tentative

                    f_score[neighbor] = (
                        tentative
                        +
                        self.heuristic(
                            self.graph.nodes[neighbor],
                            self.graph.nodes[goal]
                        )
                    )

                    heapq.heappush(
                        open_set,
                        (
                            f_score[neighbor],
                            neighbor
                        )
                    )

        return None


    def reconstruct_path(self, came_from, current):

        path = [current]

        while current in came_from:

            current = came_from[current]

            path.append(current)

        path.reverse()

        return path
