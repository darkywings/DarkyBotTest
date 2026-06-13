from utils.random import RandomUtils

class BaseTrigger:

    def __init__(self):
        self._replies = []

    def react(self):

        return RandomUtils.choice(self._replies)