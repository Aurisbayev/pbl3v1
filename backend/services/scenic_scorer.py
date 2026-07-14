"""
scenic_scorer.py

Calculates a scenic score for each road segment.
"""
class ScenicScorer:


    def __init__(self, weights=None):
        """
        weights:
            Dictionary allowing different importance for each factor.
        """

        self.weights = weights or {
            "green": 0.25,
            "water": 0.15,
            "poi": 0.15,
            "construction": 0.15,
            "traffic": 0.15,
            "pedestrian": 0.15
        }

    def scenic_score(self, edge):
        """
        Returns scenic score between 0 and 1.

        edge example:

        {
            "green_score":0.8,
            "water_score":0.6,
            "poi_score":0.7,
            "construction_score":0.2,
            "traffic_score":0.3,
            "pedestrian_score":0.9
        }
        """

        score = (

            self.weights["green"] *
            edge["green_score"]

            +

            self.weights["water"] *
            edge["water_score"]

            +

            self.weights["poi"] *
            edge["poi_score"]

            +

            self.weights["construction"] *
            (1 - edge["construction_score"])

            +

            self.weights["traffic"] *
            (1 - edge["traffic_score"])

            +

            self.weights["pedestrian"] *
            edge["pedestrian_score"]

        )

        return max(0.0, min(score, 1.0))


    def adjusted_cost(self, edge):
        """
        Converts the scenic score into an A* cost.

        Scenic roads become 'shorter' to A*.

        cost = distance × (1 − scenic_score × α)

        α controls how much scenic quality influences routing.
        """

        alpha = 0.40

        scenic = self.scenic_score(edge)

        adjusted = edge["distance"] * (1 - alpha * scenic)

        return max(adjusted, 1)
