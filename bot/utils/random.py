import random

class RandomUtils:

    def choice(variables: list):

        return random.choices(
            population = variables,
            weights = [random.random() for _ in [1] * len(variables)]
        )[0]